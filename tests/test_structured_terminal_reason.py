"""Safe terminal reason diagnostics for original structured inference."""
import json
import subprocess
import unittest
from unittest.mock import patch
from plenum_ai import openhands_coding_agent as coder


class StructuredTerminalReason(unittest.TestCase):
    def test_terminal_reason_is_bounded_and_never_retried_or_consumed(self):
        scope = (b"", b"def example():\n    return 1\n", b"")
        good = {"done": True, "done_reason": "stop", "model": coder.STRUCTURED_EDIT_MODEL,
                "message": {"content": "untrusted incomplete content"}}
        for fields, reason in (
            ({"done_reason": "length"}, "TOKEN_LIMIT"),
            ({"done": False}, "NOT_DONE"),
            ({"model": "unexpected"}, "WRONG_MODEL"),
            ({"done_reason": "untrusted provider text"}, "OTHER_STOP_REASON"),
        ):
            with self.subTest(reason=reason), patch.object(
                coder.subprocess, "run", return_value=subprocess.CompletedProcess(
                    [], 0, stdout=json.dumps({**good, **fields}).encode())) as run:
                with self.assertRaises(coder.StructuredEditFailure) as caught:
                    coder.structured_local_edit("Repair function example. Preserve behavior.", scope)
                self.assertEqual(caught.exception.stage, "INCOMPLETE_MODEL_RESPONSE")
                self.assertEqual(caught.exception.terminal_reason, reason)
                self.assertEqual(run.call_count, 1)
                self.assertNotIn("untrusted", str(caught.exception))

    def test_unknown_reason_never_persisted(self):
        self.assertIsNone(coder.StructuredEditFailure("TRANSPORT", terminal_reason="untrusted").terminal_reason)
