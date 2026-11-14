# AI-ntilipsi

A terminal-based AI assistant with local filesystem integration and model switching.

## Features
- **File Interaction**: Read, write, patch, and delete files using a secure sandbox.
- **Model Switching**: Easily switch between different models (fast, default, strong).
- **Context Awareness**: Maintains conversation history and respects token limits.
- **Action Processing**: Parses structured JSON responses to perform file operations.

## Commands
- `/stats` - Show model parameters
- `/clear` - Clear conversation history
- `/help` - List available commands
- `/default` | `/fast` | `/strong` - Switch models
- `/exit` - Terminate session
- `/model <name>` - Set custom model
- `/pure` - Disable system prompt
- `/diff` - Toggle full patch diff output
- `/self` - Inject active workspace context
- `@filename` - Attach file context
- `/ls_dir` - List directory contents

## Usage
```bash
python main.py --model <model_name>
```