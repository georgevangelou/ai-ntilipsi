
from typing import List, Optional


class ResponsePhaseTracker:
    """Tracks which response field is currently being streamed from JSON."""

    def __init__(self):
        self.phase: Optional[str] = None
        self._in_string = False
        self._escaped = False
        self._string_buffer: Optional[List[str]] = []
        self._pending_key: Optional[str] = None
        self._awaiting_colon = False

    def feed(self, text: str) -> Optional[str]:
        for character in text:
            if self._in_string:
                if self._escaped:
                    self._escaped = False
                    if self._string_buffer is not None:
                        if len(self._string_buffer) < 8:
                            self._string_buffer.append(character)
                        else:
                            self._string_buffer = None
                elif character == "\\":
                    self._escaped = True
                elif character == '"':
                    self._in_string = False
                    self._pending_key = (
                        "".join(self._string_buffer)
                        if self._string_buffer is not None
                        else None
                    )
                    self._awaiting_colon = True
                elif self._string_buffer is not None:
                    if len(self._string_buffer) < 8:
                        self._string_buffer.append(character)
                    else:
                        self._string_buffer = None
                continue

            if self._awaiting_colon:
                if character.isspace():
                    continue
                if character == ":":
                    if self._pending_key == "message":
                        self.phase = "message"
                    elif self._pending_key in {
                        "actions", "type", "filename", "search", "replace"
                    }:
                        self.phase = "actions"
                    elif self._pending_key == "content":
                        self.phase = "content"
                self._awaiting_colon = False
                self._pending_key = None

            if character == '"':
                self._in_string = True
                self._string_buffer = []

        return self.phase
