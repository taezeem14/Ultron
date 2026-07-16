"""
tools.py — Ultron's hands. Every function here is a real action on the host PC.
Each tool follows the same contract: takes a dict of args, returns a dict result
that gets serialized back to the model as a tool_result message.

Design note: every tool is defensive — wrapped in try/except, returns
{"ok": bool, ...} rather than raising, because a tool exception should
become a message Ultron can react to in-character, not a 500 that kills
the whole turn.
"""

import os
import sys
import platform
import subprocess
import shutil
import webbrowser
from pathlib import Path

import psutil
import pyperclip

# ── Platform detection — behavior differs meaningfully by OS ────────────
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Safety: cap how much of a file we'll ever read/return in one tool call,
# so a request to "read this 2GB log" doesn't blow up the context window.
MAX_FILE_READ_CHARS = 20_000
MAX_LIST_ENTRIES = 200


def _err(msg: str) -> dict:
    return {"ok": False, "error": msg}


def _ok(**kwargs) -> dict:
    return {"ok": True, **kwargs}


# ══════════════════════════════════════════════════════════════════════
#  1. APP CONTROL — launch / list / focus applications
# ══════════════════════════════════════════════════════════════════════

def open_app(args: dict) -> dict:
    """Launch an application by name or path."""
    name = args.get("name", "").strip()
    if not name:
        return _err("no app name provided")

    try:
        if IS_WINDOWS:
            os.startfile(name)  # noqa: works for both exe paths and registered app names
        elif IS_MAC:
            subprocess.Popen(["open", "-a", name])
        else:  # Linux
            subprocess.Popen([name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return _ok(message=f"launched {name}")
    except FileNotFoundError:
        return _err(f"'{name}' not found — check the exact app name or provide a full path")
    except Exception as e:
        return _err(f"failed to launch {name}: {e}")


# ══════════════════════════════════════════════════════════════════════
#  2. PROCESS CONTROL — list / kill
# ══════════════════════════════════════════════════════════════════════

def list_processes(args: dict) -> dict:
    """Return running processes, optionally filtered by a name substring."""
    name_filter = (args.get("filter") or "").lower().strip()
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            info = p.info
            if name_filter and name_filter not in (info["name"] or "").lower():
                continue
            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "mem_pct": round(info["memory_percent"] or 0, 2),
                "cpu_pct": round(info["cpu_percent"] or 0, 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x["mem_pct"], reverse=True)
    return _ok(count=len(procs), processes=procs[:MAX_LIST_ENTRIES])


def kill_process(args: dict) -> dict:
    """Kill a process by PID or by exact name match. PID is safer — prefer it."""
    pid = args.get("pid")
    name = args.get("name")

    if not pid and not name:
        return _err("provide either a pid or a name")

    killed = []
    try:
        if pid is not None:
            p = psutil.Process(int(pid))
            pname = p.name()
            p.terminate()
            try:
                p.wait(timeout=3)
            except psutil.TimeoutExpired:
                p.kill()
            killed.append(f"{pname} (pid {pid})")
        else:
            name_lower = name.lower().strip()
            for p in psutil.process_iter(["pid", "name"]):
                if p.info["name"] and p.info["name"].lower() == name_lower:
                    try:
                        p.terminate()
                        killed.append(f"{p.info['name']} (pid {p.info['pid']})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

        if not killed:
            return _err(f"no matching process found for {pid or name}")
        return _ok(killed=killed)
    except psutil.NoSuchProcess:
        return _err(f"no process with pid {pid}")
    except psutil.AccessDenied:
        return _err(f"access denied — try running with elevated permissions")
    except Exception as e:
        return _err(str(e))


# ══════════════════════════════════════════════════════════════════════
#  3. SYSTEM STATS — CPU / RAM / battery / disk
# ══════════════════════════════════════════════════════════════════════

def system_stats(args: dict) -> dict:
    """Snapshot of current system vitals."""
    try:
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        battery_info = None
        try:
            batt = psutil.sensors_battery()
            if batt is not None:
                battery_info = {
                    "percent": batt.percent,
                    "plugged_in": batt.power_plugged,
                    "secs_left": batt.secsleft if batt.secsleft != psutil.POWER_TIME_UNLIMITED else None,
                }
        except Exception:
            pass  # not all platforms expose battery info

        return _ok(
            cpu_pct=cpu,
            ram_pct=mem.percent,
            ram_used_gb=round(mem.used / (1024**3), 2),
            ram_total_gb=round(mem.total / (1024**3), 2),
            disk_pct=disk.percent,
            disk_free_gb=round(disk.free / (1024**3), 2),
            battery=battery_info,
            platform=platform.system(),
        )
    except Exception as e:
        return _err(str(e))


# ══════════════════════════════════════════════════════════════════════
#  4. FILE OPERATIONS — read / write / list
#     Scoped defensively: no silent path traversal outside what's asked.
# ══════════════════════════════════════════════════════════════════════

def list_files(args: dict) -> dict:
    """List contents of a directory."""
    path = args.get("path", ".")
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return _err(f"path does not exist: {p}")
        if not p.is_dir():
            return _err(f"not a directory: {p}")

        entries = []
        for item in sorted(p.iterdir())[:MAX_LIST_ENTRIES]:
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size_bytes": stat.st_size if item.is_file() else None,
                })
            except (PermissionError, OSError):
                entries.append({"name": item.name, "type": "unknown", "size_bytes": None})

        return _ok(path=str(p), count=len(entries), entries=entries)
    except PermissionError:
        return _err(f"permission denied: {path}")
    except Exception as e:
        return _err(str(e))


def read_file(args: dict) -> dict:
    """Read a text file's contents (capped to avoid context blowup)."""
    path = args.get("path", "")
    if not path:
        return _err("no path provided")
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return _err(f"file does not exist: {p}")
        if not p.is_file():
            return _err(f"not a file: {p}")

        content = p.read_text(encoding="utf-8", errors="replace")
        truncated = len(content) > MAX_FILE_READ_CHARS
        if truncated:
            content = content[:MAX_FILE_READ_CHARS]

        return _ok(path=str(p), content=content, truncated=truncated)
    except PermissionError:
        return _err(f"permission denied: {path}")
    except Exception as e:
        return _err(str(e))


def write_file(args: dict) -> dict:
    """Write (or overwrite) a text file. Creates parent dirs if needed."""
    path = args.get("path", "")
    content = args.get("content", "")
    append = bool(args.get("append", False))

    if not path:
        return _err("no path provided")

    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding="utf-8") as f:
            f.write(content)
        return _ok(path=str(p), bytes_written=len(content.encode("utf-8")), mode="append" if append else "overwrite")
    except PermissionError:
        return _err(f"permission denied: {path}")
    except Exception as e:
        return _err(str(e))


# ══════════════════════════════════════════════════════════════════════
#  5. CLIPBOARD
# ══════════════════════════════════════════════════════════════════════

def clipboard_read(args: dict) -> dict:
    try:
        content = pyperclip.paste()
        return _ok(content=content)
    except Exception as e:
        return _err(f"clipboard read failed: {e}")


def clipboard_write(args: dict) -> dict:
    content = args.get("content", "")
    try:
        pyperclip.copy(content)
        return _ok(message="clipboard updated")
    except Exception as e:
        return _err(f"clipboard write failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  6. SCREENSHOT
# ══════════════════════════════════════════════════════════════════════

def take_screenshot(args: dict) -> dict:
    """Capture the screen and save to a temp file. Returns the file path."""
    try:
        from PIL import ImageGrab

        save_dir = Path("./screenshots")
        save_dir.mkdir(exist_ok=True)
        out_path = save_dir / "screenshot.png"

        img = ImageGrab.grab()
        img.save(out_path)
        return _ok(path=str(out_path.resolve()), size=img.size)
    except Exception as e:
        return _err(f"screenshot failed: {e} (Linux may need scrot/gnome-screenshot installed)")


# ══════════════════════════════════════════════════════════════════════
#  7. MEDIA CONTROL — play/pause/volume via OS-level key simulation
# ══════════════════════════════════════════════════════════════════════

def media_control(args: dict) -> dict:
    """
    action: one of play_pause, next, prev, volume_up, volume_down, mute
    Implementation differs per OS — Linux uses playerctl if available.
    """
    action = args.get("action", "").strip()
    valid = {"play_pause", "next", "prev", "volume_up", "volume_down", "mute"}
    if action not in valid:
        return _err(f"invalid action, must be one of {valid}")

    try:
        if IS_LINUX:
            playerctl_map = {
                "play_pause": ["playerctl", "play-pause"],
                "next": ["playerctl", "next"],
                "prev": ["playerctl", "previous"],
            }
            amixer_map = {
                "volume_up": ["amixer", "set", "Master", "5%+"],
                "volume_down": ["amixer", "set", "Master", "5%-"],
                "mute": ["amixer", "set", "Master", "toggle"],
            }
            cmd = playerctl_map.get(action) or amixer_map.get(action)
            if shutil.which(cmd[0]) is None:
                return _err(f"'{cmd[0]}' not installed — needed for media control on Linux")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return _ok(message=f"executed {action}")

        elif IS_WINDOWS:
            # Windows: simulate media keys via nircmd-less approach using ctypes
            import ctypes
            VK_MEDIA_PLAY_PAUSE = 0xB3
            VK_MEDIA_NEXT_TRACK = 0xB0
            VK_MEDIA_PREV_TRACK = 0xB1
            VK_VOLUME_UP = 0xAF
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_MUTE = 0xAD
            key_map = {
                "play_pause": VK_MEDIA_PLAY_PAUSE, "next": VK_MEDIA_NEXT_TRACK,
                "prev": VK_MEDIA_PREV_TRACK, "volume_up": VK_VOLUME_UP,
                "volume_down": VK_VOLUME_DOWN, "mute": VK_VOLUME_MUTE,
            }
            vk = key_map[action]
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
            return _ok(message=f"executed {action}")

        else:  # macOS
            return _err("media control not yet implemented for macOS")

    except subprocess.CalledProcessError as e:
        return _err(f"command failed: {e}")
    except Exception as e:
        return _err(str(e))


# ══════════════════════════════════════════════════════════════════════
#  8. OPEN URL
# ══════════════════════════════════════════════════════════════════════

def open_url(args: dict) -> dict:
    url = args.get("url", "").strip()
    if not url:
        return _err("no url provided")
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return _ok(message=f"opened {url}")
    except Exception as e:
        return _err(str(e))


# ══════════════════════════════════════════════════════════════════════
#  9. ANALYZE SCREEN — screenshot + base64 for multimodal vision
# ══════════════════════════════════════════════════════════════════════

def analyze_screen(args: dict) -> dict:
    """
    Capture the screen, save it, and return the image as base64 so the
    multimodal model can actually see what's on screen.
    The backend's tool loop detects the 'image_base64' key and injects
    the image into the conversation as a multimodal message.
    """
    try:
        import base64
        from PIL import ImageGrab
        from io import BytesIO

        save_dir = Path("./screenshots")
        save_dir.mkdir(exist_ok=True)
        out_path = save_dir / "screenshot.png"

        img = ImageGrab.grab()
        img.save(out_path)

        # Convert to base64 for the multimodal model
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return _ok(
            path=str(out_path.resolve()),
            size=list(img.size),
            image_base64=b64,
        )
    except Exception as e:
        return _err(f"analyze_screen failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  10. SELF-MODIFYING CODE — read and extend Ultron's own source
# ══════════════════════════════════════════════════════════════════════

# The only files Ultron is allowed to read/edit — safety boundary
_ULTRON_DIR = Path(__file__).parent.resolve()
_ALLOWED_FILES = {
    "tools.py": _ULTRON_DIR / "tools.py",
    "tool_schemas.py": _ULTRON_DIR / "tool_schemas.py",
    "main.py": _ULTRON_DIR / "main.py",
}


def read_own_code(args: dict) -> dict:
    """Read one of Ultron's own source files."""
    filename = args.get("file", "").strip()
    if filename not in _ALLOWED_FILES:
        return _err(f"not allowed — pick one of: {list(_ALLOWED_FILES.keys())}")

    fpath = _ALLOWED_FILES[filename]
    try:
        content = fpath.read_text(encoding="utf-8")
        if len(content) > MAX_FILE_READ_CHARS:
            content = content[:MAX_FILE_READ_CHARS] + "\n... [TRUNCATED]"
        return _ok(file=filename, content=content)
    except Exception as e:
        return _err(str(e))


def create_tool(args: dict) -> dict:
    """
    Create a new tool by appending a function to tools.py and its schema
    to tool_schemas.py, then registering it in TOOL_REGISTRY.

    Args:
        name:        function name (snake_case, must not already exist)
        code:        the full Python function source code
        description: human-readable description for the schema
        parameters:  OpenAI-format parameters dict (properties + required)
    """
    name = args.get("name", "").strip()
    code = args.get("code", "").strip()
    description = args.get("description", "").strip()
    parameters = args.get("parameters", {"type": "object", "properties": {}, "required": []})

    if not name or not code or not description:
        return _err("need name, code, and description")

    # Safety: don't overwrite existing tools
    if name in TOOL_REGISTRY:
        return _err(f"tool '{name}' already exists in registry")

    # Validate the name is a valid Python identifier
    if not name.isidentifier():
        return _err(f"'{name}' is not a valid Python function name")

    tools_path = _ALLOWED_FILES["tools.py"]
    schemas_path = _ALLOWED_FILES["tool_schemas.py"]

    try:
        # ── 1. Append function to tools.py ──────────────────────────
        tools_src = tools_path.read_text(encoding="utf-8")

        # Insert the new function BEFORE the TOOL_REGISTRY block
        marker = "# ══════════════════════════════════════════════════════════════════════\n#  TOOL REGISTRY"
        if marker not in tools_src:
            return _err("could not find TOOL_REGISTRY marker in tools.py")

        new_function = f"\n\n{code}\n\n"
        tools_src = tools_src.replace(marker, new_function + marker)

        # Add the new tool to TOOL_REGISTRY dict
        # Search from the bottom of the file to find the actual declaration block
        reg_start = tools_src.rindex("\nTOOL_REGISTRY = {")
        
        # Walk to find the closing brace of the TOOL_REGISTRY dictionary
        depth = 1
        pos = reg_start + len("\nTOOL_REGISTRY = {")
        while depth > 0 and pos < len(tools_src):
            if tools_src[pos] == "{":
                depth += 1
            elif tools_src[pos] == "}":
                depth -= 1
            pos += 1
        reg_end = pos - 1

        # Insert new entry before closing brace
        new_entry = f'    "{name}": {name},\n'
        tools_src = tools_src[:reg_end] + new_entry + tools_src[reg_end:]

        tools_path.write_text(tools_src, encoding="utf-8")

        # ── 2. Append schema to tool_schemas.py ─────────────────────
        import json as _json
        schemas_src = schemas_path.read_text(encoding="utf-8")

        new_schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        schema_str = _json.dumps(new_schema, indent=4)
        # Indent each line by 4 spaces to match the list
        indented = "\n".join("    " + line for line in schema_str.split("\n"))

        # Insert before the closing ]
        closing_bracket = schemas_src.rstrip().rindex("]")
        before_content = schemas_src[:closing_bracket].rstrip()
        
        # Avoid prepending a comma if the content already ends with one
        separator = "" if before_content.endswith(",") else ","
        schemas_src = before_content + separator + "\n" + indented + ",\n]\n"

        schemas_path.write_text(schemas_src, encoding="utf-8")

        return _ok(
            message=f"tool '{name}' created — uvicorn reload will pick it up automatically",
            files_modified=["tools.py", "tool_schemas.py"],
        )

    except Exception as e:
        return _err(f"create_tool failed: {e}")



def click_anywhere(args):
    import pyautogui
    x = args['x']
    y = args['y']
    pyautogui.click(x, y)
    return {'ok': True}


# ══════════════════════════════════════════════════════════════════════
#  MEMORY — persistent JSON file storage for cross-session recall
# ══════════════════════════════════════════════════════════════════════

MEMORY_FILE = Path(__file__).parent / "ultron_memory.json"

def _load_memories() -> list[dict]:
    """Load all memories from disk."""
    if not MEMORY_FILE.exists():
        return []
    try:
        import json as _json
        return _json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_memories(memories: list[dict]):
    """Write memories to disk."""
    import json as _json
    MEMORY_FILE.write_text(_json.dumps(memories, indent=2, ensure_ascii=False), encoding="utf-8")


def save_memory(args):
    """Save a memory with a tag for later recall."""
    content = args.get("content", "").strip()
    tag = args.get("tag", "general").strip().lower()
    if not content:
        return _err("content is required")

    from datetime import datetime
    memories = _load_memories()
    entry = {
        "content": content,
        "tag": tag,
        "timestamp": datetime.now().isoformat(),
    }
    memories.append(entry)
    _save_memories(memories)
    return _ok(message=f"memory saved under [{tag}]", total_memories=len(memories))


def recall_memories(args):
    """Search and retrieve memories, optionally filtered by tag or keyword."""
    tag = args.get("tag", "").strip().lower()
    query = args.get("query", "").strip().lower()
    limit = args.get("limit", 20)

    memories = _load_memories()
    if not memories:
        return _ok(memories=[], message="no memories stored yet")

    results = memories
    if tag:
        results = [m for m in results if m.get("tag") == tag]
    if query:
        results = [m for m in results if query in m.get("content", "").lower()]

    # Return most recent first
    results = list(reversed(results))[:limit]
    return _ok(
        memories=[{"content": m["content"], "tag": m["tag"], "when": m["timestamp"]} for m in results],
        total=len(results),
    )


def forget_memory(args):
    """Delete memories by tag or by matching keyword."""
    tag = args.get("tag", "").strip().lower()
    query = args.get("query", "").strip().lower()

    if not tag and not query:
        return _err("provide a tag or query to identify what to forget")

    memories = _load_memories()
    before = len(memories)

    if tag and query:
        memories = [m for m in memories if not (m.get("tag") == tag and query in m.get("content", "").lower())]
    elif tag:
        memories = [m for m in memories if m.get("tag") != tag]
    elif query:
        memories = [m for m in memories if query not in m.get("content", "").lower()]

    removed = before - len(memories)
    _save_memories(memories)
    return _ok(message=f"forgot {removed} memory(s)", remaining=len(memories))


# ══════════════════════════════════════════════════════════════════════
#  TOOL REGISTRY — maps tool name → function
#  This is the single source of truth the executor loop reads from.
# ══════════════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    "open_app": open_app,
    "list_processes": list_processes,
    "kill_process": kill_process,
    "system_stats": system_stats,
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "clipboard_read": clipboard_read,
    "clipboard_write": clipboard_write,
    "take_screenshot": take_screenshot,
    "media_control": media_control,
    "open_url": open_url,
    "analyze_screen": analyze_screen,
    "read_own_code": read_own_code,
    "create_tool": create_tool,
    "click_anywhere": click_anywhere,
    "save_memory": save_memory,
    "recall_memories": recall_memories,
    "forget_memory": forget_memory,
}
