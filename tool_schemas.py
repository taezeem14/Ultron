"""
tool_schemas.py — OpenAI-format function definitions describing each tool
to the model. This is what gets sent as the `tools` array in the request
body to Spectrix's worker (which passes it straight through to OpenRouter).

Kept separate from tools.py deliberately: tools.py is "what a tool does",
this file is "how the model is told about it". Different concerns, and
schemas will churn more often (adding params, tightening descriptions)
than the implementations will.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Launch an application on the PC by its name (e.g. 'notepad', 'chrome', 'code').",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Application name or path to launch"}
                },
                "required": ["name"],
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
                    "pid": {"type": "integer", "description": "Process ID to kill"},
                    "name": {"type": "string", "description": "Exact process name to kill (used if pid not given)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "system_stats",
            "description": "Get a snapshot of current system vitals: CPU usage, RAM usage, disk usage, and battery status.",
            "parameters": {"type": "object", "properties": {}, "required": []},
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
            "name": "read_file",
            "description": "Read the text contents of a file on the PC. Large files are truncated.",
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
            "name": "clipboard_read",
            "description": "Read the current contents of the system clipboard.",
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
            "name": "take_screenshot",
            "description": "Capture a screenshot of the current screen and save it locally.",
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
            "name": "analyze_screen",
            "description": "Capture a screenshot and analyze what is currently visible on the screen. Returns the image to the multimodal model so you can SEE and describe the screen contents, read text, identify apps, windows, and UI elements.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_own_code",
            "description": "Read one of your own source files to understand your current implementation. Allowed files: tools.py, tool_schemas.py, main.py.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "enum": ["tools.py", "tool_schemas.py", "main.py"],
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
            "name": "click_anywhere",
            "description": "Click at the specified (x, y) screen coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X coordinate"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate"
                    }
                },
                "required": [
                    "x",
                    "y"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save a piece of information to persistent memory. Use this to remember facts about the user, preferences, past conversations, or anything worth recalling later. Memories survive across sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The information to remember (e.g. 'User prefers dark mode', 'Taezeem's project is called Ultron')",
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
            "description": "Search and retrieve stored memories. Can filter by tag, keyword, or both. Returns most recent memories first. Use this at the start of conversations or when the user references something you should remember.",
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
                        "description": "Max memories to return (default 20).",
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
            "description": "Delete memories by tag or keyword. Use when the user asks you to forget something or when information is outdated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Delete all memories with this tag.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Delete memories containing this keyword.",
                    },
                },
                "required": [],
            },
        },
    },
]
