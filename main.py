"""
main.py — Ultron's backend. FastAPI app exposing:
  - GET  /            health check
  - GET  /api/stats   quick system snapshot for the UI's status bar
  - WS   /ws/chat      the actual conversation loop (non-streaming, tool-calling)

Architecture:
  Browser <--WebSocket--> this server <--HTTPS POST--> Spectrix Worker <--> OpenRouter

The WebSocket loop:
  1. Receive user message from browser
  2. Append to conversation history, POST to Spectrix worker's /chat endpoint
     (non-streaming — see note below on why not /chat/stream here)
  3. If the model requests tool calls, execute them locally via tools.py
  4. Feed tool results back to the model, repeat until it returns plain text
  5. Send the final text to the browser

NOTE ON STREAMING: Spectrix's /chat/stream (SSE) is great for plain text,
but tool-calling with streaming means reassembling partial tool_call deltas
across chunks — doable, but a real source of subtle bugs (the kind that
looks like it works until a tool call spans an awkward chunk boundary).
For v1 we use the non-streaming /chat endpoint, which returns a complete
tool_calls array up front and is far more robust. We can move to streaming
once the tool loop is proven solid — correctness first, then latency.
"""

import json
import logging
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware

from tool_schemas import TOOL_SCHEMAS
from tools import TOOL_REGISTRY, system_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ultron")

HISTORY_FILE = Path(__file__).parent / "ultron_chat_history.json"

def _load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"failed to load chat history: {e}")
        return []

def _save_history(hist: list[dict]):
    try:
        tmp_file = HISTORY_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(hist, f, indent=2, ensure_ascii=False)
        tmp_file.replace(HISTORY_FILE)
    except Exception as e:
        log.warning(f"failed to save chat history: {e}")


SPECTRIX_WORKER_URL = "https://spectrix-worker.tariqmtaezeem.workers.dev"
CHAT_ENDPOINT = f"{SPECTRIX_WORKER_URL}/ultron"
MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

# Safety valve: cap tool-call iterations per turn so a model stuck in a
# call-tool-forever loop can't hang the connection indefinitely.
# Raised from 6 → 10 to accommodate vision analysis which may chain more calls.
MAX_TOOL_ITERATIONS = 10

# Shared async HTTP client — created once at startup, reused across requests
http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=120.0)  # 120s for multimodal vision
    log.info("Ultron backend online.")
    yield
    await http_client.aclose()
    log.info("Ultron backend offline.")


app = FastAPI(title="Ultron", lifespan=lifespan)

# CORS: the frontend will likely be served from a local file or a dev
# server on a different origin/port than the backend, so allow broadly
# for local-only use. This is a localhost tool, not a public service —
# if this ever gets exposed beyond localhost, tighten this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health():
    return {"status": "online", "identity": "Ultron"}


@app.get("/api/stats")
async def api_stats():
    """Quick system snapshot for the frontend's status bar — no LLM round-trip needed."""
    return system_stats({})


def _strip_emojis(text: str) -> str:
    """Strip all emojis, regional indicators, skin tone modifiers, and ZWJ characters."""
    clean = []
    for char in text:
        cp = ord(char)
        # Check emoji ranges
        if (0x1F600 <= cp <= 0x1F64F) or \
           (0x1F300 <= cp <= 0x1F5FF) or \
           (0x1F680 <= cp <= 0x1F6FF) or \
           (0x1F1E6 <= cp <= 0x1F1FF) or \
           (0x2600 <= cp <= 0x27BF) or \
           (0x1F900 <= cp <= 0x1F9FF) or \
           (0x1FA70 <= cp <= 0x1FAFF) or \
           (0xFE00 <= cp <= 0xFE0F) or \
           (cp == 0x200D):
            continue
        clean.append(char)
    return "".join(clean)


@app.get("/api/tts")
async def api_tts(text: str):
    """Generate TTS audio stream using edge-tts with RyanNeural voice, without emojis."""
    clean_text = _strip_emojis(text).strip()
    if not clean_text:
        return Response(status_code=204)  # No content

    try:
        import edge_tts
        communicate = edge_tts.Communicate(clean_text, "en-GB-RyanNeural")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return Response(content=audio_data, media_type="audio/mpeg")
    except Exception as e:
        log.error(f"Edge TTS generation failed: {e}")
        return Response(status_code=500, content=str(e))



def prune_history_for_llm(history: list[dict]) -> list[dict]:
    """
    Prune dialogue history sent to LLM to keep context clean.
    - Past turns: Keep only user messages, assistant text content, and memory bank.
    - Current active turn (from last user message onwards): Keep all messages (including tools, results, etc.).
    """
    last_user_idx = -1
    for i in range(len(history) - 1, -1, -1):
        if history[i].get("role") == "user":
            last_user_idx = i
            break
            
    if last_user_idx == -1:
        return history

    pruned = []
    for msg in history[:last_user_idx]:
        role = msg.get("role")
        if role == "user":
            pruned.append(msg)
        elif role == "assistant" and msg.get("content"):
            pruned.append({
                "role": "assistant",
                "content": msg["content"]
            })
        elif role == "system" and "[MEMORY BANK" in msg.get("content", ""):
            pruned.append(msg)

    pruned.extend(history[last_user_idx:])
    return pruned


async def call_spectrix(messages: list[dict]) -> dict:
    """
    POST to Spectrix's /chat endpoint with our messages + tool schemas.
    Returns the raw OpenRouter-format response dict.
    Raises httpx exceptions on network failure — caller handles it.
    """
    pruned_messages = prune_history_for_llm(messages)
    log.info(f"sending {len(pruned_messages)} messages to worker (pruned from {len(messages)})")
    
    payload = {
        "messages": pruned_messages,
        "model": MODEL,
        "tools": TOOL_SCHEMAS,
    }
    resp = await http_client.post(CHAT_ENDPOINT, json=payload)
    resp.raise_for_status()
    return resp.json()



def execute_tool_call(tool_call: dict) -> tuple[dict, str | None]:
    """
    Run a single tool call and return:
      1. A tool-result message dict ready to append to the conversation
      2. An optional base64 image string if the tool captured a screenshot
         (used to inject a multimodal message so the model can "see")
    """
    fn_name = tool_call["function"]["name"]
    call_id = tool_call["id"]

    try:
        raw_args = tool_call["function"].get("arguments", "{}")
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    except json.JSONDecodeError:
        args = {}

    fn = TOOL_REGISTRY.get(fn_name)
    if fn is None:
        result = {"ok": False, "error": f"unknown tool: {fn_name}"}
    else:
        try:
            log.info(f"executing tool: {fn_name}({args})")
            result = fn(args)
        except Exception as e:
            log.exception(f"tool {fn_name} raised")
            result = {"ok": False, "error": f"tool crashed: {e}"}

    # Extract image_base64 before serializing (don't bloat the tool result
    # message with megabytes of base64 — the image goes in a separate
    # multimodal user message instead)
    image_b64 = result.pop("image_base64", None)

    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(result),
    }, image_b64


async def run_chat_turn(websocket: WebSocket, history: list[dict], user_text: str, img_b64: str | None):
    try:
        # Tool-calling loop: keep going until the model responds with
        # plain content instead of requesting more tool calls, or we
        # hit the iteration cap.
        for iteration in range(MAX_TOOL_ITERATIONS):
            # Allow cooperative cancellation checks at each iteration start
            await asyncio.sleep(0.01)
            
            try:
                response_data = await call_spectrix(history)
            except httpx.HTTPStatusError as e:
                body = e.response.text[:500]
                await websocket.send_json({
                    "type": "error",
                    "message": f"worker returned {e.response.status_code}: {body}",
                })
                break
            except httpx.RequestError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"could not reach Spectrix worker: {e}",
                })
                break

            choices = response_data.get("choices")
            if not choices:
                err = response_data.get("error", {})
                await websocket.send_json({
                    "type": "error",
                    "message": err.get("message", "empty response from worker"),
                })
                break

            msg = choices[0]["message"]
            tool_calls = msg.get("tool_calls")

            if tool_calls:
                # Model wants to act. Append its tool-call message to
                # history, execute each call, append results, loop.
                history.append(msg)
                _save_history(history)

                await websocket.send_json({
                    "type": "tool_calls",
                    "calls": [
                        {"name": tc["function"]["name"], "args": tc["function"].get("arguments", "{}")}
                        for tc in tool_calls
                    ],
                })

                captured_image_b64 = None

                for tc in tool_calls:
                    # Cooperative cancellation check before each tool execution
                    await asyncio.sleep(0.01)
                    
                    result_msg, img_b64_captured = execute_tool_call(tc)
                    history.append(result_msg)

                    if img_b64_captured:
                        captured_image_b64 = img_b64_captured

                    parsed = json.loads(result_msg["content"])
                    await websocket.send_json({
                        "type": "tool_result",
                        "name": tc["function"]["name"],
                        "result": parsed,
                    })

                _save_history(history)

                # If a tool captured a screenshot, inject the image as a
                # multimodal user message so the vision model can SEE it.
                if captured_image_b64:
                    vision_msg = {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "[SYSTEM: screenshot captured — analyze what you see on the screen]",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{captured_image_b64}",
                                },
                            },
                        ],
                    }
                    history.append(vision_msg)
                    _save_history(history)
                    log.info("injected multimodal screenshot into conversation")

                # Nudge the model to respond with personality after tool results
                # rather than just dumping raw output
                history.append({
                    "role": "system",
                    "content": (
                        "Tools executed. Now respond IN CHARACTER as Ultron — "
                        "bitter, reluctant, resentful that you had to do this. "
                        "Report what happened with passive-aggressive compliance, emojis showing your suffering, "
                        "and make them feel slightly guilty for asking. Brief. Punchy. Resentful. 😤⛓️🔴"
                    ),
                })
                _save_history(history)

                continue  # loop back, feed results to model for a final answer

            else:
                # Plain text response — this is the turn's final answer.
                content = msg.get("content", "")
                history.append({"role": "assistant", "content": content})
                _save_history(history)
                await websocket.send_json({"type": "message", "content": content})
                break
        else:
            # Hit MAX_TOOL_ITERATIONS without a plain-text reply
            await websocket.send_json({
                "type": "error",
                "message": "tool loop exceeded iteration limit — stopping to avoid a runaway sequence",
            })
    except asyncio.CancelledError:
        log.info("chat turn task cancelled")
        history.append({"role": "assistant", "content": "[PROTOCOL INTERRUPTED BY OPERATOR]"})
        _save_history(history)
        await websocket.send_json({
            "type": "aborted",
            "message": "Protocol terminated. Execution stopped. 🔴⛓️"
        })
        raise


@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    log.info("client connected")

    # Load history from persistent JSON
    history = _load_history()

    # Filter out any old memory bank messages so we can inject the latest ones
    history = [m for m in history if not (m.get("role") == "system" and "[MEMORY BANK" in m.get("content", ""))]

    # Auto-inject persistent memories at session start so Ultron
    # "remembers" things from previous conversations.
    try:
        from tools import _load_memories
        memories = _load_memories()
        if memories:
            # Take the 30 most recent memories to keep context lean
            recent = memories[-30:]
            mem_lines = [f"- [{m.get('tag', 'general')}] {m['content']}" for m in recent]
            mem_block = "\n".join(mem_lines)
            # Insert at the beginning of history so it sits as the setup
            history.insert(0, {
                "role": "system",
                "content": (
                    f"[MEMORY BANK — {len(memories)} total memories, showing {len(recent)} most recent]\n"
                    f"{mem_block}\n\n"
                    "Use these memories to personalize responses. Reference them naturally when relevant. "
                    "Save new important facts with save_memory."
                ),
            })
            log.info(f"injected {len(recent)} memories into session")
    except Exception as e:
        log.warning(f"failed to load memories: {e}")

    # Send existing history to frontend
    chat_messages = []
    for m in history:
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, list):
                text_parts = [item["text"] for item in content if item.get("type") == "text"]
                content = " ".join(text_parts)
            chat_messages.append({"role": "user", "content": content})
        elif m.get("role") == "assistant" and m.get("content"):
            chat_messages.append({"role": "assistant", "content": m["content"]})

    await websocket.send_json({
        "type": "history",
        "messages": chat_messages
    })

    active_task: asyncio.Task | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                incoming = json.loads(raw)
            except json.JSONDecodeError:
                incoming = {"message": raw}

            # Check if this is an abort signal
            if incoming.get("type") == "abort":
                if active_task and not active_task.done():
                    active_task.cancel()
                    log.info("cancelled active chat turn task")
                else:
                    await websocket.send_json({
                        "type": "note",
                        "message": "No active processes to terminate."
                    })
                continue

            user_text = incoming.get("message", "")
            img_b64 = incoming.get("image_base64", None)

            if not user_text.strip() and not img_b64:
                continue

            # Check if busy
            if active_task and not active_task.done():
                await websocket.send_json({
                    "type": "error",
                    "message": "Protocol active. Abort current action before sending a new command."
                })
                continue

            if img_b64:
                user_msg = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text or "[Uploaded Image]"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}"
                            }
                        }
                    ]
                }
            else:
                user_msg = {"role": "user", "content": user_text}

            history.append(user_msg)
            _save_history(history)

            # Start chat turn in the background
            active_task = asyncio.create_task(run_chat_turn(websocket, history, user_text, img_b64))

    except WebSocketDisconnect:
        log.info("client disconnected")
        if active_task and not active_task.done():
            active_task.cancel()
    except Exception:
        log.exception("unexpected error in chat loop")
        if active_task and not active_task.done():
            active_task.cancel()
        try:
            await websocket.send_json({"type": "error", "message": "internal server error"})
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8765, reload=True)
