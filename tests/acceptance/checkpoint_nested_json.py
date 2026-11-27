"""Frozen prospective acceptance for excessively nested checkpoint JSON."""
from pathlib import Path
import tempfile
import unittest
from plenum_ai import mission_checkpoint as checkpoint


class CheckpointNestedJSONAcceptance(unittest.TestCase):
    def test_excessively_nested_checkpoint_is_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = checkpoint.checkpoint_path(root, 42)
            raw = b'{"x":' * 15000 + b'0' + b'}' * 15000
            self.assertLess(len(raw), 200000)
            path.write_bytes(raw)
            with self.assertRaises(ValueError):
                checkpoint.load_checkpoint(root, issue=42, objective="Public task", team=("program",))

    def test_valid_checkpoint_still_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = dict(issue=42, objective="Public task", team=("program",))
            result = {"program": {"attempt": 1, "verified": False, "details": {"value": [1, 2]}}}
            checkpoint.save_checkpoint(root, **args, results=result)
            self.assertEqual(checkpoint.load_checkpoint(root, **args), result)
