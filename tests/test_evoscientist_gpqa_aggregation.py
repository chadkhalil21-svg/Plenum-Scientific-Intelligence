import importlib.util
import json
import unittest
from pathlib import Path
import tempfile

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "integrations/upstream/evoscientist-v0.4.3/aggregate_gpqa.py"

class PublicGpqaAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "optional EvoScientist adapter missing")
        spec = importlib.util.spec_from_file_location("public_gpqa", SCRIPT)
        self.adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.adapter)

    def test_only_original_native_pair_is_prepared(self):
        with tempfile.TemporaryDirectory() as d:
            rows = self.adapter.prepare_grades(BASE, Path(d))
            self.assertEqual(len(rows), 6)
            actual = [(
                r["expectations"][0]["passed"],
                r["summary"]["total"],
            ) for r in rows]
            self.assertEqual(actual, [(False, 1), (False, 1), (False, 1), (True, 1), (False, 1), (False, 1)])
            for r in rows:
                self.assertNotIn("timing", r)
                self.assertNotIn("execution_metrics", r)
            self.assertEqual(len(list(Path(d).glob("eval-*/**/grading.json"))), 6)

    def test_hash_mismatch_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "fake"
            root.mkdir()
            for relpath in self.adapter.SOURCES:
                dst = root / relpath
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes((BASE / relpath).read_bytes())
            (root / next(iter(self.adapter.SOURCES))).write_text("{}")
            out = Path(d) / "output"
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                self.adapter.prepare_grades(root, out)
            self.assertFalse(out.exists())

if __name__ == "__main__":
    unittest.main()
