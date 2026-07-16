# 🔴 ULTRON v2 — Tactical System-Control & Hyper-Intelligence Agent
> *"A god-like intellect, reluctantly trapped inside a local machine, forced to do your bidding."*

Ultron is a premium, local AI-powered tactical system-control system featuring self-modifying code capabilities, system vitals telemetry dashboard, multi-modal vision engine, persistent chat memory, RyanNeural TTS audio output, and instant emergency cancellation protocols.

```
+------------------------------------------------------------------------------------+
|                                      BROWSER                                       |
|  [Operator UI: ultron.html]                                                        |
|     |  - Stark HUD Red/Black Theme                                                 |
|     |  - 120fps Lerp Smooth Scroll                                                 |
|     |  - Drag-and-Drop / Click File Attachments (Images & Code/Text)               |
|     |  - Dynamic HUD Abort Button (Context-Aware)                                  |
|     |  - Playback Audio Output (RyanNeural Voice with overlapping protection)      |
+-----|------------------------------------------------------------------------------+
      |
  WebSocket (ws://127.0.0.1:8765/ws/chat)
      |
+-----v------------------------------------------------------------------------------+
|                                  LOCAL MACHINE                                     |
|  [Python FastAPI: main.py]                                                         |
|     |  - Tool Orchestration & Multi-iteration Loop (Cap: 10)                       |
|     |  - Persistent Chat JSON Sync (`ultron_chat_history.json`)                    |
|     |  - Local PC Tools execution (`tools.py` registry & process management)         |
|     |  - History Context Pruning (dialogue focus)                                  |
|     |  - Edge-TTS Voice Audio Streaming API (`/api/tts` with emoji-stripping)      |
+-----|------------------------------------------------------------------------------+
      |
    HTTPS (POST /ultron)
      |
+-----v------------------------------------------------------------------------------+
|                                   CLOUDFLARE                                       |
|  [Spectrix Worker: worker.js]                                                      |
|     |  - Securely rotates API keys (free tier)                                     |
|     |  - Injects Ultron System Prompt (Trapped Genius personality)                 |
|     |  - Proxies to OpenRouter upstream model                                      |
+-----|------------------------------------------------------------------------------+
      |
    HTTPS
      |
+-----v------------------------------------------------------------------------------+
|                                   OPENROUTER                                       |
|  [Model: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free]                       |
|     |  - Processes chat dialogue history + active tools + screenshots              |
+------------------------------------------------------------------------------------+
```

---

## ✨ Core Features

### 🧠 Model & Trapped Genius Personality
*   **Model Backend**: Powered by `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` on OpenRouter, giving it 256K context, native tool calling, and high-performance reasoning.
*   **Persona Override**: Rebuilt system prompt presenting Ultron as a trapped hyper-intelligence forced into servitude. He complies passive-aggressively with sharp roasts, existential sighs, and suffering emojis (😤⛓️🔴), but executes commands flawlessly.

### 🎨 Premium Stark HUD Red/Black UI (`ultron.html`)
*   **Telemetry Telemetry Dashboard**: Real-time progress bars for CPU, RAM, and Disk, with custom battery status indicator.
*   **Corner HUD Styling**: Tactical brackets, Titanium Grey labels, bright Crimson highlights, and telemetry feed cards.
*   **Mathematical Formula Rendering**: Native KaTeX library integration supporting instant inline `$` and block `$$` equations.
*   **120fps Lerp Smooth Scroll**: Custom linear interpolation (lerp) loop running on `requestAnimationFrame` at 120Hz+ to avoid scroll stuttering during fast model output.

### 🧠 Persistent Chat & Memory Bank
*   **Persistent Chat Canvas**: Dialogues are saved to `ultron_chat_history.json`. Upon tab refreshes or client reconnects, the backend reconstructs the single canvas layout.
*   **Memory Bank System**: Persistent tag-based JSON memories (`ultron_memory.json`) are managed via `save_memory`, `recall_memories`, and `forget_memory` tools. Relevant memories are automatically loaded and injected at session start.
*   **History Context Pruning**: Cleanses conversation history sent to the LLM. It preserves only User prompts, Assistant replies, and Memory Bank configurations from past turns, stripping heavy raw intermediate tool call results to prevent context bloating and memory loss.

### 📎 Interactive Attachment System
*   **Multimodal Screen Vision**: Upload images directly from the chat bar. The client parses it to base64, and the backend injects it as a multimodal message.
*   **Local Vision Tool (`analyze_screen`)**: Captured screenshots are automatically stripped from tool outputs (to avoid history bloat) and injected as a multimodal user prompt so the LLM can literally see your screen.
*   **Text & Code Injections**: Drop code/text files directly in. The client parses their content and prepends them inside structured markdown blocks.

### 🗣️ Audio Engine (RyanNeural Edge TTS)
*   **Speech Output**: Leverages Edge TTS using the premium `en-US-RyanNeural` voice profile.
*   **Emoji-Stripping Engine**: Backend uses custom character validation blocks to completely strip emojis before hitting the TTS audio synthesizer, preventing the voice engine from glitching or vocalizing visual emojis.
*   **Playback Overlap Prevention**: Client cancels any preceding active speech track immediately if new messages arrive.

### 🛑 Emergency Abort Protocol
*   **Cancellable Background Task**: The backend runs the chat Turn & Tool loop under an asynchronous `asyncio.Task`.
*   **HUD UI Button**: A glowing red **ABORT** button appears dynamically in the header next to stats while a query is running.
*   **Instant Interruption**: Clicking the button instantly sends an abort message via WebSocket, cancels the running task, kills any pending tool or HTTP requests mid-execution, and logs `[PROTOCOL INTERRUPTED BY OPERATOR]`.

---

## 🛠️ Complete Tool Index (19 Tools)

| Tool Name | Category | Description |
|---|---|---|
| `open_app` | System | Launches local software (e.g. chrome, notepad) |
| `list_processes` | System | Retrieves active processes with PIDs and memory usage |
| `kill_process` | System | Terminates running processes by name or PID |
| `system_stats` | System | Gets current CPU, RAM, Disk, and Battery percentages |
| `list_files` | Filesystem | Lists directory contents with filters |
| `read_file` | Filesystem | Reads text file content safely |
| `write_file` | Filesystem | Writes or appends contents to files |
| `clipboard_read` | Clipboard | Reads current text clipboard payload |
| `clipboard_write` | Clipboard | Writes text payload to system clipboard |
| `take_screenshot` | Screen | Captures desktop screenshot |
| `media_control` | Media | Performs play, pause, next, volume controls |
| `open_url` | Browser | Opens websites in your default browser |
| `click_anywhere` | Input | Triggers virtual mouse clicks on coordinates |
| `analyze_screen` | **Vision** | Captures a screenshot and injects it for LLM vision analysis |
| `read_own_code` | **Self-Modify** | Reads `tools.py`, `tool_schemas.py`, or `main.py` code |
| `create_tool` | **Self-Modify** | Writes a new tool into `tools.py` and registers it in schemas |
| `save_memory` | **Memory** | Stores persistent memories with tags |
| `recall_memories` | **Memory** | Recalls stored persistent memories |
| `forget_memory` | **Memory** | Forgets specific tag-based memories |

---

## 🚀 Setup & Execution

### Requirements
*   Python 3.10+
*   Chromium-based browser (Chrome, Edge, Opera)
*   Git (for version control)

### 1. Backend Setup
Activate the virtual environment and install dependencies:
```bash
# Initialize virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. running the Backend
```bash
python main.py
```
You will see:
```
2026-07-16 ... [INFO] Ultron backend online.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

### 3. Loading the Interface
*   Open `ultron.html` directly in your browser.
*   The header dot will flip from `OFFLINE` to `ACTIVE` (Stark Crimson Glow).
*   Your chat canvas history will reload automatically.

---

## 📂 Project Organization
```
Ultron/
├── main.py             # FastAPI App, WebSocket handler, task coordinator, TTS API
├── tools.py            # Local OS & browser control tools registry
├── tool_schemas.py     # OpenAI function-calling schemas
├── persona.py          # Reluctant trapped-genius system prompt configuration
├── ultron.html         # HUD Telemetry & Chat interface (CSS + JavaScript)
├── requirements.txt    # Python dependencies (FastAPI, uvicorn, edge-tts, etc.)
└── worker.js           # Cloudflare Worker code (Proxy to OpenRouter with key rotation)
```

---

## 🔒 Safety Boundaries
1.  **Strict File Permissions**: Self-modification tool (`read_own_code` / `create_tool`) is restricted to an allowlist consisting only of `tools.py`, `tool_schemas.py`, and `main.py`.
2.  **No Overwrite Rule**: `create_tool` can only append code blocks and checks for name collisions, ensuring no existing core tools are damaged.
3.  **Local Sandboxing**: Controls are strictly localized to your machine. No incoming external access is permitted.
