import re
import json
import asyncio
from typing import Any, Dict, List, Union
from prompt_toolkit import prompt
from rich import print as rich_print
from file_manager import FileManager


class ActionResponseError(ValueError):
    """Raised when a model response does not match the action protocol."""


class ActionProcessor:
    """Handles parsing and execution of JSON action markers in AI responses."""
    def __init__(self, file_manager: FileManager):
        self.fm = file_manager

    @staticmethod
    def parse_response(response: str) -> Dict[str, Any]:
        clean_response = re.sub(
            r'<think>.*?</think>', '', response, flags=re.DOTALL
        ).strip()
        try:
            data = json.loads(clean_response)
        except json.JSONDecodeError as error:
            raise ActionResponseError(
                f"Model response is not valid JSON: {error.msg}."
            ) from error

        if not isinstance(data, dict):
            raise ActionResponseError("Model response must be a JSON object.")
        if not isinstance(data.get("message"), str):
            raise ActionResponseError('Response field "message" must be a string.')

        actions = data.get("actions")
        if not isinstance(actions, list):
            raise ActionResponseError('Response field "actions" must be a list.')

        required_fields = {
            "read": {"filename"},
            "write": {"filename", "content"},
            "patch": {"filename", "search", "replace"},
            "delete": {"filename"},
        }
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ActionResponseError(
                    f"Action {index + 1} must be a JSON object."
                )
            action_type = action.get("type")
            if not isinstance(action_type, str) or action_type not in required_fields:
                raise ActionResponseError(
                    f'Action {index + 1} has unsupported type "{action_type}".'
                )

            missing = required_fields[action_type] - action.keys()
            if missing:
                raise ActionResponseError(
                    f"Action {index + 1} ({action_type}) is missing required "
                    f"field(s): {', '.join(sorted(missing))}."
                )

            filename = action["filename"]
            if not isinstance(filename, str) or not filename.strip():
                raise ActionResponseError(
                    f"Action {index + 1} field \"filename\" must be a non-empty string."
                )

            for field in required_fields[action_type] - {"filename"}:
                value = action[field]
                if field in {"search", "replace"} and isinstance(value, list):
                    if not all(isinstance(line, str) for line in value):
                        raise ActionResponseError(
                            f"Action {index + 1} field \"{field}\" must be a "
                            "string or a list of strings."
                        )
                elif not isinstance(value, str):
                    raise ActionResponseError(
                        f"Action {index + 1} field \"{field}\" must be a string."
                    )

        return data

    async def process(self, response: str) -> List[Union[str, Dict]]:
        results = []
        data = self.parse_response(response)
        pending_actions = []

        for action in data["actions"]:
            action_type = action["type"]
            filename = action["filename"]
            if action_type == "read":
                try:
                    content = self.fm.read_file(filename)
                    rich_print(f"[green]> Read: {filename}[/green]")
                    results.append({
                        "type": "read_success",
                        "filename": filename,
                        "content": content,
                        "status": (
                            f"Successfully read {filename}. "
                            f"Content length: {len(content)} chars."
                        )
                    })
                except Exception as error:
                    rich_print(f"[red][ERROR] {error}[/red]")
                    results.append(f"Error reading {filename}: {error}")
            else:
                pending_actions.append(action)

        if pending_actions:
            rich_print(
                f"\n[yellow]PERMISSION REQUESTED for "
                f"{len(pending_actions)} actions:[/yellow]"
            )
            for action in pending_actions:
                rich_print(
                    f"  - {action['type'].capitalize()} targeting: "
                    f"{action['filename']}"
                )

            user_choice = await asyncio.to_thread(
                prompt, "Proceed with all actions? (y/n): "
            )
            if user_choice.lower().strip() in ["y", "yes"]:
                for action in pending_actions:
                    action_type = action["type"]
                    filename = action["filename"]
                    try:
                        if action_type == "write":
                            path = self.fm.write_file(filename, action["content"])
                            rich_print(
                                f"[green][SYSTEM] File configured: {path}[/green]"
                            )
                            results.append(f"Successfully wrote {filename}")
                        elif action_type == "patch":
                            search_val = action["search"]
                            replace_val = action["replace"]
                            if isinstance(search_val, list):
                                search_val = "\n".join(search_val)
                            if isinstance(replace_val, list):
                                replace_val = "\n".join(replace_val)

                            path = self.fm.patch_file(
                                filename, search_val, replace_val
                            )
                            rich_print(
                                f"[green][SYSTEM] File patched successfully: "
                                f"{path}[/green]"
                            )
                            results.append(f"Successfully patched {filename}")
                        elif action_type == "delete":
                            result = self.fm.delete_file(filename)
                            rich_print(f"[green][SYSTEM] {result}[/green]")
                            results.append(result)
                    except Exception as error:
                        rich_print(f"[red][ERROR] {error}[/red]")
                        results.append(
                            f"Error executing {action_type} on {filename}: {error}"
                        )
            else:
                results.append("Execution denied by user permission gate.")

        return results
