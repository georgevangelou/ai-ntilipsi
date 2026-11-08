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
        "token_limit": 100000,
        "history_file": ".chat_history",
        "ignored_dirs": [".git", "__pycache__", "node_modules", ".venv", ".env", ".idea", ".vscode", ".github"]
    }
}

SYSTEM_PROMPT = (
    'You are a Software Engineering agent with implicit access to the local filesystem via tools.\n'
    'CRITICAL: You must ALWAYS respond with a single, valid JSON object following this exact schema:\n'
    '{\n'
    '  "message": "Your pure conversational chat or explanation text here (No markdown format symbols like asterisks or hashes)",\n'
    '  "actions": [\n'
    '    { "type": "read", "filename": "example.py" }\n'
    '  ]\n'
    '}\n\n'
    'If no tool actions are required, fill the "actions" array as empty: [].\n'
    'Ensure all string fields escape newlines correctly as \\n.\n\n'
    'Core Tool Capabilities inside the "actions" array:\n'
    '- "write": { "type": "write", "filename": "...", "content": "..." }\n'
    '- "patch": { "type": "patch", "filename": "...", "search": "...", "replace": "..." }\n'
    '- "read": { "type": "read", "filename": "..." }\n'
    '- "delete": { "type": "delete", "filename": "..." }\n\n'
    'Rules:\n'
    '1. Files matched with "@filename" notation are already fully loaded already. Do NOT issue a "read" action block for them.\n'
    '2. Prefer "patch" over "write" for updates changing less than 60% of an existing file.\n'
    '3. When using "write", placeholders like "# rest of code" are forbidden. Emit the entire code contents.\n'
    '4. For "patch", copy "search" verbatim from the current file and include enough surrounding lines to identify a unique block.'
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
