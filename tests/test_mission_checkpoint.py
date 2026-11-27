"""Recovery must reject unsafe worker artifacts without exhausting the runner."""
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from plenum_ai import mission_checkpoint as checkpoint
from acceptance.checkpoint_scope_attempt import CheckpointQualification
from acceptance.checkpoint_tree_invariants import CheckpointTreeAcceptance
from acceptance.checkpoint_exact_issue_identity import ExactCheckpointIssueAcceptance
from acceptance.checkpoint_path_identity import CheckpointPathIdentityAcceptance
from acceptance.checkpoint_duplicate_keys import CheckpointDuplicateKeysAcceptance


class MissionCheckpointLimitsTests(TestCase):
    def test_oversized_artifact_rejected_before_file_open(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "workers/program/output.bin"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"12345")
            with patch.object(checkpoint, "MAX_BYTES", 4), patch.object(
                Path, "open", side_effect=AssertionError("oversized artifact was opened")
            ):
                self.assertIsNone(checkpoint.artifact_digest(root, "workers/program/output.bin"))

    def test_unreadable_artifact_is_rejected_instead_of_aborting_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "workers/program/output.txt"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("public output")
            with patch.object(Path, "open", side_effect=OSError("storage disappeared")):
                self.assertIsNone(checkpoint.artifact_digest(root, "workers/program/output.txt"))

    def test_directory_scan_stops_after_one_entry_over_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "workers/program"
            artifact.mkdir(parents=True)
            for number in range(10):
                (artifact / str(number)).touch()
            original_scandir = os.scandir

            class GuardedScan:
                def __init__(self, path):
                    self.scan = original_scandir(path)
                    self.consumed = 0

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.scan.close()

                def __iter__(self):
                    return self

                def __next__(self):
                    self.consumed += 1
                    if self.consumed > 4:
                        raise AssertionError("continued scanning oversized artifact tree")
                    return next(self.scan)

            with patch.object(checkpoint, "MAX_FILES", 3), patch.object(os, "scandir", GuardedScan):
                self.assertIsNone(checkpoint.artifact_digest(root, "workers/program"))


    def test_dangling_checkpoint_is_not_a_new_mission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = checkpoint.checkpoint_path(root, 42)
            path.symlink_to(root / "missing.json")
            with self.assertRaises(ValueError):
                checkpoint.load_checkpoint(root, issue=42, objective="Public task", team=("program",))
            with self.assertRaises(ValueError):
                checkpoint.save_checkpoint(root, issue=42, objective="Public task", team=("program",), results={})
            self.assertTrue(path.is_symlink())

    def test_intermediate_worker_alias_cannot_supply_another_worker_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            other = root / "workers/other"
            other.mkdir(parents=True)
            (other / "output.txt").write_text("other worker result")
            (root / "workers/program").symlink_to(other, target_is_directory=True)
            self.assertIsNone(checkpoint.artifact_digest(root, "workers/program/output.txt"))
            self.assertIsNotNone(checkpoint.artifact_digest(root, "workers/other/output.txt"))
            self.assertIsNone(checkpoint.artifact_digest(root, "workers//other/output.txt"))

    def test_checkpoint_save_never_overwrites_preexisting_temporary_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "unrelated.txt"
            existing.write_text("preserve")
            path = checkpoint.checkpoint_path(root, 42)
            path.with_suffix(".json.tmp").symlink_to(existing)
            result = {"program": {"attempt": 1, "verified": False}}
            checkpoint.save_checkpoint(root, issue=42, objective="Public task", team=("program",), results=result)
            self.assertEqual(existing.read_text(), "preserve")
            self.assertEqual(checkpoint.load_checkpoint(root, issue=42, objective="Public task", team=("program",)), result)

    def test_nonregular_checkpoint_is_not_a_new_mission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint.checkpoint_path(root, 42).mkdir()
            with self.assertRaises(ValueError):
                checkpoint.load_checkpoint(root, issue=42, objective="Public task", team=("program",))
