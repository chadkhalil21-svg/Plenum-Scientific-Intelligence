"""Safety contract checks; never run the upstream scientific evaluator."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent


class FixedComponentBoundaryTests(unittest.TestCase):
    def invoke(self, root, *args):
        return subprocess.run(
            [sys.executable, str(root / "run_fixed_baseline.py"), *args],
            capture_output=True, text=True, timeout=10,
        )

    def test_verify_only_validates_fixed_sources_without_execution(self):
        result = self.invoke(HERE, "--verify-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["upstream_commit"],
                         "de1cd267b8922faa31631fb397bbc202bf714d84")
        self.assertTrue(report["sources_verified"])
        self.assertFalse(report["evaluator_executed"])

    def test_rejects_arbitrary_program_argument(self):
        result = self.invoke(HERE, "--run", "--program", "arbitrary.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_tampered_candidate_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "component"
            shutil.copytree(HERE, root)
            candidate = root / "examples/circpack/program_0/src/program.py"
            candidate.write_text("raise RuntimeError('must not execute')\n", encoding="utf-8")
            result = self.invoke(root, "--run")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Source integrity failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
