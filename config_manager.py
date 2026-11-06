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
