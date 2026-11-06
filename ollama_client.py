import logging
from typing import List, Dict, AsyncGenerator
import ollama

logger = logging.getLogger("Assistant")

class OllamaClient:
    """Handles real-time streaming communication with Ollama utilizing AsyncIO."""
    @staticmethod
    async def chat_stream(model: str, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """
        Sends a message to the specified Ollama model and streams the response back.
        
        Args:
            model: The name of the model to use (e.g., 'llama3').
            messages: A list of message dictionaries for the conversation history.
            
        Yields:
            Strings representing chunks of the generated content.
        """
        try:
            # Initialize the asynchronous client
            async_client = ollama.AsyncClient()
            # Initiate a streaming chat request
            response = await async_client.chat(
                model=model,
                messages=messages,
                stream=True,
                options={
                    "temperature": 0.3,
                    "top_p": 0.9
                    }
                )
            # Iterate through the streamed chunks and yield each content piece
            async for chunk in response:
                yield chunk["message"]["content"]
        except Exception as e:
            # Log the error and yield an error message to the UI
            logger.error(f"Ollama API Error: {e}")
            yield f"\n[API ERROR: {e}]\n"

    @staticmethod
    def get_stats(model: str):
        """
        Retrieves metadata and configuration details for a specific model.
        
        Args:
            model: The name of the model to inspect.
            
        Returns:
            A tuple containing (parameters, context_window) or error strings.
        """
        try:
            # Fetch model information from the Ollama server
            response = ollama.show(model=model)
            # Handle different return formats from the library
            if isinstance(response, dict):
                params = response.get('parameters', 'N/A')
                context = response.get('context_window', 'N/A')
            else:
                # If response is an object, access attributes directly
                params = getattr(response, 'parameters', 'N/A')
                context = getattr(response, 'context_window', 'N/A')
            return params, context
        except Exception as e:
            # Fallback to returning the error message if the call fails
            return str(e), str(e)
