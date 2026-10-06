"""
tool_schemas.py — OpenAI-format function definitions describing each tool
to the model. This is what gets sent as the `tools` array in the request
body to Spectrix's worker (which passes it straight through to OpenRouter).

Kept separate from tools.py deliberately: tools.py is "what a tool does",
this file is "how the model is told about it".
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Launch an application on the PC by its name or path (e.g. 'notepad', 'chrome', 'calc', 'code', 'spotify').",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Application executable name or full path to launch"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_installed_apps",
            "description": "List software and applications installed on the host computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max applications to return (default 60)"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_processes",
            "description": "List currently running processes on the PC, sorted by memory usage. Optionally filter by name substring.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Optional substring to filter process names by"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kill_process",
            "description": "Terminate a running process by its PID (preferred, safer) or by exact process name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pid": {"type": "integer", "description": "Process ID (PID) to kill"},
                    "name": {"type": "string", "description": "Exact process name to kill (used if pid not given)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_active_window",
            "description": "Get the title and process of the currently focused / active foreground window.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lock_screen",
            "description": "Immediately lock the host machine screen for security.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_stats",
            "description": "Get a real-time snapshot of system vitals: CPU usage, RAM usage, storage/disk partitions, battery status, and hostname.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_network_info",
            "description": "Get network interfaces, local IP address, gateway info, and internet connectivity status.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ping_diagnostics",
            "description": "Test ping latency (ms) to major global DNS servers (Cloudflare, Google) and evaluate internet response time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "targets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of IP addresses or domains to ping"
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_environment",
            "description": "Inspect host system environment variables (username, OS version, processor architecture, temp path).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell or PowerShell command on the host machine. Returns stdout, stderr, and exit code. Use for diagnostics, system queries, git, directory trees, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell/PowerShell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 20, max 60)"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the contents of a directory on the PC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list. Defaults to current directory."}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files recursively by filename keyword or wildcard glob pattern (e.g. '*.pdf', 'budget', '*.py').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword or glob pattern"},
                    "path": {"type": "string", "description": "Root directory to search in. Defaults to current directory."},
                    "limit": {"type": "integer", "description": "Max matching files to return (default 50)"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text contents of a file on the PC. Large files are truncated to safe bounds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file on the PC. Creates the file and parent directories if they don't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Text content to write"},
                    "append": {"type": "boolean", "description": "If true, append instead of overwrite. Defaults to false."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_info",
            "description": "Inspect metadata for a specific file or folder (size, timestamps, line count, permissions).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or folder path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file or directory permanently. Protected system files cannot be deleted.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to delete"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_or_rename_file",
            "description": "Move or rename a file or directory on disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"}
                },
                "required": ["source", "destination"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clipboard_read",
            "description": "Read the current text contents of the system clipboard.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clipboard_write",
            "description": "Write text to the system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Text to copy to clipboard"}
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_anywhere",
            "description": "Simulate a mouse click at screen coordinates (x, y) with left or right button.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate in pixels"},
                    "y": {"type": "integer", "description": "Y coordinate in pixels"},
                    "button": {"type": "string", "enum": ["left", "right"], "description": "Mouse button (default 'left')"},
                    "clicks": {"type": "integer", "description": "Number of clicks (1 for single, 2 for double click)"}
                },
                "required": ["x", "y"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Simulate typing text into the currently active window / focused input field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text string to type out"}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "press_hotkey",
            "description": "Simulate keyboard shortcut combinations (e.g. ['ctrl', 'c'], ['alt', 'tab'], ['win', 'd'], ['ctrl', 'shift', 'esc'], ['enter']).",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of key names in combination order (e.g. ['ctrl', 'v'])"
                    }
                },
                "required": ["keys"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Capture a desktop screenshot and save it locally.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_screen",
            "description": "Capture a screenshot and analyze what is currently visible on the screen. Returns the image to the multimodal model so you can SEE and describe the screen contents, read text, identify apps, windows, and UI elements.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "media_control",
            "description": "Control media playback on the PC: play/pause, skip track, or adjust volume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play_pause", "next", "prev", "volume_up", "volume_down", "mute"],
                        "description": "The media action to perform",
                    }
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Set master system volume to a specific percentage (0 to 100) or toggle mute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Master volume percentage level from 0 to 100"},
                    "mute": {"type": "boolean", "description": "If true, mute system audio"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notification_popup",
            "description": "Trigger a native desktop notification toast banner on the user's screen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Notification title"},
                    "message": {"type": "string", "description": "Notification body message"}
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to open"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live web using DuckDuckGo to obtain current facts, documentation, news, or technical answers. Returns top titles, links, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "limit": {"type": "integer", "description": "Max search results to return (default 5)"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_content",
            "description": "Fetch and extract readable clean text/content from any public webpage URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The webpage URL to fetch and read"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_own_code",
            "description": "Read one of your own source files to understand your current implementation. Allowed files: tools.py, tool_schemas.py, main.py, persona.py.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "enum": ["tools.py", "tool_schemas.py", "main.py", "persona.py"],
                        "description": "Which source file to read",
                    }
                },
                "required": ["file"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_tool",
            "description": "Create a brand new tool for yourself by writing a Python function and registering it. The function must follow the pattern: takes a dict arg, returns a dict with 'ok' key. Use _ok(**kwargs) and _err(msg) helpers. After creation, uvicorn auto-reloads and the tool becomes available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Snake_case function name for the new tool"},
                    "code": {"type": "string", "description": "Complete Python function source code. Must define a function with the same name as 'name' that takes (args: dict) and returns a dict."},
                    "description": {"type": "string", "description": "Human-readable description of what the tool does (shown to the model)"},
                    "parameters": {
                        "type": "object",
                        "description": "OpenAI-format parameters schema: {type: 'object', properties: {...}, required: [...]}",
                    },
                },
                "required": ["name", "code", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save a piece of information to persistent memory. Use this to remember facts about the user, preferences, past tasks, or anything worth recalling later. Memories survive across sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember",
                    },
                    "tag": {
                        "type": "string",
                        "description": "Category tag for organization (e.g. 'preference', 'fact', 'task', 'person', 'project'). Defaults to 'general'.",
                    },
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memories",
            "description": "Search and retrieve stored memories. Can filter by tag, keyword, or both. Returns most recent memories first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Filter by tag (e.g. 'preference', 'fact'). Leave empty for all tags.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Keyword to search in memory content. Leave empty for no keyword filter.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max memories to return (default 30).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forget_memory",
            "description": "Delete memories by id, tag, or keyword. Use when information is outdated or when requested.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Specific memory ID to delete"},
                    "tag": {"type": "string", "description": "Delete all memories with this tag."},
                    "query": {"type": "string", "description": "Delete memories containing this keyword."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_missions",
            "description": "List all active tactical missions, directives, and goals from the mission deck.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                        "description": "Filter by mission status (optional)"
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_mission",
            "description": "Create a new mission, directive, or tactical task in the mission deck.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Mission title or description"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "normal", "high", "urgent"],
                        "description": "Mission priority level"
                    }
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_mission",
            "description": "Update the status of a mission (e.g. mark as 'completed' or 'in_progress').",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Mission ID to update"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                        "description": "New status for the mission"
                    },
                    "title": {"type": "string", "description": "Updated mission title (optional)"}
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_mission",
            "description": "Purge or delete a mission from the mission deck by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Mission ID to delete"}
                },
                "required": ["id"],
            },
        },
    },
]
