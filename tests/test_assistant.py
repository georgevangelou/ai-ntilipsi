import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from assistant import Assistant
from ollama_client import OllamaClientError


class AgentIterationTests(unittest.TestCase):
    def setUp(self):
        self.assistant = Assistant("test-model")
        self.assistant.history.add_message("user", "Read a file and summarize it.")

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


if __name__ == "__main__":
    unittest.main()
