"""Independent preflight tests for constrained open-weight model fine-tuning."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from plenum_ai.fine_tune import (CONFIG, ORIGINAL_LESSONS, _training_example,
                                 training_checksum, _manifest, verify_manifest)


class CandidateCheckpointTests(unittest.TestCase):
    def test_fixed_training_set_separate_from_arc(self):
        self.assertEqual(CONFIG["steps"], 2)
        self.assertEqual(CONFIG["test_count"], 8)
        self.assertGreaterEqual(len(ORIGINAL_LESSONS), 8)
        self.assertEqual(len(training_checksum()), 64)
        for i in range(len(ORIGINAL_LESSONS)):
            example = _training_example(i)
            self.assertTrue(example["id"].startswith("plenum-original-"))
            self.assertEqual(len(example["options"]), 4)
            self.assertIn(example["answer_index"], range(4))

    def test_safetensors_manifest_and_tampering(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            (folder/"adapter_model.safetensors").write_bytes(b"checkpoint-fixture-only")
            (folder/"adapter_config.json").write_text('{"r":2}')
            fake_report = {
                "base_model": "Qwen/Qwen3-0.6B",
                "base_model_revision": "a"*40,
                "training_fixture_sha256": training_checksum(),
                "source": {"revision": "b"*40},
                "baseline": {"sample_sha256": "c"*64},
            }
            manifest = _manifest(folder, fake_report)
            self.assertTrue(verify_manifest(folder))
            self.assertFalse(manifest["promoted_or_deployed"])
            (folder/"adapter_config.json").write_text("tampered")
            with self.assertRaises(ValueError):
                verify_manifest(folder)

    def test_corrupted_manifest_fails(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                verify_manifest(d)

if __name__ == "__main__":
    unittest.main()
