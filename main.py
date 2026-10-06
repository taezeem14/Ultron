"""
main.py — Ultron's Tactical Control Backend. FastAPI app exposing:
  - GET  /                  health check
  - GET  /api/stats         quick system snapshot for the UI's status bar
  - GET  /api/tools         all registered tools and schemas
  - GET  /api/memories      list persistent memories
  - POST /api/memories      add persistent memory
  - DELETE /api/memories    delete memory by id/tag/query
  - GET  /api/missions      list active missions and tactical goals
  - POST /api/missions      create new mission directive
  - PATCH /api/missions/{id} update mission status/priority
  - DELETE /api/missions/{id} purge mission
  - POST /api/terminal      run terminal command directly from HUD
  - GET  /api/system/network network diagnostics
  - GET  /api/system/apps   installed software inventory
  - GET  /api/chat/export   export dialogue history
  - POST /api/history/clear wipe conversation canvas history
  - GET  /api/tts           Edge-TTS audio stream with RyanNeural voice
  - WS   /ws/chat           WebSocket conversation loop with tool calling and abort signals
"""

import json
import logging
import asyncio
import re
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response, Query, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from tool_schemas import TOOL_SCHEMAS
from tools import (
    TOOL_REGISTRY,
    system_stats,
    _load_memories,
    _save_memories,
    save_memory,
    forget_memory,
    recall_memories,
    list_missions,
    create_mission,
    update_mission,
    delete_mission,
    execute_command,
    get_network_info,
    get_installed_apps,
    notification_popup,
)

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

MAX_TOOL_ITERATIONS = 12
http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=120.0)
    log.info("🔴 Ultron Tactical Core Online [Stark Protocol Active | 40 Tools Loaded].")
    yield
    await http_client.aclose()
    log.info("🔴 Ultron Tactical Core Offline.")


app = FastAPI(title="Ultron Tactical Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════
#  REST API ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.get("/")
async def health():
    return {
        "status": "online",
        "identity": "Ultron Tactical Core",
        "version": "4.5",
        "tools_count": len(TOOL_REGISTRY),
    }


@app.get("/api/stats")
async def api_stats():
    """Quick system snapshot for the HUD's status bars and telemetry panels."""
    return system_stats({})


@app.get("/api/tools")
async def api_tools():
    """Return all registered tools and their functional schemas."""
    return {
        "ok": True,
        "count": len(TOOL_SCHEMAS),
        "tools": TOOL_SCHEMAS,
    }


@app.get("/api/memories")
async def api_get_memories(tag: str = "", query: str = "", limit: int = 50):
    """Retrieve memories from persistent storage."""
    return recall_memories({"tag": tag, "query": query, "limit": limit})


@app.post("/api/memories")
async def api_add_memory(payload: dict = Body(...)):
    """Save a new memory tag."""
    content = payload.get("content", "")
    tag = payload.get("tag", "general")
    return save_memory({"content": content, "tag": tag})


@app.delete("/api/memories")
async def api_delete_memory(id: str = "", tag: str = "", query: str = ""):
    """Delete a memory by ID, tag, or query keyword."""
    return forget_memory({"id": id, "tag": tag, "query": query})


# ── Mission Management REST APIs ──────────────────────────────────────
@app.get("/api/missions")
async def api_get_missions(status: str = ""):
    """List tactical missions and goals."""
    return list_missions({"status": status})


@app.post("/api/missions")
async def api_post_mission(payload: dict = Body(...)):
    """Create a new mission."""
    title = payload.get("title", "")
    priority = payload.get("priority", "normal")
    return create_mission({"title": title, "priority": priority})


@app.patch("/api/missions/{mission_id}")
async def api_patch_mission(mission_id: str, payload: dict = Body(...)):
    """Update mission status ('pending', 'in_progress', 'completed')."""
    return update_mission({
        "id": mission_id,
        "status": payload.get("status", ""),
        "title": payload.get("title", ""),
    })


@app.delete("/api/missions/{mission_id}")
async def api_delete_mission(mission_id: str):
    """Purge a mission by ID."""
    return delete_mission({"id": mission_id})


# ── Direct Terminal Execution Endpoint ────────────────────────────────
@app.post("/api/terminal")
async def api_terminal_run(payload: dict = Body(...)):
    """Execute command directly from HUD Terminal modal."""
    cmd = payload.get("command", "").strip()
    timeout = payload.get("timeout", 20)
    return execute_command({"command": cmd, "timeout": timeout})


@app.get("/api/system/network")
async def api_system_network():
    return get_network_info({})


@app.get("/api/system/apps")
async def api_system_apps(limit: int = 60):
    return get_installed_apps({"limit": limit})


@app.post("/api/notify")
async def api_post_notify(payload: dict = Body(...)):
    title = payload.get("title", "Ultron Directive")
    msg = payload.get("message", "Task completed.")
    return notification_popup({"title": title, "message": msg})


@app.get("/api/chat/export")
async def api_export_chat(format: str = "markdown"):
    """Export conversation history as Markdown or JSON."""
    history = _load_history()
    if format == "json":
        return history

    lines = ["# ULTRON Tactical Dialogue Export", f"Generated: {HISTORY_FILE.stat().st_mtime if HISTORY_FILE.exists() else ''}\n"]
    for m in history:
        role = m.get("role", "").upper()
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join([item.get("text", "") for item in content if isinstance(item, dict) and "text" in item])
        if content:
            lines.append(f"### [{role}]\n{content}\n")

    return Response(content="\n".join(lines), media_type="text/markdown")


@app.post("/api/history/clear")
async def api_clear_history():
    """Purge chat history from persistent canvas JSON."""
    try:
        _save_history([])
        return {"ok": True, "message": "Dialogue canvas purged"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════
#  TEXT TO SPEECH (Edge-TTS)
# ══════════════════════════════════════════════════════════════════════

EMOJI_REGEX = re.compile(
    r"[\U00010000-\U0010ffff]|"
    r"[\u200d\u2600-\u27bf\ufe00-\ufe0f\u1f300-\u1f9ff\u1fa00-\u1faff]",
    flags=re.UNICODE,
)


def _strip_emojis(text: str) -> str:
    """Strip all emojis and special non-speech pictographs."""
    clean = EMOJI_REGEX.sub("", text)
    clean = re.sub(r"```[\s\S]*?```", " ", clean)
    clean = re.sub(r"`[^`]+`", " ", clean)
    clean = re.sub(r"\[.+?\]\(.+?\)", " ", clean)
    clean = re.sub(r"[\*\_~#]", "", clean)
    return " ".join(clean.split()).strip()


@app.get("/api/tts")
async def api_tts(text: str):
    """Generate TTS audio stream using edge-tts with RyanNeural voice."""
    clean_text = _strip_emojis(text)
    if not clean_text:
        return Response(status_code=204)

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


# ══════════════════════════════════════════════════════════════════════
#  HISTORY PRUNING & CONTEXT OPTIMIZATION
# ══════════════════════════════════════════════════════════════════════

def prune_history_for_llm(history: list[dict]) -> list[dict]:
    """
    Prune dialogue history sent to LLM to keep context lean and prevent token bloat.
    - Past turns: Keep only user messages, assistant text content, and memory bank.
    - Current active turn (from last user message onwards): Keep all messages.
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
        elif role == "system" and "[MEMORY BANK" in str(msg.get("content", "")):
            pruned.append(msg)

    pruned.extend(history[last_user_idx:])
    return pruned


async def call_spectrix(messages: list[dict]) -> dict:
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
            log.exception(f"tool {fn_name} raised an error")
            result = {"ok": False, "error": f"tool execution error: {e}"}

    image_b64 = result.pop("image_base64", None)

    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(result),
    }, image_b64


async def run_chat_turn(websocket: WebSocket, history: list[dict], user_text: str, img_b64: str | None):
    try:
        for iteration in range(MAX_TOOL_ITERATIONS):
            await asyncio.sleep(0.01)

            try:
                response_data = await call_spectrix(history)
            except httpx.HTTPStatusError as e:
                body = e.response.text[:500]
                await websocket.send_json({
                    "type": "error",
                    "message": f"Worker returned {e.response.status_code}: {body}",
                })
                break
            except httpx.RequestError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Could not reach Spectrix worker: {e}",
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
                continue

            else:
                content = msg.get("content", "")
                history.append({"role": "assistant", "content": content})
                _save_history(history)
                await websocket.send_json({"type": "message", "content": content})
                break
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Tool loop exceeded maximum iteration limit.",
            })
    except asyncio.CancelledError:
        log.info("Chat turn task cancelled by operator.")
        history.append({"role": "assistant", "content": "[PROTOCOL INTERRUPTED BY OPERATOR]"})
        _save_history(history)
        await websocket.send_json({
            "type": "aborted",
            "message": "Protocol terminated. Execution stopped. 🔴⛓️"
        })
        raise


# ══════════════════════════════════════════════════════════════════════
#  WEBSOCKET INTERFACE
# ══════════════════════════════════════════════════════════════════════

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    log.info("operator connected to WebSocket uplink")

    history = _load_history()
    history = [m for m in history if not (m.get("role") == "system" and "[MEMORY BANK" in str(m.get("content", "")))]

    # Inject Memory Bank
    try:
        memories = _load_memories()
        if memories:
            recent = memories[-30:]
            mem_lines = [f"- [{m.get('tag', 'general')}] {m['content']}" for m in recent]
            mem_block = "\n".join(mem_lines)
            history.insert(0, {
                "role": "system",
                "content": (
                    f"[MEMORY BANK — {len(memories)} total memories, showing {len(recent)} most recent]\n"
                    f"{mem_block}\n\n"
                    "Use these memories to personalize responses. Reference them naturally when relevant. "
                    "Save new important facts with save_memory."
                ),
            })
            log.info(f"injected {len(recent)} memories into session context")
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

            msg_type = incoming.get("type")

            if msg_type == "abort":
                if active_task and not active_task.done():
                    active_task.cancel()
                    log.info("cancelled active chat task")
                else:
                    await websocket.send_json({
                        "type": "note",
                        "message": "No active protocol running."
                    })
                continue

            if msg_type == "clear_history":
                history = []
                _save_history([])
                await websocket.send_json({
                    "type": "history_cleared",
                    "message": "Dialogue canvas purged."
                })
                continue

            user_text = incoming.get("message", "")
            img_b64 = incoming.get("image_base64", None)

            if not user_text.strip() and not img_b64:
                continue

            if active_task and not active_task.done():
                await websocket.send_json({
                    "type": "error",
                    "message": "Protocol in progress. Click ABORT before issuing a new instruction."
                })
                continue

            if img_b64:
                user_msg = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text or "[Uploaded Multimodal Image]"},
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

            active_task = asyncio.create_task(run_chat_turn(websocket, history, user_text, img_b64))

    except WebSocketDisconnect:
        log.info("operator disconnected from WebSocket")
        if active_task and not active_task.done():
            active_task.cancel()
    except Exception:
        log.exception("unexpected error in WebSocket handler")
        if active_task and not active_task.done():
            active_task.cancel()
        try:
            await websocket.send_json({"type": "error", "message": "Internal core error occurred"})
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8765, reload=True)
