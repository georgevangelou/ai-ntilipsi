from typing import Dict, List, Optional

class ChatHistory:
    """Manages chronological conversation history and context windowing."""
    def __init__(self, token_limit: int):
        self.history: List[Dict] = []
        self.limit = token_limit
        self._current_tokens = 0
        self._system_prompt: Optional[Dict] = None
        self._pending_context: List[str] = []

    def count_tokens(self, text: str) -> int:
        """Estimate token usage for context-window management."""
        if not text:
            return 0
        return len(text.split()) + (len(text) >> 2)

    def add_message(self, role: str, content: str):
        if role == "user" and self._pending_context:
            content = "\n\n".join([*self._pending_context, content])
            self._pending_context.clear()

        message = {"role": role, "content": content}
        if role == "system" and self._system_prompt is None:
            self._system_prompt = message

        self.history.append(message)
        if message is not self._system_prompt:
            self._current_tokens += self.count_tokens(content)
        self._trim_history()

    def add_context(self, content: str, defer_until_next_user: bool = False):
        """Add context for the next user message or as an in-turn system message."""
        if defer_until_next_user:
            self._pending_context.append(content)
        else:
            self.add_message("system", content)

    def _trim_history(self):
        while self._current_tokens > self.limit:
            user_indices = [
                index for index, message in enumerate(self.history)
                if message["role"] == "user"
            ]
            if len(user_indices) < 2:
                break

            # Remove the oldest complete turn, including any tool context it produced.
            start, end = user_indices[0], user_indices[1]
            removed_messages = self.history[start:end]
            self._current_tokens -= sum(
                self.count_tokens(message["content"])
                for message in removed_messages
                if message is not self._system_prompt
            )
            del self.history[start:end]

    def get_history(self, attach_system_prompt=True) -> List[Dict]:
        if attach_system_prompt:
            return self.history
        return [
            message for message in self.history
            if message is not self._system_prompt
        ]

    def get_token_count(self) -> int:
        return self._current_tokens

    def clear(self):
        self.history = [self._system_prompt] if self._system_prompt is not None else []
        self._current_tokens = 0
        self._pending_context.clear()
