import tempfile
import unittest
from pathlib import Path

from file_manager import FileManager


class PatchFileTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_manager = FileManager()
        self.file_manager.base_dir = Path(self.temp_dir.name)
        self.filename = str(self.file_manager.base_dir / "example.py")

    def write_source(self, content):
        Path(self.filename).write_text(content, encoding="utf-8")

    def test_patch_matches_when_indentation_differs(self):
        self.write_source("def greet():\n        return 'hello'\n")

        self.file_manager.patch_file(
            self.filename,
            "def greet():\n    return 'hello'\n",
            "def greet():\n    return 'hi'\n",
        )

        self.assertEqual(
            Path(self.filename).read_text(encoding="utf-8"),
            "def greet():\n    return 'hi'\n",
        )

    def test_patch_rejects_ambiguous_whitespace_insensitive_match(self):
        original = "def greet():\n    return 'hello'\n\n" \
                   "def greet():\n        return 'hello'\n"
        self.write_source(original)

        with self.assertRaisesRegex(ValueError, "matched multiple locations"):
            self.file_manager.patch_file(
                self.filename,
                "def greet():\n  return 'hello'\n",
                "def greet():\n    return 'hi'\n",
            )

        self.assertEqual(Path(self.filename).read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
