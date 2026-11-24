"""Independent original planner outcome acceptance, not a worker execution receipt."""
import json
from pathlib import Path
import tempfile
import unittest

from plenum_ai.chief_contract_plan import run_contract
from plenum_ai.chief_team_mission import grade_planned_clause


class PlannedScienceAcceptance(unittest.TestCase):
    def test_actual_solver_artifact_and_independent_negative_cases(self):
        goal = "cooling initial 347 K ambient 298 K rate 0.07 time 13"
        scope = {"cooling": {"initial_kelvin": 347., "ambient_kelvin": 298.,
                              "rate": .07, "duration": 13.}}
        solution = run_contract("cooling_solution", scope, {})
        readback = run_contract("cooling_readback", scope, {"cooling_solution": solution})
        step = {"kind": "public_science", "objective": goal}
        relative = "workers/public_science/issue-1001"
        worker = {"status": "DRAFT_READY_FOR_FOUNDER", "verified": True,
                  "_artifact_path": relative}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root / relative
            path.mkdir(parents=True)
            receipt = path / "cooling.json"
            data = {"cooling_solution": solution, "cooling_readback": readback}
            receipt.write_text(json.dumps(data))
            proof = grade_planned_clause(step, worker, root)
            self.assertEqual(proof["objective"], goal)
            self.assertLessEqual(proof["absolute_error_kelvin"], 1e-6)
            self.assertFalse(proof["experimental_validation"])
            for changed in (
                {**data, "cooling_solution": {**solution, "observed_kelvin": 999}},
                {**data, "cooling_solution": {**solution, "parameters": {**scope["cooling"], "duration": 14}}},
                {**data, "cooling_readback": {**readback, "experimental_validation": True}},
                {**data, "cooling_readback": {**readback, "absolute_error_kelvin": 1}},
                {"cooling_solution": solution},
            ):
                receipt.write_text(json.dumps(changed))
                self.assertIs(grade_planned_clause(step, worker, root), False)
            receipt.unlink()
            self.assertIs(grade_planned_clause(step, worker, root), False)
            self.assertIsNone(grade_planned_clause({**step, "objective": "Simulate unknown physics"}, worker, root))
            self.assertIs(grade_planned_clause({**step, "objective": goal.replace("0.07", "0")}, worker, root), False)


if __name__ == "__main__":
    unittest.main()
