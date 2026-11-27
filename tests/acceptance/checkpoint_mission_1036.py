"""Independent task acceptance for original issue 1036, not a candidate patch.

Run in the existing secret-free networkless review container. The model may
not modify this test. Criteria were preregistered in issue 432 comment
7217110085 before the candidate was produced.
"""
import json
import tempfile
import unittest
from pathlib import Path

from plenum_ai.mission_checkpoint import (
    checkpoint_path, load_checkpoint, save_checkpoint, verified_previous_result,
    artifact_digest,
)

ISSUE = 1036
OBJECTIVE = "Checkpoint persistence integrity"
TEAM = ("research", "engineering")


class OriginalMission1036Acceptance(unittest.TestCase):
    def test_valid_roundtrip_and_invalid_writes_leave_no_disk_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "existing"
            artifact = root / "workers" / "research" / "evidence.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text('{"observed": 12.5}\n', encoding="utf-8")
            good = {"research": {"attempt": 1, "status": "DRAFT_READY_FOR_FOUNDER",
                    "verified": True, "artifact_path": "workers/research/evidence.json",
                    "sha256": artifact_digest(root, "workers/research/evidence.json"),
                    "worker": "research", "verified_scope": "original public result",
                    "actual_offline_functional_test_passed": True}}
            args = dict(issue=ISSUE, objective=OBJECTIVE, team=TEAM)
            save_checkpoint(root, **args, results=good)
            path = checkpoint_path(root, ISSUE)
            original = path.read_bytes()
            loaded = load_checkpoint(root, **args)
            self.assertEqual(loaded, good)
            restored = verified_previous_result(root, "research", loaded["research"])
            self.assertIsNotNone(restored)
            self.assertTrue(restored["_reused"])
            self.assertTrue(restored["actual_offline_functional_test_passed"])
            invalid = [None, [], "results", {"unassigned": {"attempt": 1}},
                       {"research": []}, {"research": {}},
                       *({"research": {"attempt": a}} for a in (True, False, 1.0, 0, 3, None)),
                       *({"research": {"attempt": 1, "nested": [v]}}
                         for v in (float("nan"), float("inf"), -float("inf")))]
            for index, results in enumerate(invalid):
                with self.subTest(index=index):
                    absent = Path(tmp) / ("absent-" + str(index))
                    with self.assertRaises((ValueError, TypeError)):
                        save_checkpoint(absent, **args, results=results)
                    self.assertFalse(absent.exists(), "Invalid save created a directory")
                    with self.assertRaises((ValueError, TypeError)):
                        save_checkpoint(root, **args, results=results)
                    self.assertEqual(path.read_bytes(), original)
                    self.assertEqual(load_checkpoint(root, **args), good)
                    self.assertEqual(list(root.glob("chief-checkpoint-*.tmp")), [])
            save_checkpoint(root, **args, results={"engineering": {"attempt": 2}})
            self.assertEqual(load_checkpoint(root, **args), {"engineering": {"attempt": 2}})

    def test_nonfinite_nested_json_is_rejected_on_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = dict(issue=ISSUE, objective=OBJECTIVE, team=TEAM)
            save_checkpoint(root, **args, results={"research": {"attempt": 1, "nested": [0.25]}})
            path = checkpoint_path(root, ISSUE)
            original = path.read_text(encoding="utf-8")
            self.assertEqual(load_checkpoint(root, **args)["research"]["nested"], [0.25])
            for representation in ("NaN", "Infinity", "-Infinity", "1e999", "-1e999"):
                with self.subTest(representation=representation):
                    raw = original.replace("0.25", representation)
                    self.assertNotEqual(raw, original)
                    path.write_text(raw, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_checkpoint(root, **args)
                    self.assertEqual(path.read_text(encoding="utf-8"), raw)
            path.write_text(original, encoding="utf-8")
            self.assertEqual(load_checkpoint(root, **args)["research"]["nested"], [0.25])


if __name__ == "__main__":
    unittest.main()
