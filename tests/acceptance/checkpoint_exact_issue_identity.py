"""Untrusted checkpoint identity must be an exact integer, not a coercible JSON value."""
import json
import tempfile
import unittest
from pathlib import Path

from plenum_ai import mission_checkpoint as checkpoint


class ExactCheckpointIssueAcceptance(unittest.TestCase):
    def test_reject_noninteger_identity_and_preserve_valid_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for issue, invalid in ((1, True), (42, 42.0), (42, "42"), (42, 43)):
                checkpoint.save_checkpoint(root, issue=issue, objective="Public task",
                                           team=("program",), results={"program": {"attempt": 1}})
                path = checkpoint.checkpoint_path(root, issue)
                data = json.loads(path.read_text())
                self.assertEqual(checkpoint.load_checkpoint(root, issue=issue,
                                 objective="Public task", team=("program",)), data["results"])
                data["issue_number"] = invalid
                path.write_text(json.dumps(data))
                with self.subTest(issue=issue, invalid=invalid):
                    with self.assertRaises(ValueError):
                        checkpoint.load_checkpoint(root, issue=issue,
                            objective="Public task", team=("program",))

    def test_missing_checkpoint_and_wrong_scope_still_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(checkpoint.load_checkpoint(root, issue=42,
                             objective="Public task", team=("program",)), {})
            checkpoint.save_checkpoint(root, issue=42, objective="Public task",
                                       team=("program",), results={})
            with self.assertRaises(ValueError):
                checkpoint.load_checkpoint(root, issue=42, objective="Different task",
                                           team=("program",))
