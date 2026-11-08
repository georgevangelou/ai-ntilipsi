import asyncio
import unittest
from unittest.mock import patch

from ollama_client import OllamaClient, OllamaClientError


class OllamaClientErrorTests(unittest.TestCase):
    def test_api_error_is_raised_instead_of_returned_as_an_empty_action_response(self):
        async def collect_chunks():
            return [
                chunk async for chunk in OllamaClient.chat_stream("model", [])
            ]

        with patch(
            "ollama_client.ollama.AsyncClient",
            side_effect=RuntimeError("server unavailable"),
        ):
            with self.assertRaisesRegex(
                OllamaClientError, "Ollama API request failed: server unavailable"
            ):
                asyncio.run(collect_chunks())


if __name__ == "__main__":
    unittest.main()
