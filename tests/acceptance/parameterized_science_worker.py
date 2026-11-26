"""Held-out behavior gate for the original science worker's parameterized cooling route."""
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from plenum_ai import chief_contract_plan as contracts
from plenum_ai.workforce_public_inbox import run_issue


def event(objective):
    return {"action": "opened",
            "repository": {"full_name": "chadkhalil21-svg/Plenum-Scientific-Intelligence"},
            "issue": {"number": 901, "user": {"login": "chadkhalil21-svg"},
                      "title": "[Plenum Workforce] public research",
                      "body": "PLENUM_PUBLIC_WORKFORCE_V2\nkind: public_science\nobjective: " + objective}}


class CoolingWorkerAcceptance(unittest.TestCase):
    def test_distinct_inputs_use_original_solver_and_independent_readback(self):
        original = contracts.run_contract
        for initial, ambient, rate, duration in [(370, 300, .07, 11), (280, 310, .03, 17)]:
            objective = f"cooling initial {initial} K ambient {ambient} K rate {rate} time {duration}"
            parameters = {"initial_kelvin": initial, "ambient_kelvin": ambient,
                          "rate": rate, "duration": duration}
            temperature = ambient + (initial - ambient) * math.exp(-rate * duration)
            solution = {"observed_kelvin": temperature, "parameters": parameters,
                        "library": "SciPy solve_ivp", "method": "RK45"}
            calls = []
            def solver(tool, scope, prior):
                self.assertEqual(scope["cooling"], parameters)
                calls.append(tool)
                if tool == "cooling_solution":
                    return solution
                self.assertEqual(prior["cooling_solution"], solution)
                return original(tool, scope, prior)
            with self.subTest(objective=objective), tempfile.TemporaryDirectory() as d, patch.object(
                contracts, "run_contract", side_effect=solver
            ):
                root = Path(d)
                result = run_issue(event(objective), output_dir=root)
                self.assertTrue(result["verified"])
                self.assertEqual(result["status"], "DRAFT_READY_FOR_FOUNDER")
                self.assertEqual(calls, ["cooling_solution", "cooling_readback"])
                report = json.loads((root / "issue-901" / "cooling.json").read_text())
                self.assertEqual(report["cooling_solution"], solution)
                self.assertAlmostEqual(report["cooling_readback"]["analytic_kelvin"], temperature, places=8)
                self.assertLessEqual(report["cooling_readback"]["absolute_error_kelvin"], 1e-6)

    def test_invalid_parameters_and_wrong_solver_output_cannot_pass(self):
        objective = "cooling initial 370 K ambient 300 K rate 0.07 time 11"
        original = contracts.run_contract
        def bad_solver(tool, scope, prior):
            if tool == "cooling_solution":
                return {"observed_kelvin": 999, "parameters": scope["cooling"]}
            return original(tool, scope, prior)
        with tempfile.TemporaryDirectory() as d, patch.object(contracts, "run_contract", side_effect=bad_solver):
            self.assertFalse(run_issue(event(objective), output_dir=Path(d))["verified"])
        for bad in ("cooling initial 370 K ambient 300 K rate 0 time 11",
                    "cooling initial 2100 K ambient 300 K rate 0.07 time 11"):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as d, patch.object(contracts, "run_contract") as solve:
                self.assertFalse(run_issue(event(bad), output_dir=Path(d))["verified"])
                solve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
