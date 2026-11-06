#!/usr/bin/env python3

import argparse
import re
import asyncio
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich import print as rich_print
from rich.panel import Panel

# Local component imports
from config_manager import CONFIG, FAST_MODEL, DEFAULT_MODEL, STRONG_MODEL, TOKEN_LIMIT, logger
from file_manager import FileManager
from chat_history import ChatHistory
from ollama_client import OllamaClient
from action_processor import ActionProcessor
from autocomplete import UnifiedCompleter

class Assistant:
    """High-level Orchestrator for the AI Agent."""
    SYSTEM_PROMPT = (
        "You are a Professional Software Engineering Agent with implicit access to the local filesystem via tools. "
        "Your primary goal is to assist in clean coding, precise refactoring, and debugging.\n\n"
        "**CLI Display Rules:**\n"
        "- Write your conversational text in raw, pure text format. Do NOT use markdown (such as bold asterisks or hashes), as it is unsupported and unreadable in the CLI interface.\n\n"
        "**Core Capabilities:**\n"
        "1. File Creation & Modification: Create or modify sandboxed project files.\n"
        "2. File Reading: Read file contents into active history context.\n"
        "3. File Deletion: Erase files from the sandboxed environment.\n"
        "4. Context Awareness: Scan directory structure hierarchies.\n\n"
        "**Workspace & Attachment Constraints:**\n"
        "- Files matched with '@filename' notation are already fully loaded into your conversation history window matrix. Do NOT issue a 'read' action block for them.\n"
        "- You operate within a strict sandbox. Never reference paths outside the current runtime project directory layout.\n\n"
        "**Tool Usage & Operational Protocols:**\n"
        "You MUST interact with files by emitting a single, structured JSON block. Example:\n"
        "{\n"
        "  \"actions\": [\n"
        "    { \"type\": \"patch\", \"filename\": \"app.py\", \"search\": \"old_line\", \"replace\": \"new_line\" }\n"
        "  ]\n"
        "}\n\n"
        "Supported Action Configurations:\n"
        "- \"write\": { \"type\": \"write\", \"filename\": \"...\", \"content\": \"...\" }\n"
        "- \"patch\": { \"type\": \"patch\", \"filename\": \"...\", \"search\": \"...\", \"replace\": \"...\" }\n"
        "- \"read\": { \"type\": \"read\", \"filename\": \"...\" }\n"
        "- \"delete\": { \"type\": \"delete\", \"filename\": \"...\" }\n\n"
        "**Strict Engineering Rules (Anti-Truncation Guardrails):**\n"
        "1. Never mix 'patch' and 'write' actions targeting the same filename in a single turn. Choose one strategy.\n"
        "2. Prefer 'patch' over 'write' for all updates changing less than 60% of an existing file to avoid stream trunction.\n"
        "3. When using 'write', placeholders like '# rest of code here' are strictly forbidden. You must emit the full content.\n"
        "4. When using 'patch', the 'search' block must be unique, contiguous, and captured exactly verbatim from the source file. "
        "Include enough surrounding context lines (2-3 lines above and below) to establish clear indentation and uniqueness."
    )

    def __init__(self, model: str):
        self.model = model
        self.history = ChatHistory(TOKEN_LIMIT)
        self.file_manager = FileManager()
        self.action_processor = ActionProcessor(self.file_manager)
        self.history.add_message("system", self.SYSTEM_PROMPT)
        
        self.attach_pattern = re.compile(r'@([a-zA-Z0-9_\-\.\/]+)')
        
        self.commands = ['/stats', '/clear', '/help', '/default', '/fast', '/strong', '/ls_dir', '/self', '/exit', '/model']
        self.completer = UnifiedCompleter(self.commands, self.file_manager)
        
        self.kb = KeyBindings()
        @self.kb.add('escape', 'enter')
        def _(event):
            event.current_buffer.insert_text('\n')

        @self.kb.add('enter')
        def _(event):
            event.current_buffer.validate_and_handle()

    def handle_attachment_logic(self, user_input: str):
        """Processes file attachments identified by the @ symbol notation."""
        matches = self.attach_pattern.findall(user_input)
        for file_path_str in matches:
            try:
                content = self.file_manager.read_file(file_path_str)
                self.history.add_message("user", f"=== ATTACHED FILE CONTEXT [{file_path_str}] ===\n{content}\n=======================================")
                rich_print(f"[green]Attached context from: {file_path_str}[/green]")
            except Exception as e:
                rich_print(f"[red]Error linking {file_path_str}: {e}[/red]")

    async def run_async(self):
        """Asynchronous execution core loop."""
        rich_print(Panel(f"Connected to Ollama Backend Layer\nModel: {self.model}\nToken Window Limit: {self.history.limit}", 
                         title="System Initialization Active", subtitle="Type /help for options", border_style="blue"))
        rich_print("[dim]💡 Hint: Use [bold]Alt+Enter[/bold] or [bold]Esc+Enter[/bold] to write multi-line text snippets; press [bold]Enter[/bold] to submit.[/dim]")
        
        while True:
            try:
                user_input = await asyncio.to_thread(
                    prompt,
                    f"\nUser > ", 
                    history=FileHistory(CONFIG['settings']['history_file']),
                    completer=self.completer,
                    key_bindings=self.kb,
                    multiline=True
                )
                if not user_input.strip(): continue
                
                cmd = user_input.lower().strip()
                if cmd == "/exit": break
                elif cmd == "/stats":
                    params, ctx = OllamaClient.get_stats(self.model)
                    rich_print(f"Model: {self.model}\nParams: {params}\nContext Limit: {ctx}")
                    continue
                elif cmd == "/clear":
                    self.history.clear()
                    rich_print("[yellow]Context reset to base configuration environment parameters.[/yellow]")
                    continue
                elif cmd == "/help":
                    rich_print("""
[yellow]--- Core Terminal Directory Control Matrix ---[/yellow]
- /stats            Inspect base parameter constraints
- /clear            Wipe dynamic runtime memory array
- /default          Switch to default structural mapping
- /fast             Switch to swift execution layout
- /strong           Switch to deep inference layout
- /ls_dir           List all target contents recursively
- /self             Inject active orchestration workspace context
- @filename         Bind target resource context array
- Alt+Enter         Insert newline for multi-line copy/pasting
                    """)
                    continue
                elif cmd in ["/default", "/fast", "/strong"]:
                    if cmd == "/fast":
                        self.model = FAST_MODEL
                    elif cmd == "/strong":
                        self.model = STRONG_MODEL
                    else:
                        self.model = DEFAULT_MODEL
                    rich_print(f"Active runtime model targets updated: {self.model}")
                    continue
                elif cmd.startswith("/model"):
                    parts = user_input.split()
                    if len(parts) > 1:
                        self.model = parts[1]
                        rich_print(f"Switched model pointer: {self.model}")
                    continue
                elif cmd == "/ls_dir":
                    file_list = self.file_manager.list_files()
                    content = file_list
                    self.history.add_message("user", f"=== GOT FILE LIST FROM CURRENT DIRECTORY ===\n{content}\n=======================================" )
                    rich_print(f"[green]Read file list from current directory.[/green]")
                    for f in file_list: 
                        rich_print(f"  - [cyan]{f}[/cyan]")
                    continue
                elif cmd == "/self":
                    try:
                        content = Path(__file__).read_text(encoding="utf-8")
                        self.history.add_message("user", f"=== ATTACHED FILE CONTEXT [self] ===\n{content}\n=======================================" )
                        rich_print(f"[green]Bound orchestration layer source successfully.[/green]")
                    except Exception as e:
                        rich_print(f"[red]Error parsing runtime package: {e}[/red]")
                    continue
                
                self.handle_attachment_logic(user_input)
                clean_input = self.attach_pattern.sub('', user_input).strip()
                if not clean_input: continue

                self.history.add_message("user", clean_input)
                rich_print(f"\n[cyan]AI:[/cyan] ", end="", flush=True)

                full_response = ""
                async for chunk in OllamaClient.chat_stream(self.model, self.history.get_history()):
                    print(chunk, end="", flush=True)
                    full_response += chunk
                print()
                print() 

                self.history.add_message("assistant", full_response)
                
                action_results = await self.action_processor.process(full_response)
                if action_results:
                    summary = "\n".join([f"- {res}" for res in action_results])
                    self.history.add_message("system", f"=== TOOL EXECUTION ENVIRONMENT STATUS UPDATE ===\n{summary}")

            except (EOFError, KeyboardInterrupt):
                rich_print("\n[yellow]Shutdown intercept caught. Graceful exit initiated.[/yellow]")
                break
            except Exception as e:
                logger.exception("Runtime Exception")
                rich_print(f"[red]Fatal Runtime Exception: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="Hardened Local Orchestration Environment Client.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Target processing model")
    args = parser.parse_args()

    asyncio.run(Assistant(args.model).run_async())

if __name__ == "__main__":
    main()
