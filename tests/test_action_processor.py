import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

from action_processor import ActionProcessor, ActionResponseError
from file_manager import FileManager
from rich.syntax import Syntax


class ActionResponseValidationTests(unittest.TestCase):
    def setUp(self):
        self.file_manager = Mock()
        self.processor = ActionProcessor(self.file_manager)

    def test_valid_response_without_actions_returns_no_results(self):
        results = asyncio.run(
            self.processor.process('{"message":"Done","actions":[]}')
        )

        self.assertEqual(results, [])
        self.file_manager.read_file.assert_not_called()

    def test_invalid_action_batch_is_rejected_before_any_action_runs(self):
        response = (
            '{"message":"Read and write","actions":['
            '{"type":"read","filename":"notes.txt"},'
            '{"type":"write","filename":"copy.txt"}]}'
        )

        with self.assertRaisesRegex(ActionResponseError, "missing required"):
            asyncio.run(self.processor.process(response))

        self.file_manager.read_file.assert_not_called()

    def test_unsupported_and_malformed_action_types_are_rejected(self):
        for action in [
            {"type": "execute", "filename": "script.py"},
            {"type": ["read"], "filename": "notes.txt"},
            {"type": "read", "filename": ""},
        ]:
            with self.subTest(action=action):
                response = json.dumps({"message": "Test", "actions": [action]})
                with self.assertRaises(ActionResponseError):
                    self.processor.parse_response(response)

    def test_invalid_response_envelope_is_rejected(self):
        for response in [
            "not JSON",
            '{"message":"Missing actions"}',
            '{"message":12,"actions":[]}',
            '{"message":"Bad actions","actions":{}}',
        ]:
            with self.subTest(response=response):
                with self.assertRaises(ActionResponseError):
                    self.processor.parse_response(response)

    def test_patch_diff_option_displays_the_full_unified_diff(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_manager = FileManager()
            file_manager.base_dir = Path(temp_dir)
            filename = str(Path(temp_dir) / "notes.txt")
            Path(filename).write_text("before\n", encoding="utf-8")
            processor = ActionProcessor(file_manager)
            processor.show_patch_diff = True
            response = json.dumps({
                "message": "Updating the file.",
                "actions": [{
                    "type": "patch",
                    "filename": filename,
                    "search": "before",
                    "replace": "after",
                }],
            })

            with patch("action_processor.prompt", return_value="yes"), \
                    patch("action_processor.rich_print") as display:
                results = asyncio.run(processor.process(response))

            self.assertEqual(results, [f"Successfully patched {filename}"])
            diff = next(
                item.code for (item,), _kwargs in display.call_args_list
                if isinstance(item, Syntax)
            )
            self.assertIn(f"--- a/{filename}", diff)
            self.assertIn("-before", diff)
            self.assertIn("+after", diff)


if __name__ == "__main__":
    unittest.main()
