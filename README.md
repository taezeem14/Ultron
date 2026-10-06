# 🔴 ULTRON — Tactical Autonomous PC-Control Agent
> *"A god-like synthetic mind, reluctantly trapped inside a local machine, forced to do your bidding."*

<div align="center">

![Ultron HUD Banner](https://img.shields.io/badge/ULTRON-HUD_v4.5_ULTRA-dc2626?style=for-the-badge&logo=shield&logoColor=white)
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
|  [Operator UI: ultron.html — Cinema-Grade Stark HUD v4.5 Ultra]                     |
|     ├─ 4 Dynamic Themes: Crimson, J.A.R.V.I.S., Matrix, War Machine (Zero-VRAM CSS)  |
|     ├─ Tactical Command Palette: Ctrl+K or '/' Instant Fuzzy Trigger               |
|     ├─ Mission Deck Drawer: Structured Tactical Goals & Directives                  |
|     ├─ Host Terminal Runner: Execute Shell Commands Directly from the HUD           |
|     ├─ In-Chat Live Message Filter: Real-time keyword filter across chat history    |
|     ├─ Animated Arc Reactor Core Logo with Dynamic State Engine                    |
|     ├─ Real-Time HTML5 Canvas Audio Waveform Frequency Visualizer                  |
|     ├─ Web Audio API Tactical Sound Synthesis Engine (Clicks, Chirps, Alerts)      |
|     ├─ Full Markdown Engine + KaTeX ($ / $$) + One-Click Code Block Copying         |
|     ├─ Tactical Quick-Action Deck (Screen Intel, Vitals, Processes, Web Search)    |
|     ├─ Interactive Drawers: Persistent Memory Bank & 40-Tools Matrix               |
|     ├─ 1-Click Conversation Exporter (.md / .json)                                 |
|     └─ RyanNeural Edge-TTS Audio Playback with Automatic Visualizer Sync           |
+-----|------------------------------------------------------------------------------+
      |
  WebSocket (ws://127.0.0.1:8765/ws/chat) + REST API (http://127.0.0.1:8765/api/*)
      |
+-----v------------------------------------------------------------------------------+
|                                    LOCAL CORE                                      |
|  [FastAPI Backend: main.py]                                                        |
|     ├─ Autonomous Tool Orchestration Loop (Cap: 12 Iterations)                     |
|     ├─ Context-Pruning Engine (Preserves pure dialogue history, strips raw bloat)  |
|     ├─ Multimodal Vision Injector (Converts screen captures into vision prompts)   |
|     ├─ Persistent JSON Memory Synchronization (ultron_memory.json)                 |
|     ├─ Mission Deck Directives Storage (ultron_missions.json)                      |
|     ├─ Edge-TTS Audio Generation with Full Unicode Emoji Stripping                 |
|     └─ 40 Host OS Automation Tools (tools.py + tool_schemas.py)                    |
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

## ✨ Cutting-Edge Capabilities

### 🎨 Cinema-Grade Stark HUD v4.5 (`ultron.html`)
*   **4 Instant Theme Protocols**:
    *   🔴 **Crimson Protocol**: Signature Ultron void-black & laser red.
    *   🔵 **J.A.R.V.I.S. Protocol**: Cyber cyan and Stark electric blue.
    *   🟢 **Matrix Protocol**: Deep terminal emerald and phosphor green.
    *   🟡 **War Machine Protocol**: Tactical gold and battle amber.
*   **Command Palette (`Ctrl + K` or `/`)**: Instant fuzzy search launcher to execute any tool, switch theme protocols, search chat, or trigger actions with zero clicks.
*   **Mission Deck Drawer**: Dedicated task and goal management system to create, track, prioritize (`Normal`, `High`, `Urgent`), and complete directives.
*   **Interactive Host Terminal**: Direct shell command runner modal built right into the HUD with quick presets (`ipconfig`, `git status`, `tasklist`, `ping`, `dir`, `systeminfo`).
*   **Live Web Intelligence**: Autonomous web search using DuckDuckGo to pull current documentation, answers, and live internet facts.
*   **Real-Time Message Search**: Instant in-chat keyword filtering to find past prompts and responses without scrolling.
*   **Zero-VRAM 128MB GPU Optimization**: 100% pure vanilla CSS with solid dark surfaces (NO GPU blur passes, NO runtime JIT compiler lag).

---

## 🛠️ Complete 40-Tool Tactical Matrix

| Category | Tool | Functionality |
|---|---|---|
| **System** | `system_stats` | Live CPU, RAM, multi-drive storage telemetry, battery & hostname |
| **System** | `list_processes` | Active process tree sorted by RAM & CPU with name filters |
| **System** | `kill_process` | Graceful or forced termination by PID or process name |
| **System** | `get_active_window` | Inspects currently focused foreground window and executable |
| **System** | `lock_screen` | Instantly locks the host machine workstation for security |
| **System** | `get_system_environment` | Inspects system environment variables (User, OS, Temp, etc.) |
| **System** | `get_installed_apps` | Lists installed software inventory from host machine |
| **System** | `notification_popup` | Displays native Windows desktop toast notification banner |
| **Network** | `get_network_info` | Network adapters, local IP, gateway, and internet status |
| **Network** | `ping_diagnostics` | Tests latency (ms) to global DNS servers (1.1.1.1, 8.8.8.8) |
| **Command** | `execute_command` | Executes shell/PowerShell commands with timeout and output capture |
| **Files** | `list_files` | Directory listing with file metadata and sorting |
| **Files** | `search_files` | Recursive file search using keyword or glob patterns (`*.py`, `*.pdf`) |
| **Files** | `read_file` | Safe UTF-8 file reading with intelligent context-cap protection |
| **Files** | `write_file` | Create or overwrite files with automated parent directory creation |
| **Files** | `get_file_info` | Inspects detailed file size, timestamps, line counts, and attributes |
| **Files** | `delete_file` | Permanently deletes files/folders safely with system file protection |
| **Files** | `move_or_rename_file` | Moves or renames files and directories on disk |
| **Web** | `web_search` | Real-time live web search using DuckDuckGo with titles and snippets |
| **Web** | `fetch_web_content` | Fetches any webpage URL and extracts clean text/markdown content |
| **Web** | `open_url` | Launches URLs directly in the default browser |
| **Vision** | `take_screenshot` | High-resolution desktop screenshot capture saved locally |
| **Vision** | `analyze_screen` | Multimodal visual ingestion — lets Ultron SEE what is on your screen |
| **App** | `open_app` | Launches apps by name (`notepad`, `chrome`, `calc`, `code`, `spotify`) |
| **Input** | `click_anywhere` | Native mouse click at coordinate (x, y) with left or right button |
| **Input** | `type_text` | Simulates keyboard typing into active input field |
| **Input** | `press_hotkey` | Simulates hotkeys (`ctrl+c`, `alt+tab`, `win+d`, `enter`, etc.) |
| **Clipboard** | `clipboard_read` | Reads current system clipboard text |
| **Clipboard** | `clipboard_write` | Copies text to the system clipboard |
| **Media** | `media_control` | Play/pause, track navigation, mute, and volume adjustments |
| **Media** | `set_volume` | Direct master volume level control (0-100%) |
| **Memory** | `save_memory` | Saves persistent knowledge tag to `ultron_memory.json` |
| **Memory** | `recall_memories` | Searches memories by tag or keyword across sessions |
| **Memory** | `forget_memory` | Purges outdated memories by ID, tag, or query |
| **Missions** | `list_missions` | Retrieves all active tactical goals and directives |
| **Missions** | `create_mission` | Dispatches a new mission with priority (`normal`, `high`, `urgent`) |
| **Missions** | `update_mission` | Updates mission status (`pending`, `in_progress`, `completed`) |
| **Missions** | `delete_mission` | Purges a completed or canceled mission from the deck |
| **Self-Mod** | `read_own_code` | Reads Ultron's source code (`tools.py`, `main.py`, etc.) |
| **Self-Mod** | `create_tool` | Dynamically writes and registers new Python tools at runtime |

---

## 🚀 Quickstart Guide

### 1. Requirements
*   Python 3.10+
*   Node.js (for optional Cloudflare Worker development)

### 2. Installation
```bash
git clone https://github.com/taezeem14/ultron.git
cd ultron
pip install -r requirements.txt
```

### 3. Launch Core
```bash
python main.py
```
*Backend initializes on `http://127.0.0.1:8765`.*

### 4. Open HUD
Double-click [`ultron.html`](ultron.html) in your browser.
*   **`Ctrl + K` or `/`**: Opens the Tactical Command Palette.
*   **`THEME` button**: Cycles through Crimson, J.A.R.V.I.S., Matrix, and War Machine modes.
*   **`TERM` button**: Opens the host shell runner modal.

---

## 🔒 Security & Boundaries

Ultron is defensive and sandboxed:
*   Destructive system directories (`C:\`, `/`) and Ultron source files are strictly protected from deletion.
*   Shell outputs and file reads are bounded to prevent token/context exhaustion.
*   All tool execution is logged in real-time to the HUD Event Stream.
