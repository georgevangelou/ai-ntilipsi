import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from assistant import Assistant
from ollama_client import OllamaClientError


class AgentIterationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.history_log_path = Path(self.temp_dir.name) / "chat.history"
        self.history_log_path.write_text("stale session", encoding="utf-8")
        with patch("assistant.Path.cwd", return_value=Path(self.temp_dir.name)):
            self.assistant = Assistant("test-model")
        self.assistant.history.add_message("user", "Read a file and summarize it.")
        self.assistant._save_history()

    def test_history_log_is_overwritten_for_each_new_session(self):
        self.history_log_path.write_text("stale session", encoding="utf-8")
        with patch("assistant.Path.cwd", return_value=Path(self.temp_dir.name)):
            Assistant("test-model")
        messages = json.loads(self.history_log_path.read_text(encoding="utf-8"))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "system")

        self.assistant.history.add_message(
            "assistant",
            '{"message":"Reading it.","actions":[{"type":"read","filename":"x.txt"}]}',
        )
        self.assistant._save_history()
        messages = json.loads(self.history_log_path.read_text(encoding="utf-8"))
        self.assertEqual([message["role"] for message in messages],
                         ["system", "user", "assistant"])
        self.assertIn('"type":"read"', messages[-1]["content"])

    def test_diff_command_toggles_patch_diff_output(self):
        with patch("assistant.rich_print"):
            result, _ = self.assistant.handle_commands("/diff", "/diff")
            self.assertEqual(result, "CONTINUE")
            self.assertTrue(self.assistant.action_processor.show_patch_diff)

            self.assistant.handle_commands("/diff", "/diff")
            self.assertFalse(self.assistant.action_processor.show_patch_diff)

    def test_action_results_are_sent_to_a_follow_up_model_turn(self):
        responses = [
            '{"message":"I will read the file.","actions":[{"type":"read","filename":"notes.txt"}]}',
            '{"message":"I will duplicate the content.","actions":[{"type":"write","filename":"copy.txt","content":"hello"}]}',
            '{"message":"The file was copied and summarized.","actions":[]}',
        ]
        model_inputs = []

        def chat_stream(model, messages):
            model_inputs.append((model, list(messages)))

            async def chunks():
                yield responses[len(model_inputs) - 1], False

            return chunks()

        self.assistant.action_processor.process = AsyncMock(side_effect=[
            [{
                "type": "read_success",
                "filename": "notes.txt",
                "content": "hello",
                "status": "Successfully read notes.txt. Content length: 5 chars.",
            }],
            ["Successfully wrote copy.txt"],
            [],
        ])

        with patch("assistant.OllamaClient.chat_stream", side_effect=chat_stream), \
                patch("assistant.rich_print"), patch("builtins.print"):
            status = asyncio.run(
                self.assistant.run_agent_request(attach_system_prompt=True)
            )

        self.assertEqual(status, "completed")
        self.assertEqual(len(model_inputs), 3)
        self.assertIn("hello", "\n".join(
            message["content"] for message in model_inputs[1][1]
        ))
        self.assertIn("Successfully wrote copy.txt", "\n".join(
            message["content"] for message in model_inputs[2][1]
        ))
        self.assertEqual(self.assistant.action_processor.process.await_count, 3)
        logged_messages = json.loads(
            self.history_log_path.read_text(encoding="utf-8")
        )
        self.assertEqual(
            [message["role"] for message in logged_messages].count("assistant"), 3
        )
        self.assertIn('"type":"read"', "\n".join(
            message["content"] for message in logged_messages
            if message["role"] == "assistant"
        ))

    def test_action_without_results_still_gets_a_follow_up_model_turn(self):
        responses = [
            '{"message":"I will read the file.","actions":[{"type":"read","filename":"notes.txt"}]}',
            '{"message":"The request is complete.","actions":[]}',
        ]
        model_inputs = []

        def chat_stream(model, messages):
            model_inputs.append((model, list(messages)))

            async def chunks():
                yield responses[len(model_inputs) - 1], False

            return chunks()

        self.assistant.action_processor.process = AsyncMock(side_effect=[[], []])

        with patch("assistant.OllamaClient.chat_stream", side_effect=chat_stream), \
                patch("assistant.rich_print"), patch("builtins.print"), \
                patch("assistant.logger.warning") as warning_log:
            status = asyncio.run(
                self.assistant.run_agent_request(attach_system_prompt=True)
            )

        self.assertEqual(status, "completed")
        self.assertEqual(len(model_inputs), 2)
        warning_log.assert_called_once_with(
            "No results were returned for requested action(s): read."
        )
        self.assertIn(
            "No results were returned for requested action(s): read.",
            "\n".join(message["content"] for message in model_inputs[1][1]),
        )

    def test_permission_denial_stops_follow_up_turns(self):
        self.assistant.action_processor.process = AsyncMock(return_value=[
            "Execution denied by user permission gate."
        ])

        async def chat_stream(model, messages):
            self.assertEqual(model, "test-model")
            self.assertTrue(messages)
            yield (
                '{"message":"May I write this file?",'
                '"actions":[{"type":"write","filename":"out.txt","content":"ok"}]}',
                False,
            )

        with patch("assistant.OllamaClient.chat_stream", side_effect=chat_stream) as stream, \
                patch("assistant.rich_print"), patch("builtins.print"):
            status = asyncio.run(
                self.assistant.run_agent_request(attach_system_prompt=True)
            )

        self.assertEqual(status, "denied")
        stream.assert_called_once()

    def test_invalid_model_response_is_not_reported_as_completion(self):
        async def chat_stream(model, messages):
            del model, messages
            yield '{"message":"Invalid","actions":[{"type":"unknown"}]}', False

        with patch("assistant.OllamaClient.chat_stream", side_effect=chat_stream), \
                patch("assistant.rich_print"), patch("builtins.print"), \
                patch.object(self.assistant.action_processor, "process", new_callable=AsyncMock) as process:
            status = asyncio.run(
                self.assistant.run_agent_request(attach_system_prompt=True)
            )

        self.assertEqual(status, "failed")
        process.assert_not_awaited()

    def test_model_api_failure_is_not_reported_as_completion(self):
        async def chat_stream(model, messages):
            del model, messages

            async def fail_request():
                raise OllamaClientError("Ollama API request failed: offline")

            yield await fail_request(), False

        with patch("assistant.OllamaClient.chat_stream", side_effect=chat_stream), \
                patch("assistant.rich_print"), patch("builtins.print"), \
                patch.object(self.assistant.action_processor, "process", new_callable=AsyncMock) as process:
            status = asyncio.run(
                self.assistant.run_agent_request(attach_system_prompt=True)
            )

        self.assertEqual(status, "failed")
        process.assert_not_awaited()

    def test_stream_status_reports_thinking_and_response_progress(self):
        async def chat_stream(model, messages):
            del model, messages
            yield "considering the attached code", True
            yield '{"message":"Done.","actions":[]}', False

        self.assistant.action_processor.process = AsyncMock(return_value=[])
        status_display = MagicMock()

        with patch("assistant.OllamaClient.chat_stream", side_effect=chat_stream), \
                patch("assistant.rich_print"), patch("builtins.print"), \
                patch("assistant.Status") as status:
            status.return_value.__enter__.return_value = status_display
            result = asyncio.run(
                self.assistant.run_agent_request(attach_system_prompt=True)
            )

        self.assertEqual(result, "completed")
        status_display.update.assert_any_call(
            "[dim]Thinking (29 characters)...[/dim]"
        )
        status_display.update.assert_any_call("[dim]Generating response...[/dim]")


if __name__ == "__main__":
    unittest.main()
