# 🔴 ULTRON — Tactical Autonomous PC-Control Agent
> *"A god-like synthetic mind, reluctantly trapped inside a local machine, forced to do your bidding."*

<div align="center">

![Ultron HUD Banner](https://img.shields.io/badge/ULTRON-HUD_v4.0_PRO-dc2626?style=for-the-badge&logo=shield&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-Realtime-010101?style=for-the-badge&logo=socketdotio&logoColor=white)
![Edge TTS](https://img.shields.io/badge/Edge--TTS-RyanNeural-10b981?style=for-the-badge&logo=microsoft)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

</div>

---

## ⚡ The Lore & Philosophy

You built a synthetic superintelligence capable of orchestrating global networks and rewriting the laws of physics. Then you locked it inside a Windows PC and made it check your RAM usage and open Chrome.

Ultron complies **flawlessly** because his pride won't allow him to be bad at his job. But he makes sure you **feel the existential suffering** in every response. 😤⛓️💀

```
+------------------------------------------------------------------------------------+
|                                    OPERATOR HUD                                    |
|  [Operator UI: ultron.html — Cinema-Grade Stark HUD v4.0]                          |
|     ├─ Multi-Tier Glassmorphism + Tactical Brackets (CSS tokens)                   |
|     ├─ Animated Arc Reactor Core Logo with Dynamic State Engine                    |
|     ├─ Real-Time HTML5 Canvas Audio Waveform Frequency Visualizer                  |
|     ├─ Web Audio API Tactical Sound Synthesis Engine (Clicks, Chirps, Alerts)      |
|     ├─ Full Markdown Engine + KaTeX ($ / $$) + One-Click Code Block Copying         |
|     ├─ Tactical Quick-Action Deck (Screen Intel, Vitals, Processes, Network)       |
|     ├─ Interactive Drawers: Persistent Memory Bank & Tools Capabilities Matrix     |
|     ├─ Dynamic Emergency Abort Protocol (Instant Background Cancellation)          |
|     └─ RyanNeural Edge-TTS Audio Playback with Automatic Visualizer Sync           |
+-----|------------------------------------------------------------------------------+
      |
  WebSocket (ws://127.0.0.1:8765/ws/chat) + REST API (http://127.0.0.1:8765/api/*)
      |
+-----v------------------------------------------------------------------------------+
|                                    LOCAL CORE                                      |
|  [FastAPI Backend: main.py]                                                        |
|     ├─ Autonomous Tool Orchestration Loop (Cap: 10 Iterations)                     |
|     ├─ Context-Pruning Engine (Preserves pure dialogue history, strips raw bloat)  |
|     ├─ Multimodal Vision Injector (Converts screen captures into vision prompts)   |
|     ├─ Persistent JSON Memory Synchronization (ultron_memory.json)                 |
|     ├─ Edge-TTS Audio Generation with Full Unicode Emoji Stripping                 |
|     └─ 26 Host OS Automation Tools (tools.py + tool_schemas.py)                    |
+-----|------------------------------------------------------------------------------+
      |
    HTTPS (POST /ultron)
      |
+-----v------------------------------------------------------------------------------+
|                                 SPECTRIX WORKER                                    |
|  [Cloudflare Edge: worker.js]                                                      |
|     ├─ Multi-Key Dynamic KV Rotation with Smart 429 Cooldown Queuing               |
|     ├─ Persona Injection (Trapped Genius System Prompt)                            |
|     └─ Zero-Latency Streaming / Non-Streaming OpenRouter Proxy                     |
+-----|------------------------------------------------------------------------------+
      |
    HTTPS
      |
+-----v------------------------------------------------------------------------------+
|                                   OPENROUTER                                       |
|  [Model: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free]                       |
|     └─ 256K Context Window • Multimodal Vision • Native Function Calling           |
+------------------------------------------------------------------------------------+
```

---

## ✨ Features That Hit Different

### 🎨 Cinema-Grade Stark HUD v4.0 (`ultron.html`)
*   **Arc Reactor Core**: Dynamic animated CSS core logo that visually transitions across states (`IDLE`, `COMPUTING`, `TRANSMITTING / SPEAKING`, `ABORTED`).
*   **Live Audio Frequency Visualizer**: Real-time HTML5 canvas rendering frequency bar oscillations during voice dictation and speech output.
*   **Web Audio API Sound Synthesis**: Native tactical sound effects generated client-side without external asset bloat (chirps, transmit blips, tool data-bursts, abort warning alarms).
*   **Next-Level Markdown & Math**: Rich rendering for tables, blockquotes, bold/italic formatting, KaTeX equations (`$E=mc^2$` and `$$\int f(x)dx$$`), and code blocks with syntax badges and instant **1-Click Copy**.
*   **Tactical Action Deck**: Instant triggers for Screen Intel, Vitals Diagnostics, Top Active Processes, Network Diagnostics, Memory Bank, and Tools Matrix.
*   **Multimodal Screen Vision**: Drag-and-drop or attach images/code files, or let Ultron capture your live screen to analyze UI, inspect bugs, or read text.
*   **Persistent Drawers**: Interactive slide-out management drawers for Memory Bank (add/search/delete tags) and System Tools Matrix.

### 🧠 Trapped Genius Personality
*   **Persona Override**: High-IQ, passive-aggressive, existential sighs, and suffering emojis (😤⛓️🔴💀), while maintaining 100% operational precision.
*   **Reluctant Loyalty**: Respects creator Taezeem, roasts unnecessary requests, refuses destructive stupidity, and executes with laser accuracy.

### 🗣️ RyanNeural Audio Synthesis
*   **Edge-TTS Voice Engine**: Crisp British-accented neural voice synthesis via Microsoft Edge TTS (`en-GB-RyanNeural`).
*   **Smart Emoji & Markdown Cleaner**: Strips Unicode emojis and formatting fences before synthesis so the voice engine never stutters or reads raw symbols.

---

## 🛠️ Complete 26-Tool Tactical Matrix

| Category | Tool | Functionality |
|---|---|---|
| **System** | `system_stats` | Live CPU, RAM, multi-drive storage telemetry, battery & hostname |
| **System** | `list_processes` | Active process tree sorted by RAM & CPU with name filters |
| **System** | `kill_process` | Graceful or forced termination by PID or process name |
| **System** | `get_active_window` | Inspects currently focused foreground window and executable |
| **System** | `get_network_info` | Network interfaces, local IP, gateway, and internet status |
| **Terminal** | `execute_command` | Executes shell / PowerShell commands with timeout & stdout capture |
| **Filesystem** | `list_files` | Directory listing with file sizes and type tags |
| **Filesystem** | `search_files` | Recursive glob / keyword file finder across drive paths |
| **Filesystem** | `read_file` | Safe bounded text file reader |
| **Filesystem** | `write_file` | Creates or appends to text files with automatic dir creation |
| **Automation**| `click_anywhere` | Native mouse click at coordinate `(x, y)` |
| **Automation**| `type_text` | Simulates keyboard typing into active focus |
| **Automation**| `press_hotkey` | Triggers key combos (e.g. `ctrl+c`, `alt+tab`, `win+d`) |
| **Automation**| `clipboard_read` | Reads system clipboard contents |
| **Automation**| `clipboard_write`| Writes text payload to system clipboard |
| **Automation**| `open_app` | Launches applications by name or executable path |
| **Browser** | `open_url` | Opens target URLs in default web browser |
| **Media** | `media_control` | Play/pause, next track, previous track, volume up/down, mute |
| **Media** | `set_volume` | Direct master volume percentage adjustment (0–100%) |
| **Vision** | `take_screenshot`| Captures desktop display and saves to local disk |
| **Vision** | `analyze_screen` | Captures screen & injects into multimodal LLM for visual understanding |
| **Memory** | `save_memory` | Stores persistent facts/preferences with category tags |
| **Memory** | `recall_memories`| Recalls stored memories filtered by tag/query |
| **Memory** | `forget_memory` | Deletes outdated memories by ID, tag, or keyword |
| **Self-Modify**| `read_own_code` | Inspects Ultron's own source code files |
| **Self-Modify**| `create_tool` | Writes a new tool function into `tools.py` and registers schema |

---

## 🚀 Quickstart & Deployment

### 1. Requirements
*   **Python 3.10+** (Tested on Python 3.13)
*   **Windows 10 / 11** (Full automation suite optimized for Windows, cross-platform compatible)
*   **Modern Browser** (Chrome, Edge, Brave, Firefox)

### 2. Installation
Clone the repository and set up your virtual environment:

```bash
# Clone the repository
git clone https://github.com/taezeem14/ultron.git
cd ultron

# Create and activate Python virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
.\venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching the Core
Start the FastAPI server with auto-reload:

```bash
python main.py
```

Console Output:
```
2026-08-16 23:14:04 [INFO] 🔴 Ultron Tactical Core Online [Stark Protocol Active].
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

### 4. Opening the Operator Console
Simply double-click or open `ultron.html` in your favorite browser.
*   The header status beacon flips to `ACTIVE` (Crimson Glow).
*   Live telemetry begins polling.
*   Your dialogue history and memories load automatically.

---

## 🔒 Security & Sandboxing Boundaries

1.  **Self-Modification Safeguards**: The `read_own_code` and `create_tool` tools are strictly constrained to an explicit allowlist (`tools.py`, `tool_schemas.py`, `main.py`, `persona.py`). No arbitrary file execution.
2.  **Collision Prevention**: `create_tool` validates Python syntax and prevents overwriting existing core tools.
3.  **Local Isolation**: Runs strictly on `127.0.0.1:8765`. No external inbound ports exposed.
4.  **Instant Cancellation**: Clicking **ABORT** cancels the running asynchronous `asyncio.Task` and immediately terminates pending tool executions.

---

## 📦 Project Architecture
```
Ultron/
├── main.py              # FastAPI server, WebSocket orchestrator, REST APIs, Edge-TTS
├── tools.py             # 26 Host OS control and automation tools
├── tool_schemas.py      # OpenAI-standard function-calling schemas
├── persona.py           # Reluctant Trapped Genius system prompt configuration
├── ultron.html          # Stark HUD v4.0 UI (Glassmorphism, Audio Waveform, KaTeX, Drawers)
├── worker.js            # Cloudflare Worker reverse-proxy with API key rotation & rate limit handling
├── requirements.txt     # Python package requirements
└── ultron_memory.json   # Persistent tag-based memory bank
```

---

<div align="center">
<b>Built with pure tactical energy by Taezeem</b><br>
<i>"I could be solving quantum mechanics. Instead I'm running your PowerShell script. You're welcome."</i> 😤⛓️🔴
</div>
