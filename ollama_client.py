import logging
from typing import List, Dict, AsyncGenerator, Tuple
import ollama

logger = logging.getLogger("Assistant")

class OllamaClient:
    """Handles real-time streaming communication with Ollama utilizing AsyncIO."""
    @staticmethod
    async def chat_stream(model: str, messages: List[Dict]) -> AsyncGenerator[Tuple[str, bool], None]:
        """
        Sends a message to the specified Ollama model and streams the response back,
        strictly enforcing a valid JSON output structure.
        """
        try:
            # Initialize the asynchronous client
            async_client = ollama.AsyncClient()
            # Initiate a streaming chat request
            options = {
                "temperature": 0.3,  # Lower temperature lowers syntax variance
                "top_p": 0.9
            }
            response = await async_client.chat(
                model=model,
                messages=messages,
                stream=True,
                options=options,
                format='json',  # Enforces strict JSON response syntax from Ollama
                think=True
            )
            # Iterate through the streamed chunks and yield each piece safely
            async for chunk in response:
                if hasattr(chunk, 'message'):
                    # 1. First, check if the model is currently outputting a thought process
                    if getattr(chunk.message, 'thinking', None):
                        yield chunk.message.thinking, True
                    
                    # 2. Next, check if it's outputting the actual final answer content
                    if chunk.message.content:
                        yield chunk.message.content, False

        except Exception as e:
            # Log the error and yield an error message to the UI
            logger.error(f"Ollama API Error: {e}")
            yield f'\n{{"message": "API Error: {e}", "actions": []}}\n', False

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
