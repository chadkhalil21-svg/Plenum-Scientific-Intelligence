"""Recovery must reject unsafe worker artifacts without exhausting the runner."""
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from plenum_ai import mission_checkpoint as checkpoint


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
