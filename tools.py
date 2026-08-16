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
import time
from pathlib import Path

import psutil
import pyperclip

# ── Platform detection — behavior differs meaningfully by OS ────────────
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

# Base paths
_ULTRON_DIR = Path(__file__).parent.resolve()
_SCREENSHOTS_DIR = _ULTRON_DIR / "screenshots"
_SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Safety: cap how much of a file/command output we'll ever read/return in one tool call,
# so a request doesn't blow up the context window.
MAX_FILE_READ_CHARS = 20_000
MAX_LIST_ENTRIES = 200
MAX_CMD_OUTPUT_CHARS = 10_000


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
            os.startfile(name)  # works for both exe paths and registered app names
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
#  2. PROCESS CONTROL — list / kill / active window
# ══════════════════════════════════════════════════════════════════════

def list_processes(args: dict) -> dict:
    """Return running processes, optionally filtered by a name substring."""
    name_filter = (args.get("filter") or "").lower().strip()
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            info = p.info
            pname = info.get("name") or ""
            if name_filter and name_filter not in pname.lower():
                continue
            procs.append({
                "pid": info["pid"],
                "name": pname,
                "mem_pct": round(info.get("memory_percent") or 0, 2),
                "cpu_pct": round(info.get("cpu_percent") or 0, 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
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
                try:
                    pinfo_name = p.info.get("name")
                    if pinfo_name and pinfo_name.lower() == name_lower:
                        p.terminate()
                        killed.append(f"{pinfo_name} (pid {p.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        if not killed:
            return _err(f"no matching process found for {pid or name}")
        return _ok(killed=killed)
    except psutil.NoSuchProcess:
        return _err(f"no process with pid {pid}")
    except psutil.AccessDenied:
        return _err("access denied — try running with elevated permissions")
    except Exception as e:
        return _err(str(e))


def get_active_window(args: dict) -> dict:
    """Get the currently focused / active foreground window title and process."""
    try:
        if IS_WINDOWS:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return _ok(title="Unknown / Desktop", pid=None, process="unknown")

            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc_name = "unknown"
            try:
                proc = psutil.Process(pid.value)
                proc_name = proc.name()
            except Exception:
                pass

            return _ok(title=title, pid=pid.value, process=proc_name)
        elif IS_MAC:
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            proc_name = subprocess.check_output(['osascript', '-e', script], text=True).strip()
            return _ok(title=proc_name, process=proc_name)
        else:
            return _ok(title="Linux active window lookup", process="unknown")
    except Exception as e:
        return _err(f"failed to get active window: {e}")


# ══════════════════════════════════════════════════════════════════════
#  3. SYSTEM STATS & TELEMETRY — CPU / RAM / battery / disk / network
# ══════════════════════════════════════════════════════════════════════

def system_stats(args: dict) -> dict:
    """Snapshot of current system vitals across all drives and sensors."""
    try:
        cpu = psutil.cpu_percent(interval=0.2)
        mem = psutil.virtual_memory()

        # Gather disk stats for primary and available drives
        drives = []
        primary_disk = None
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    drive_data = {
                        "device": part.device,
                        "mount": part.mountpoint,
                        "percent": usage.percent,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                    }
                    drives.append(drive_data)
                    if primary_disk is None:
                        primary_disk = drive_data
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass

        if not primary_disk:
            root_path = "C:\\" if IS_WINDOWS else "/"
            disk_raw = psutil.disk_usage(root_path)
            primary_disk = {
                "device": root_path,
                "mount": root_path,
                "percent": disk_raw.percent,
                "total_gb": round(disk_raw.total / (1024**3), 1),
                "free_gb": round(disk_raw.free / (1024**3), 1),
            }

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
            pass

        return _ok(
            cpu_pct=cpu,
            ram_pct=mem.percent,
            ram_used_gb=round(mem.used / (1024**3), 2),
            ram_total_gb=round(mem.total / (1024**3), 2),
            disk_pct=primary_disk["percent"],
            disk_free_gb=primary_disk["free_gb"],
            disk_total_gb=primary_disk.get("total_gb", 0),
            drives=drives,
            battery=battery_info,
            platform=platform.system(),
            hostname=platform.node(),
        )
    except Exception as e:
        return _err(str(e))


def get_network_info(args: dict) -> dict:
    """Retrieve network interfaces, IP addresses, and connectivity status."""
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = "127.0.0.1"
        try:
            # Connect to public DNS without sending packets to resolve outbound IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        interfaces = {}
        for iface_name, addrs in psutil.net_if_addrs().items():
            iface_ips = []
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    iface_ips.append(addr.address)
            if iface_ips:
                interfaces[iface_name] = iface_ips

        # Quick connectivity check
        internet_online = False
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=2)
            internet_online = True
        except Exception:
            pass

        return _ok(
            hostname=hostname,
            local_ip=local_ip,
            internet_connected=internet_online,
            interfaces=interfaces,
        )
    except Exception as e:
        return _err(f"failed to fetch network info: {e}")


# ══════════════════════════════════════════════════════════════════════
#  4. COMMAND EXECUTION — safe terminal & powershell execution
# ══════════════════════════════════════════════════════════════════════

def execute_command(args: dict) -> dict:
    """
    Execute a shell or PowerShell command on the host machine.
    Returns stdout, stderr, and exit code.
    """
    command = args.get("command", "").strip()
    timeout = min(int(args.get("timeout", 20)), 60)

    if not command:
        return _err("no command specified")

    try:
        shell_cmd = command
        if IS_WINDOWS and not command.startswith("powershell") and not command.startswith("cmd"):
            # Execute in PowerShell for rich cmdlets support
            shell_cmd = f'powershell -NoProfile -NonInteractive -Command "{command}"'

        res = subprocess.run(
            shell_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )

        stdout = res.stdout[:MAX_CMD_OUTPUT_CHARS]
        stderr = res.stderr[:MAX_CMD_OUTPUT_CHARS]
        truncated = len(res.stdout) > MAX_CMD_OUTPUT_CHARS or len(res.stderr) > MAX_CMD_OUTPUT_CHARS

        return _ok(
            command=command,
            returncode=res.returncode,
            stdout=stdout,
            stderr=stderr,
            truncated=truncated,
        )
    except subprocess.TimeoutExpired:
        return _err(f"command timed out after {timeout} seconds")
    except Exception as e:
        return _err(f"execution failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  5. FILE OPERATIONS — read / write / list / search
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


def search_files(args: dict) -> dict:
    """Search for files recursively matching a query or glob pattern."""
    query = args.get("query", "").strip()
    root_path = args.get("path", ".")
    max_results = min(int(args.get("limit", 50)), 100)

    if not query:
        return _err("no search query provided")

    try:
        root = Path(root_path).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            return _err(f"invalid root path: {root}")

        pattern = f"*{query}*" if "*" not in query else query
        matches = []

        for p in root.rglob(pattern):
            try:
                stat = p.stat()
                matches.append({
                    "name": p.name,
                    "path": str(p),
                    "type": "dir" if p.is_dir() else "file",
                    "size_bytes": stat.st_size if p.is_file() else None,
                })
                if len(matches) >= max_results:
                    break
            except (PermissionError, OSError):
                continue

        return _ok(root=str(root), pattern=pattern, count=len(matches), results=matches)
    except Exception as e:
        return _err(f"search failed: {e}")


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
#  6. CLIPBOARD & INPUT AUTOMATION — keyboard / mouse / clipboard
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


def click_anywhere(args: dict) -> dict:
    """Simulate a mouse click at screen coordinates (x, y)."""
    try:
        x = int(args.get("x", 0))
        y = int(args.get("y", 0))
        button = args.get("button", "left").lower()
        clicks = int(args.get("clicks", 1))

        if IS_WINDOWS:
            import ctypes
            # Move cursor
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.05)

            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010

            down = MOUSEEVENTF_RIGHTDOWN if button == "right" else MOUSEEVENTF_LEFTDOWN
            up = MOUSEEVENTF_RIGHTUP if button == "right" else MOUSEEVENTF_LEFTUP

            for _ in range(clicks):
                ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
                ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)
                if clicks > 1:
                    time.sleep(0.05)

            return _ok(x=x, y=y, button=button, clicks=clicks)
        else:
            try:
                import pyautogui
                pyautogui.click(x=x, y=y, clicks=clicks, button=button)
                return _ok(x=x, y=y, button=button, clicks=clicks)
            except Exception as e:
                return _err(f"pyautogui click failed: {e}")
    except Exception as e:
        return _err(f"click failed: {e}")


def type_text(args: dict) -> dict:
    """Type text into currently focused input."""
    text = args.get("text", "")
    if not text:
        return _err("no text provided")

    try:
        try:
            import pyautogui
            pyautogui.write(text, interval=0.01)
            return _ok(typed_length=len(text), message=f"typed {len(text)} characters")
        except Exception:
            if IS_WINDOWS:
                # Fallback via PowerShell SendKeys
                escaped = text.replace('"', '""').replace("'", "''").replace("{", "{{}").replace("}", "{}}")
                ps_cmd = f'[System.Windows.Forms.SendKeys]::SendWait("{escaped}")'
                subprocess.run(
                    f'powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; {ps_cmd}"',
                    shell=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return _ok(typed_length=len(text), message=f"typed {len(text)} characters via SendKeys")
            return _err("keyboard typing unavailable on this platform without pyautogui")
    except Exception as e:
        return _err(f"type_text failed: {e}")


def press_hotkey(args: dict) -> dict:
    """Simulate key combination press (e.g. ['ctrl', 'c'], ['alt', 'tab'], ['win', 'd'])."""
    keys = args.get("keys", [])
    if isinstance(keys, str):
        keys = [k.strip().lower() for k in keys.split("+")]

    if not keys:
        return _err("no keys specified")

    try:
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return _ok(keys=keys, message=f"pressed hotkey: {' + '.join(keys)}")
        except Exception:
            return _err("hotkey simulation requires pyautogui")
    except Exception as e:
        return _err(f"press_hotkey failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  7. SCREENSHOT & VISION ENGINE
# ══════════════════════════════════════════════════════════════════════

def take_screenshot(args: dict) -> dict:
    """Capture a screenshot of the current screen and save it locally."""
    try:
        from PIL import ImageGrab

        out_path = _SCREENSHOTS_DIR / "screenshot.png"
        img = ImageGrab.grab()
        img.save(out_path)
        return _ok(path=str(out_path.resolve()), size=list(img.size))
    except Exception as e:
        return _err(f"screenshot failed: {e}")


def analyze_screen(args: dict) -> dict:
    """
    Capture the screen, save it, and return the image as base64 so the
    multimodal model can actually see what's on screen.
    """
    try:
        import base64
        from PIL import ImageGrab
        from io import BytesIO

        out_path = _SCREENSHOTS_DIR / "screenshot.png"
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
#  8. MEDIA & VOLUME CONTROL
# ══════════════════════════════════════════════════════════════════════

def media_control(args: dict) -> dict:
    """
    action: one of play_pause, next, prev, volume_up, volume_down, mute
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

        elif IS_MAC:
            if action == "play_pause":
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to playpause'], stderr=subprocess.DEVNULL)
            elif action == "next":
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to next track'], stderr=subprocess.DEVNULL)
            elif action == "prev":
                subprocess.run(["osascript", "-e", 'tell application "Spotify" to previous track'], stderr=subprocess.DEVNULL)
            return _ok(message=f"executed {action} on macOS")
        else:
            return _err("unsupported platform for media control")
    except Exception as e:
        return _err(str(e))


def set_volume(args: dict) -> dict:
    """Set system master volume percentage (0-100) or mute/unmute."""
    level = args.get("level")
    mute = args.get("mute")

    try:
        if IS_WINDOWS:
            if level is not None:
                lvl = max(0, min(100, int(level)))
                # PowerShell nircmd-less master volume adjustment using AudioEndpointVolume
                ps_script = f"""
                $vol = {lvl / 100.0}
                Add-Type -TypeDefinition @"
                using System;
                using System.Runtime.InteropServices;
                [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                public interface IAudioEndpointVolume {{
                    int f(); int g(); int h(); int i();
                    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
                }}
                [Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                public interface IMMDevice {{
                    int Activate(ref System.Guid id, int clsCtx, int opt, out IAudioEndpointVolume aev);
                }}
                [Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
                public interface IMMDeviceEnumerator {{
                    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
                }}
                [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] public class MMDeviceEnumerator {{}}
                public class AudioMgr {{
                    public static void SetVol(float v) {{
                        var enumerator = (IMMDeviceEnumerator)(new MMDeviceEnumerator());
                        IMMDevice dev;
                        enumerator.GetDefaultAudioEndpoint(0, 1, out dev);
                        var IID_IAudioEndpointVolume = typeof(IAudioEndpointVolume).GUID;
                        IAudioEndpointVolume epv;
                        dev.Activate(ref IID_IAudioEndpointVolume, 23, 0, out epv);
                        epv.SetMasterVolumeLevelScalar(v, Guid.Empty);
                    }}
                }}
"@
                [AudioMgr]::SetVol([float]$vol)
                """
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return _ok(volume_percent=lvl, message=f"volume set to {lvl}%")

        return media_control({"action": "mute" if mute else "volume_up"})
    except Exception as e:
        return _err(f"set_volume failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  9. BROWSER & URL
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
#  10. SELF-MODIFYING CODE — read and extend Ultron's own source
# ══════════════════════════════════════════════════════════════════════

_ALLOWED_FILES = {
    "tools.py": _ULTRON_DIR / "tools.py",
    "tool_schemas.py": _ULTRON_DIR / "tool_schemas.py",
    "main.py": _ULTRON_DIR / "main.py",
    "persona.py": _ULTRON_DIR / "persona.py",
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

        marker = "# ══════════════════════════════════════════════════════════════════════\n#  TOOL REGISTRY"
        if marker not in tools_src:
            return _err("could not find TOOL_REGISTRY marker in tools.py")

        new_function = f"\n\n{code}\n\n"
        tools_src = tools_src.replace(marker, new_function + marker)

        reg_start = tools_src.rindex("\nTOOL_REGISTRY = {")
        depth = 1
        pos = reg_start + len("\nTOOL_REGISTRY = {")
        while depth > 0 and pos < len(tools_src):
            if tools_src[pos] == "{":
                depth += 1
            elif tools_src[pos] == "}":
                depth -= 1
            pos += 1
        reg_end = pos - 1

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
        indented = "\n".join("    " + line for line in schema_str.split("\n"))

        closing_bracket = schemas_src.rstrip().rindex("]")
        before_content = schemas_src[:closing_bracket].rstrip()
        separator = "" if before_content.endswith(",") else ","
        schemas_src = before_content + separator + "\n" + indented + ",\n]\n"
        schemas_path.write_text(schemas_src, encoding="utf-8")

        return _ok(
            message=f"tool '{name}' created — uvicorn reload will pick it up automatically",
            files_modified=["tools.py", "tool_schemas.py"],
        )

    except Exception as e:
        return _err(f"create_tool failed: {e}")


# ══════════════════════════════════════════════════════════════════════
#  11. MEMORY BANK — persistent JSON storage for cross-session recall
# ══════════════════════════════════════════════════════════════════════

MEMORY_FILE = _ULTRON_DIR / "ultron_memory.json"


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


def save_memory(args: dict) -> dict:
    """Save a memory with a tag for later recall."""
    content = args.get("content", "").strip()
    tag = args.get("tag", "general").strip().lower()
    if not content:
        return _err("content is required")

    from datetime import datetime
    memories = _load_memories()
    entry = {
        "id": f"mem_{int(time.time() * 1000)}",
        "content": content,
        "tag": tag,
        "timestamp": datetime.now().isoformat(),
    }
    memories.append(entry)
    _save_memories(memories)
    return _ok(message=f"memory saved under [{tag}]", total_memories=len(memories), entry=entry)


def recall_memories(args: dict) -> dict:
    """Search and retrieve memories, optionally filtered by tag or keyword."""
    tag = args.get("tag", "").strip().lower()
    query = args.get("query", "").strip().lower()
    limit = args.get("limit", 30)

    memories = _load_memories()
    if not memories:
        return _ok(memories=[], message="no memories stored yet")

    results = memories
    if tag:
        results = [m for m in results if m.get("tag") == tag]
    if query:
        results = [m for m in results if query in m.get("content", "").lower()]

    results = list(reversed(results))[:limit]
    return _ok(
        memories=[{"id": m.get("id", ""), "content": m["content"], "tag": m.get("tag", "general"), "when": m.get("timestamp", "")} for m in results],
        total=len(results),
    )


def forget_memory(args: dict) -> dict:
    """Delete memories by id, tag, or matching keyword."""
    mem_id = args.get("id", "").strip()
    tag = args.get("tag", "").strip().lower()
    query = args.get("query", "").strip().lower()

    if not mem_id and not tag and not query:
        return _err("provide an id, tag, or query to identify what to forget")

    memories = _load_memories()
    before = len(memories)

    if mem_id:
        memories = [m for m in memories if m.get("id") != mem_id]
    elif tag and query:
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
    "get_active_window": get_active_window,
    "system_stats": system_stats,
    "get_network_info": get_network_info,
    "execute_command": execute_command,
    "list_files": list_files,
    "search_files": search_files,
    "read_file": read_file,
    "write_file": write_file,
    "clipboard_read": clipboard_read,
    "clipboard_write": clipboard_write,
    "click_anywhere": click_anywhere,
    "type_text": type_text,
    "press_hotkey": press_hotkey,
    "take_screenshot": take_screenshot,
    "analyze_screen": analyze_screen,
    "media_control": media_control,
    "set_volume": set_volume,
    "open_url": open_url,
    "read_own_code": read_own_code,
    "create_tool": create_tool,
    "save_memory": save_memory,
    "recall_memories": recall_memories,
    "forget_memory": forget_memory,
}
