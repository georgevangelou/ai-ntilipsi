# AI-ntilipsi

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

The assistant feeds action results back to the model and continues the same request for up to 10 model iterations, stopping when no actions are returned or an action is denied. Invalid model/action responses and Ollama request failures are reported as incomplete requests. Actions are validated as a batch before any of them run.

Conversation messages, model responses, and action calls are saved as JSON in `chat.history`. The file is overwritten when a new assistant session starts and updated as the conversation progresses. Use `/diff` to toggle full unified-diff output for patch actions; it is disabled by default.

### `file_manager.py`
Secure sandboxed file operations. Lists files, reads/writes/patches/deletes with path validation against ignored directories.

### `chat_history.py`
Token-aware conversation management. Tracks messages with configurable token limits and system prompt handling.

### `autocomplete.py`
Provides slash command completion and file path auto-completion via @ syntax.

## Usage
```
python main.py --model <model_name>
```

## Commands
- `/stats` - Show model parameters
- `/clear` - Clear conversation history
- `/help` - List available commands
- `/default` | `/fast` | `/strong` - Switch models
- `/exit` - Terminate interactive session gracefully
- `/model <name>` - Set custom model name dynamically
- `/pure` - Disable system prompt attachment
- `/diff` - Toggle full patch diff output
- `/self` - Inject active orchestration workspace context
- `@filename` - Attach file context
- `/ls_dir` - List directory contents
- `/math sqrt <number>` - Calculate square root of a number
