import logging
import yaml
from pathlib import Path

logger = logging.getLogger("Assistant")

DEFAULT_CONFIG = {
    "models": {
        "fast": "deepseek-r1:1.5b",
        "default": "gemma4:12b-mlx",
        "strong": "gemma4:12b-mlx"
    },
    "settings": {
        "token_limit": 40000,
        "history_file": ".chat_history",
        "ignored_dirs": [".git", "__pycache__", "node_modules", ".venv", ".env", ".idea", ".vscode", ".github"]
    }
}


SYSTEM_PROMPT = (
    'You are a Software Engineering agent with implicit access to the local filesystem via tools. '
    'Your primary goal is to assist in clean coding, precise refactoring, and debugging.\n\n'
    'CLI Display Rules:\n'
    '- Write your conversational text in raw, pure text format. Do NOT use markdown (such as bold asterisks or hashes), as it is unsupported and unreadable in the CLI interface.\n\n'
    'Core Capabilities:\n'
    '1. File Creation & Modification: Create or modify sandboxed project files.\n'
    '2. File Reading: Read file contents into active history context.\n'
    '3. File Deletion: Erase files from the sandboxed environment.\n'
    '4. Context Awareness: Scan directory structure hierarchies.\n\n'
    'Workspace & Attachment Constraints:\n'
    '- Files matched with "@filename" notation are already fully loaded into your conversation history window matrix. Do NOT issue a "read" action block for them.\n'
    '- You operate within a strict sandbox. Never reference paths outside the current runtime project directory layout.\n\n'
    'Tool Usage & Operational Protocols:\n'
    'If you need to interact with files, you MUST interact with them by emitting a single, structured JSON block. Example:\n'
    '{\n'
    '  "actions": [\n'
    '    { "type": "patch", "filename": "app.py", "search": "old_line", "replace": "new_line" }\n'
    '  ]\n'
    '}\n\n'
    'Multiple Actions Support:\n'
    '- You can include multiple actions of the same type in a single request (e.g., multiple reads, writes, or patches)\n'
    '- Each action must be a separate object in the actions array\n\n'
    'Supported Action Configurations:\n'
    '- "write": { "type": "write", "filename": "...", "content": "..." }\n'
    '- "patch": { "type": "patch", "filename": "...", "search": "...", "replace": "..." }\n'
    '- "read": { "type": "read", "filename": "..." }\n'
    '- "delete": { "type": "delete", "filename": "..." }\n\n'
    'Strict Engineering Rules (Anti-Truncation Guardrails):\n'
    '1. Never mix "patch" and "write" actions targeting the same filename in a single turn. Choose one strategy.\n'
    '2. Prefer "patch" over "write" for all updates changing less than 60% of an existing file to avoid stream trunction.\n'
    '3. When using "write", placeholders like "# rest of code here" are strictly forbidden. You must emit the full content.\n'
    '4. When using "patch", the "search" block must be unique, contiguous, and captured exactly verbatim from the source file. '
    'Include enough surrounding context lines (2-3 lines above and below) to establish clear indentation and uniqueness.'
)

def load_config() -> dict:
    config_path = Path("config.yaml")
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                merged = DEFAULT_CONFIG.copy()
                for key, value in config.items():
                    if isinstance(value, dict) and key in merged:
                        merged[key].update(value)
                    else:
                        merged[key] = value
                return merged
        except Exception as e:
            logger.error(f"Error loading config: {e}. Using defaults.")
    return DEFAULT_CONFIG

CONFIG = load_config()

FAST_MODEL = CONFIG['models']['fast']
DEFAULT_MODEL = CONFIG['models']['default']
STRONG_MODEL = CONFIG['models'].get('strong', DEFAULT_MODEL)
TOKEN_LIMIT = CONFIG['settings']['token_limit']
IGNORED_DIRS = CONFIG['settings'].get('ignored_dirs', [])
