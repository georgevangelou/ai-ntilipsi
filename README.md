# Local AI Agent System

## Overview
A terminal-based AI assistant with local filesystem integration, model switching, and code execution capabilities.

## Core Components

### `main.py`
Main orchestrator. Runs interactive terminal interface with model switching, file attachments, and action processing.

### `config_manager.py`
Manages configuration via YAML files. Defines default models (fast, default, strong) and token limits.

### `ollama_client.py`
Streams responses from Ollama API with async support. Handles temperature tuning and error handling.

### `action_processor.py`
Parses JSON actions from AI responses. Executes read/write/patch/delete operations with user permission checks.

### `file_manager.py`
Secure sandboxed file operations. Lists files, reads/writes/patches/deletes with path validation against ignored directories.

### `chat_history.py`
Token-aware conversation management. Tracks messages with configurable token limits and system prompt handling.

### `autocomplete.py`
Provides slash command completion and file path auto-completion via @ syntax.

## Usage
```bash
python main.py --model <model_name>
```

## Commands
- `/stats` - Show model parameters
- `/clear` - Clear conversation history
- `/help` - List available commands
- `/default` | `/fast` | `/strong` - Switch models
- `@filename` - Attach file context
- `/ls_dir` - List directory contents