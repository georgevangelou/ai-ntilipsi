import asyncio
import json
import unittest
from unittest.mock import Mock

from action_processor import ActionProcessor, ActionResponseError


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


if __name__ == "__main__":
    unittest.main()
