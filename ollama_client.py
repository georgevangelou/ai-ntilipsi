import logging
from typing import List, Dict, AsyncGenerator
import ollama

logger = logging.getLogger("Assistant")

class OllamaClient:
    """Handles real-time streaming communication with Ollama utilizing AsyncIO."""
    @staticmethod
    async def chat_stream(model: str, messages: List[Dict]) -> AsyncGenerator[str, None]:
        try:
            async_client = ollama.AsyncClient()
            response = await async_client.chat(model=model, messages=messages, stream=True)
            async for chunk in response:
                yield chunk["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama API Error: {e}")
            yield f"\n[API ERROR: {e}]\n"

    @staticmethod
    def get_stats(model: str):
        try:
            response = ollama.show(model=model)
            if isinstance(response, dict):
                params = response.get('parameters', 'N/A')
                context = response.get('context_window', 'N/A')
            else:
                params = getattr(response, 'parameters', 'N/A')
                context = getattr(response, 'context_window', 'N/A')
            return params, context
        except Exception as e:
            return str(e), str(e)
