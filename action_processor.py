import re
import json
import asyncio
from pathlib import Path
from typing import List, Union, Dict
from prompt_toolkit import prompt
from rich import print as rich_print
from rich.console import Console
from rich.syntax import Syntax
from file_manager import FileManager

console = Console()

class ActionProcessor:
    """Handles parsing and execution of JSON action markers in AI responses."""
    def __init__(self, file_manager: FileManager):
        self.fm = file_manager

    async def process(self, response: str) -> List[Union[str, Dict]]:
        results = []
        
        # Clean reasoning tags out if present
        clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Find the true outermost boundaries of the JSON structure
        start_idx = clean_response.find('{')
        end_idx = clean_response.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            return results

        json_str = clean_response[start_idx:end_idx + 1].strip()
        try:
            data = json.loads(json_str)
            if "actions" in data:
                pending_actions = []
                for action in data["actions"]:
                    if action.get("content"):
                        rich_print(f"\n[bold blue]Action Transaction Detected:[/bold blue]")
                        content = action["content"]
                        syntax = Syntax(content, "python", theme="monokai", line_numbers=True)
                        console.print(syntax)
                                                                                                                                                                                                                                                                                                                                                                 
                    action_type = action.get("type")
                    filename = action.get("filename")
                    
                    if action_type == "read":
                        try:
                            content = self.fm.read_file(filename)
                            rich_print(f"\n[green]--- Reading {filename} ---[/green]")
                            ext = Path(filename).suffix.lstrip('.') or 'txt'
                            syntax = Syntax(content, ext, theme="monokai", line_numbers=True, word_wrap=True)
                            console.print(syntax)
                            
                            results.append({
                                "type": "read_success",
                                "filename": filename,
                                "content": content,
                                "status": f"Successfully read {filename}. Content length: {len(content)} chars."
                            })
                        except Exception as e:
                            rich_print(f"[red][ERROR] {e}[/red]")
                            results.append(f"Error reading {filename}: {e}")
                    elif action_type in ["write", "patch", "delete"]:
                        pending_actions.append(action)
                
                if pending_actions:
                    rich_print(f"\n[yellow]PERMISSION REQUESTED for {len(pending_actions)} actions:[/yellow]")
                    for action in pending_actions:
                        action_type = action.get("type")
                        filename = action.get("filename")
                        rich_print(f"  - {action_type.capitalize()} targeting: {filename}")
                    
                    user_choice = await asyncio.to_thread(prompt, "Proceed with all actions? (y/n): ")
                    if user_choice.lower().strip() in ['y', 'yes']:
                        for action in pending_actions:
                            action_type = action.get("type")
                            filename = action.get("filename")
                            try:
                                if action_type == "write":
                                    path = self.fm.write_file(filename, action.get("content", ""))
                                    rich_print(f"[green][SYSTEM] File configured: {path}[/green]")
                                    results.append(f"Successfully wrote {filename}")
                                elif action_type == "patch":
                                    search_val = action.get("search", "")
                                    replace_val = action.get("replace", "")
                                    if isinstance(search_val, list): search_val = "\n".join(search_val)
                                    if isinstance(replace_val, list): replace_val = "\n".join(replace_val)
                                    
                                    path = self.fm.patch_file(filename, search_val, replace_val)
                                    rich_print(f"[green][SYSTEM] File patched successfully: {path}[/green]")
                                    results.append(f"Successfully patched {filename}")
                                elif action_type == "delete":
                                    result = self.fm.delete_file(filename)
                                    rich_print(f"[green][SYSTEM] {result}[/green]")
                                    results.append(result)
                            except Exception as e:
                                rich_print(f"[red][ERROR] {e}[/red]")
                                results.append(f"Error executing {action_type} on {filename}: {e}")
                    else:
                        results.append("Execution denied by user permission gate.")
        except Exception as e:
            rich_print(f"[red][SYSTEM ERROR] Failed to parse Action JSON payload: {e}[/red]")
            results.append(f"System failed to parse action JSON block due to structural formatting anomaly: {e}")

        return results
