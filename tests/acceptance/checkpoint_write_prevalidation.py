"""Prospective independent acceptance: invalid checkpoint IDs cannot create directories."""
from pathlib import Path
import tempfile
import unittest
from plenum_ai import mission_checkpoint as checkpoint

class CheckpointWritePrevalidationAcceptance(unittest.TestCase):
    def test_invalid_identifiers_leave_nonexistent_root_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            for index, issue in enumerate((True, False, 1.0, "42", 0, -1, 1000000000)):
                root = Path(tmp) / str(index) / "checkpoints"
                with self.subTest(issue=issue):
                    with self.assertRaises(ValueError):
                        checkpoint.save_checkpoint(root, issue=issue, objective="Public task",
                                                   team=("program",), results={})
                    self.assertFalse(root.parent.exists())

    def test_valid_identifier_creates_checkpoint_and_preserves_readback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "new" / "checkpoints"
            args = dict(issue=42, objective="Public task", team=("program",))
            result = {"program":{"attempt":1,"verified":False}}
            checkpoint.save_checkpoint(root, **args, results=result)
            self.assertEqual(checkpoint.load_checkpoint(root, **args), result)
            updated = {"program":{"attempt":2,"verified":False}}
            checkpoint.save_checkpoint(root, **args, results=updated)
            self.assertEqual(checkpoint.load_checkpoint(root, **args), updated)
            self.assertEqual(list(root.iterdir()), [checkpoint.checkpoint_path(root, 42)])
