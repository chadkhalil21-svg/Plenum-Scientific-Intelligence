"""Safety contract checks; never run the upstream scientific evaluator."""
import json
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
import run_fixed_baseline


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

    @unittest.skipUnless(os.name == "posix", "POSIX process-group boundary")
    def test_timeout_kills_descendant_with_inherited_pipe(self):
        self.assertTrue(hasattr(run_fixed_baseline, "_wait_bounded"))
        # The test exercises process cleanup only, never the upstream evaluator.
        code = (
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(8)']); "
            "print('ready', flush=True); time.sleep(8)"
        )
        proc = subprocess.Popen(
            [sys.executable, "-c", code], start_new_session=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            self.assertEqual(proc.stdout.readline().strip(), "ready")
            started = time.monotonic()
            with self.assertRaises(subprocess.TimeoutExpired):
                run_fixed_baseline._wait_bounded(proc, 0.1)
            self.assertLess(time.monotonic() - started, 3.0)
            self.assertIsNotNone(proc.poll())
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.communicate(timeout=2)


if __name__ == "__main__":
    unittest.main()
