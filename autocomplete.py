from typing import List
from prompt_toolkit.completion import Completer, Completion
from file_manager import FileManager

class UnifiedCompleter(Completer):
    """Handles unified auto-completion for slash commands and dynamically fetches file completions when typing '@'."""
    def __init__(self, commands: List[str], file_manager: FileManager):
        self.commands = commands
        self.file_manager = file_manager

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Check if user is trying to type a system slash command
        if text.startswith('/'):
            for cmd in self.commands:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
            return

        # Handle context file auto-completion when typing @
        word_before_cursor = document.get_word_before_cursor()
        
        # We trigger if the word starts with '@' or if the character immediately preceding the word is '@'
        if text.endswith('@') or (word_before_cursor and text[:-len(word_before_cursor)].endswith('@')):
            # Strip out the leading '@' symbol if present to search through directory files matches
            search_term = word_before_cursor.lstrip('@')
            try:
                files = self.file_manager.list_files()
                for f in files:
                    # Provide matches prefix-aware or fully if empty query tracking
                    if not search_term or f.lower().startswith(search_term.lower()):
                        # Retain start coordinate placement calculations properly
                        # Include '@' prefix in completion text to preserve it when selected via up/down arrows
                        if word_before_cursor.startswith("@"):
                            completion_text = "@" + f
                        else:
                            completion_text = f
                        yield Completion(completion_text, start_position=-len(word_before_cursor))
            except Exception:
                pass
