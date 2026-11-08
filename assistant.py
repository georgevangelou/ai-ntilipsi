#!/usr/bin/env python3

import re
import asyncio
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich import print as rich_print
from rich import table
from rich.panel import Panel

# Local component imports
from config_manager import CONFIG, FAST_MODEL, DEFAULT_MODEL, STRONG_MODEL, TOKEN_LIMIT, logger
from file_manager import FileManager
from chat_history import ChatHistory
from ollama_client import OllamaClient, OllamaClientError
from action_processor import ActionProcessor, ActionResponseError
from autocomplete import UnifiedCompleter
from config_manager import SYSTEM_PROMPT
from typing import Tuple

NONE = "NONE"
BREAK = "BREAK"
CONTINUE = "CONTINUE"
MAX_AGENT_ITERATIONS = 10

class Assistant:
    """High-level Orchestrator for the AI Agent."""

    def __init__(self, model: str):
        self.model = model
        self.history = ChatHistory(TOKEN_LIMIT)
        self.file_manager = FileManager()
        self.action_processor = ActionProcessor(self.file_manager)
        self.history.add_message("system", SYSTEM_PROMPT)
        
        self.attach_pattern = re.compile(r'@([a-zA-Z0-9_\-\.\/]+)')
        
        self.commands = ['/stats', '/clear', '/help', '/default', '/fast', '/strong', '/ls_dir', '/self', '/exit', '/model', '/pure']
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
                self.history.add_context(
                    f"=== ATTACHED FILE CONTEXT [{file_path_str}] ===\n{content}\n=======================================",
                    defer_until_next_user=True,
                )
                rich_print(f"[green]Attached context from: {file_path_str}[/green]")
            except Exception as e:
                rich_print(f"[red]Error linking {file_path_str}: {e}[/red]")

    def is_option_in_command(self, prompt: str, option: str):
        # Check if option exists in prompt
        normalized_prompt = prompt.lower()
        normalized_option = option.lower()
        if not (
            normalized_prompt == normalized_option
            or (normalized_option + ' ') in normalized_prompt
            or normalized_prompt.endswith(normalized_option)
        ):
            return False, prompt
        
        # Remove the option from prompt
        if normalized_prompt == normalized_option:
            remaining = ''
        elif (normalized_option + ' ') in normalized_prompt:
            index = normalized_prompt.index(normalized_option + ' ')
            remaining = prompt[:index] + prompt[index + len(option) + 1:]
        else:
            remaining = prompt[:-len(option)]
        
        return True, remaining


    def handle_commands(self, cmd: str, user_input: str) -> Tuple[str, bool]:
        to_return = NONE

        if cmd == "/exit":
            return BREAK, True
        
        is_pure, cmd = self.is_option_in_command(cmd, "/pure")
        attach_system_prompt = not is_pure
        if is_pure:
            rich_print("[dim]No system context will be attached to this prompt.[/dim]")
            if cmd == '':
                rich_print("[yellow]No user prompt added.[/yellow]")
                to_return = CONTINUE

        elif cmd == "/stats":
            params, ctx = OllamaClient.get_stats(self.model)
            tokens_used = self.history.get_token_count()
            t = table.Table(
                title="Model Statistics",
                box=None,
                border_style="blue"
            )
            t.add_column("Category", style="bold")
            t.add_column("Value", style="cyan")
            t.add_row("Model Name", self.model)
            t.add_row("Parameters", params)
            t.add_row("Token Window Limit", ctx)
            t.add_row("Imposed Token Limit", str(TOKEN_LIMIT))
            t.add_row("Tokens Currently Used", str(tokens_used))
            rich_print(t)
            to_return = CONTINUE
        
        elif self.is_option_in_command(cmd, "/clear")[0]:
            self.history.clear()
            rich_print("[dim]Context reset to base configuration environment parameters.[/dim]")
            to_return = CONTINUE

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
            to_return = CONTINUE

        elif cmd in ["/default", "/fast", "/strong"]:
            if cmd == "/fast":
                self.model = FAST_MODEL
            elif cmd == "/strong":
                self.model = STRONG_MODEL
            else:
                self.model = DEFAULT_MODEL
            rich_print(f"[green]Active runtime model targets updated: {self.model}[/green]")
            to_return = CONTINUE

        elif cmd.startswith("/model"):
            parts = user_input.split()
            if len(parts) > 1:
                self.model = parts[1]
                rich_print(f"Switched model pointer: {self.model}")
            to_return = CONTINUE

        elif cmd == "/ls_dir":
            file_list = self.file_manager.list_files()
            content = str(file_list)
            self.history.add_context(
                f"=== GOT FILE LIST FROM CURRENT DIRECTORY ===\n{content}\n=======================================",
                defer_until_next_user=True,
            )
            rich_print(f"[green]Read file list from current directory.[/green]")
            for f in file_list: 
                rich_print(f"  - [cyan]{f}[/cyan]")
            to_return = CONTINUE

        elif cmd == "/self":
            try:
                content = Path(__file__).read_text(encoding="utf-8")
                self.history.add_context(
                    f"=== ATTACHED FILE CONTEXT [self] ===\n{content}\n=======================================",
                    defer_until_next_user=True,
                )
                rich_print(f"[green]Bound orchestration layer source successfully.[/green]")
            except Exception as e:
                rich_print(f"[red]Error parsing runtime package: {e}[/red]")
            to_return = CONTINUE

        return to_return, attach_system_prompt

    async def run_agent_request(self, attach_system_prompt: bool) -> str:
        """Continue model turns and return the request outcome."""
        for _ in range(MAX_AGENT_ITERATIONS):
            rich_print(f"\n[cyan]AI:[/cyan] ", end="", flush=True)
            rich_print("[dim] Thinking...[/dim]")

            full_response = ""
            try:
                async for chunk in OllamaClient.chat_stream(
                    self.model, self.history.get_history(attach_system_prompt)
                ):
                    response, is_thinking = chunk
                    if not is_thinking:
                        full_response += response
                        if "content" in response:
                            rich_print("[dim]Writing content...[/]", end=" ", flush=True)
                        elif "actions" in response:
                            rich_print("[dim]Writing actions...[/]", end=" ", flush=True)
                        elif "message" in response:
                            rich_print("[dim]> Writing message...[/]", end=" ", flush=True)
            except OllamaClientError as error:
                print()
                rich_print(f"[red]{error} The request did not complete.[/red]")
                return "failed"

            print()
            self.history.add_message("assistant", full_response)
            try:
                parsed_response = self.action_processor.parse_response(full_response)
            except ActionResponseError as error:
                rich_print(f"[red]Invalid model response: {error}[/red]")
                return "failed"

            conversation_text = parsed_response["message"]
            if conversation_text:
                rich_print(conversation_text)
            else:
                rich_print(full_response)

            print()
            action_results = await self.action_processor.process(full_response)
            if not action_results:
                return "completed"

            summary_items = []
            for result in action_results:
                if isinstance(result, dict) and result.get("type") == "read_success":
                    self.history.add_context(
                        f"=== AUTO-READ FILE CONTENT [{result['filename']}] ===\n"
                        f"{result['content']}\n======================================="
                    )
                    summary_items.append(f"- {result['status']}")
                else:
                    summary_items.append(f"- {result}")

            summary = "\n".join(summary_items)
            self.history.add_context(
                f"=== TOOL EXECUTION ENVIRONMENT STATUS UPDATE ===\n{summary}"
            )
            if any("Execution denied by user permission gate." in str(result)
                   for result in action_results):
                return "denied"
        else:
            rich_print(
                f"[yellow]Stopped after {MAX_AGENT_ITERATIONS} model iterations. "
                "The request may be incomplete.[/yellow]"
            )
            return "iteration_limit"
    
    async def run_async(self):
        """Asynchronous execution core loop."""
        rich_print(Panel(f"Connected to Ollama Backend Layer\nModel: {self.model}\nToken Window Limit: {self.history.limit}", 
                         title="System Initialization Active", subtitle="Type /help for options", border_style="blue"))
        rich_print("[dim] Hint: Use [bold]Alt+Enter[/bold] or [bold]Esc+Enter[/bold] to write multi-line text snippets; press [bold]Enter[/bold] to submit.[/dim]")
        
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

                action, attach_system_prompt = self.handle_commands(cmd, user_input)
                if action == BREAK:
                    break
                elif action == CONTINUE:
                    continue
                
                self.handle_attachment_logic(user_input)
                clean_input = self.attach_pattern.sub('', user_input).strip()
                if not attach_system_prompt:
                    _, clean_input = self.is_option_in_command(clean_input, "/pure")
                    clean_input = clean_input.strip()
                if not clean_input: continue

                self.history.add_message("user", clean_input)
                await self.run_agent_request(attach_system_prompt)

            except (EOFError, KeyboardInterrupt):
                rich_print("\n[yellow]Shutdown intercept caught. Graceful exit initiated.[/yellow]")
                break
            except Exception as e:
                logger.exception("Runtime Exception")
                rich_print(f"[red]Fatal Runtime Exception: {e}[/red]")
