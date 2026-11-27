"""Independent prospective checkpoint parser acceptance; no network or model."""
import json
from pathlib import Path
import tempfile
import unittest
from plenum_ai import mission_checkpoint as checkpoint

class CheckpointDuplicateKeysAcceptance(unittest.TestCase):
    def test_valid_checkpoint_and_duplicate_keys_at_any_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = dict(issue=42, objective="Public task", team=("program",))
            results = {"program":{"attempt":1,"verified":False}}
            checkpoint.save_checkpoint(root, **args, results=results)
            path = checkpoint.checkpoint_path(root, 42)
            raw = path.read_text()
            self.assertEqual(checkpoint.load_checkpoint(root, **args), results)
            for changed in (
                raw.replace('"issue_number": 42', '"issue_number": 7, "issue_number": 42'),
                raw.replace('"attempt": 1', '"attempt": 2, "attempt": 1'),
                raw.replace('"verified": false', '"verified": true, "verified": false'),
                raw.replace('"attempt": 1', '"\\u0061ttempt": 2, "attempt": 1'),
                raw.replace('"attempt": 1', '"attempt": 1, "attempt": 1'),
            ):
                self.assertNotEqual(changed, raw)
                path.write_text(changed)
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    checkpoint.load_checkpoint(root, **args)
            path.write_text(raw)
            self.assertEqual(checkpoint.load_checkpoint(root, **args), results)
