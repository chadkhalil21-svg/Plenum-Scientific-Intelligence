import unittest
from plenum_ai.mission import run_mission
from plenum_ai.science import diffuse_heat
from plenum_ai.hf_model import APPROVED_MODEL, _load_model


class MissionTests(unittest.TestCase):
    def test_heat_conserves_total(self):
        r = diffuse_heat()
        self.assertTrue(r["verification"]["conserved_discrete_total"])
        self.assertLess(max(r["final_profile"]), max(r["initial_profile"]))

    def test_unstable_time_step_refused(self):
        with self.assertRaises(ValueError):
            diffuse_heat(dt=1.0)

    def test_offline_mission_is_not_discovery(self):
        report = run_mission("Can we improve materials?", offline=True)
        self.assertEqual(report["source_status"], "offline_fixture_no_research_retrieval")
        self.assertFalse(report["verified_new_scientific_discovery"])
        self.assertTrue(report["numeric_benchmark_verified"])
        self.assertFalse(report["model_inference_executed"])

    def test_agent_roles_call_model_twice(self):
        called = []
        def dummy(prompt, model):
            called.append(prompt)
            return "Not verified"
        report = run_mission("Check physics", offline=True,
                             model="test-local", generator=dummy, simulation="orbit")
        self.assertEqual(len(called), 2)
        self.assertIn("critic", called[1].lower())
        self.assertTrue(report["model_inference_executed"])

    def test_failed_source_is_recorded(self):
        def fail(_):
            raise RuntimeError("Unavailable")
        report = run_mission("physics", searcher=fail)
        self.assertEqual(report["source_status"], "source_unavailable")
        self.assertEqual(len(report["issues"]), 1)

    def test_model_allowlist(self):
        with self.assertRaises(ValueError):
            _load_model("arbitrary/unreviewed-code")
        self.assertIn("SmolLM2", APPROVED_MODEL)


if __name__ == "__main__":
    unittest.main()
