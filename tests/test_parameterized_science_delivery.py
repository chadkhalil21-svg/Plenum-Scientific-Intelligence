"""Real end-to-end numerical science worker acceptance, without model or network mocks."""
import json
import math
from pathlib import Path
import runpy
import tempfile
import unittest

from plenum_ai.workforce_public_inbox import run_issue
from plenum_ai.chief_team_mission import grade_planned_clause

# Reuse the already frozen independent candidate tests, unchanged.
_frozen = runpy.run_path(str(Path(__file__).parent / "acceptance" / "parameterized_science_worker.py"))
CoolingWorkerAcceptance = _frozen["CoolingWorkerAcceptance"]


class ActualScientificDelivery(unittest.TestCase):
    def test_actual_two_unfamiliar_numerical_cases(self):
        for initial, ambient, rate, duration in ((351, 299, .08, 17), (281, 312, .06, 9)):
            goal = f"cooling initial {initial} K ambient {ambient} K rate {rate} time {duration}"
            with self.subTest(goal=goal), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                worker_root = root / "workers" / "public_science"
                event = _frozen["event"](goal)
                result = run_issue(event, output_dir=worker_root)
                self.assertTrue(result["verified"])
                path = worker_root / result["output_artifact"]
                data = json.loads((path / "cooling.json").read_text())
                expected = ambient + (initial - ambient) * math.exp(-rate * duration)
                self.assertAlmostEqual(data["cooling_solution"]["observed_kelvin"], expected, places=6)
                self.assertEqual(data["cooling_solution"]["method"], "RK45")
                proof = grade_planned_clause({"kind":"public_science","objective":goal},
                    {**result,"_artifact_path":path.relative_to(root).as_posix()}, root)
                self.assertIsInstance(proof, dict)
                self.assertLessEqual(proof["absolute_error_kelvin"], 1e-6)
                self.assertFalse(proof["experimental_validation"])

    def test_malformed_cooling_is_not_generic_science_success(self):
        with tempfile.TemporaryDirectory() as d:
            result = run_issue(_frozen["event"]("cooling initial 351 K ambient 299 K rate invalid time 17"),
                               output_dir=Path(d))
            self.assertFalse(result["verified"])


if __name__ == "__main__":
    unittest.main()
