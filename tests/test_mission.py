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
        self.assertIn("Qwen3", APPROVED_MODEL)


from plenum_ai.quality import assess_answer


class QualityTests(unittest.TestCase):
    def test_repetition_is_rejected(self):
        text = ("Scientific hypothesis proposer: Provide two falsifiable proposals and tests. " * 4)
        self.assertFalse(assess_answer(text, "proposer")["acceptable"])

    def test_fabricated_citations_rejected(self):
        fake = "The tests were verified by a journal. Citations: [1] Smith et al., Nature, 2023."
        self.assertEqual(assess_answer(fake + " This is an invented reference.", "proposer")["reason"], "unsupported_reference_style")

    def test_empty_is_rejected(self):
        self.assertFalse(assess_answer("short", "critic")["acceptable"])

    def test_plausible_but_not_proven_accepted_for_screen(self):
        text = "A proposed test would compare the conservation errors of two separate numerical schemes across distinct step sizes and independently report discrepancies."
        self.assertTrue(assess_answer(text, "proposer")["acceptable"])


if __name__ == "__main__":
    unittest.main()
