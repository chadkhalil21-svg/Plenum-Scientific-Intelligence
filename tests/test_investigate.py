import unittest
from plenum_ai.investigate import investigate, supervise


class ResearchTeamTests(unittest.TestCase):
    def test_offline_science_team(self):
        report=investigate("Could orbital mechanics be improved?", offline=True)
        self.assertTrue(report["workflow_verified_as_known_tool_demonstration"])
        self.assertFalse(report["hypotheses_verified"])
        self.assertFalse(report["claims"]["new_scientific_discovery_verified"])
        self.assertEqual(len(report["roles"]),7)
        self.assertTrue(report["lab"]["known_model_checks_passed"])

    def test_independent_roles_receive_distinct_prompts(self):
        calls=[]
        def local_agent(prompt, model):
            calls.append(prompt)
            return "Unverified proposal subject to independent numerical checks and physical experiments."
        report=investigate("Can orbital mechanics be improved?", model="test",
                           generator=local_agent, offline=True, domains=["mechanics"])
        self.assertEqual(len(calls),2)
        self.assertIn("critic",calls[1].lower())
        self.assertFalse(report["hypotheses_verified"])
        self.assertTrue(report["workflow_verified_as_known_tool_demonstration"])

    def test_bad_evidence_never_certified(self):
        report=investigate("Test molecular chemistry",offline=True,domains=["molecules"])
        report["lab"]["known_model_checks_passed"]=False
        report=supervise(report)
        self.assertFalse(report["workflow_verified_as_known_tool_demonstration"])
        self.assertFalse(report["claims"]["new_scientific_discovery_verified"])

    def test_unknown_domain_refused(self):
        with self.assertRaises(ValueError):
            investigate("Any question",offline=True,domains=["shell"])

    def test_no_paid_service_or_live_retrieval_for_offline_fixture(self):
        r=investigate("Testing materials",offline=True,domains=["materials"])
        self.assertEqual(r["research"]["source_status"],"offline_fixture_no_research_retrieval")
        self.assertFalse(r["research"]["model_inference_executed"])
