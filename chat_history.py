from typing import List, Dict

class ChatHistory:
    """Manages conversation history and context windowing with efficient token calculation."""
    def __init__(self, token_limit: int):
        self.history: List[Dict] = []
        self.limit = token_limit
        self._current_tokens = 0

    def count_tokens(self, text: str) -> int:
        """Optimized token estimation using bitwise shifts instead of division."""
        if not text:
            return 0
        return len(text.split()) + (len(text) >> 2)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if role != "system":
            self._current_tokens += self.count_tokens(content)
        self._trim_history()

    def _trim_history(self):
        system_messages = [m for m in self.history if m["role"] == "system"]
        chat_messages = [m for m in self.history if m["role"] != "system"]
        
        while self._current_tokens > self.limit and chat_messages:
            removed_msg = chat_messages.pop(0)
            self._current_tokens -= self.count_tokens(removed_msg["content"])
            
        self.history = system_messages + chat_messages

    def get_history(self, attach_system_prompt=True) -> List[Dict]:
        if attach_system_prompt:
            return self.history
        else:
            return self.history[1:]

    def clear(self):
        self.history = [m for m in self.history if m["role"] == "system"]
        self._current_tokens = 0
