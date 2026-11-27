"""Independent public checkpoint path identity contract, fixed before candidate execution."""
import tempfile
import unittest
from pathlib import Path

from plenum_ai import mission_checkpoint as checkpoint


class CheckpointPathIdentityAcceptance(unittest.TestCase):
    def test_invalid_issue_values_are_rejected_before_path_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for issue in (True, False, 1.0, "1", "../outside", "x/../../outside",
                          None, [], {}, 0, -1, 1000000000, 10**30):
                with self.subTest(issue=issue):
                    with self.assertRaises(ValueError):
                        checkpoint.checkpoint_path(root, issue)
            self.assertEqual(list(root.iterdir()), [])

    def test_valid_boundary_paths_and_roundtrip_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for issue in (1, 42, 999999999):
                expected = root / f"chief-checkpoint-{issue}.json"
                self.assertEqual(checkpoint.checkpoint_path(root, issue), expected)
                checkpoint.save_checkpoint(root, issue=issue, objective="Public mission",
                    team=("program",), results={"program": {"attempt": 1}})
                self.assertTrue(expected.is_file())
                self.assertEqual(checkpoint.load_checkpoint(root, issue=issue,
                    objective="Public mission", team=("program",)), {"program": {"attempt": 1}})
