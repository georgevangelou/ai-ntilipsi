import os
from pathlib import Path
from typing import List
from config_manager import IGNORED_DIRS

class FileManager:
    """Handles all filesystem operations with robust sandbox security and optimization."""
    def __init__(self):
        self.base_dir = Path.cwd().resolve()
        self._ignored_set = set(IGNORED_DIRS)

    def _is_safe_path(self, path: Path) -> bool:
        """Strict sandbox check using commonpath extraction."""
        try:
            target_path = Path(os.path.abspath(path)).resolve()
            return os.path.commonpath([str(self.base_dir), str(target_path)]) == str(self.base_dir)
        except Exception:
            return False

    def list_files(self, max_depth: int = 3) -> List[str]:
        """Efficiently lists files while skipping ignored directories."""
        files = []
        
        for root, dirs, file_names in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if d not in self._ignored_set and not d.startswith('.')]
            
            rel_root = os.path.relpath(root, self.base_dir)
            if rel_root == ".":
                depth = 0
            else:
                depth = rel_root.count(os.sep) + 1
            
            if depth > max_depth:
                continue
                
            for f in file_names:
                if not f.startswith('.'):
                    if rel_root == ".":
                        files.append(f)
                    else:
                        files.append(os.path.join(rel_root, f).replace(os.sep, '/'))
        return files

    def read_file(self, filename: str) -> str:
        """Reads content from a file safely inside the sandbox constraint boundaries."""
        full_path = Path(os.path.abspath(os.path.expanduser(filename)))

        if not self._is_safe_path(full_path):
            raise PermissionError(f"Access denied: {filename} points outside the sandbox boundary.")
        
        if not full_path.is_file():
            raise FileNotFoundError(f"File not found: {filename}")

        return full_path.read_text(encoding='utf-8')

    def write_file(self, filename: str, content: str) -> str:
        """Writes content to a file, enforcing sandbox parameters."""
        full_path = Path(os.path.abspath(os.path.expanduser(filename)))

        if not self._is_safe_path(full_path):
            raise PermissionError(f"Access denied: {filename} points outside the sandbox boundary.")

        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        return str(full_path)

    def patch_file(self, filename: str, search_text: str, replace_text: str) -> str:
        """Replaces a specific block of text within a file with robust matching."""
        full_content = self.read_file(filename)
        search_block = search_text.strip()
        
        variants = [
            search_block,
            "\n".join([line.rstrip() for line in search_block.splitlines()]),
            search_block.rstrip()
        ]

        for block in variants:
            if block and block in full_content:
                new_content = full_content.replace(block, replace_text, 1)
                return self.write_file(filename, new_content)
        
        raise ValueError(f"Could not find exact block match inside {filename}.\nSearch block attempted (variants): {variants}")

    def delete_file(self, filename: str) -> str:
        """Deleted a file within the sandbox."""
        full_path = Path(os.path.abspath(os.path.expanduser(filename)))
        if not self._is_safe_path(full_path):
            raise PermissionError(f"Access denied: {filename} points outside the sandbox.")
        
        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            return f"Deleted {filename}"
        else:
            raise FileNotFoundError(f"File not found: {filename}")
