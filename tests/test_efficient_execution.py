"""Regression checks for cheapest authorized scientific execution path."""
import json
import tempfile
import unittest
from pathlib import Path
from plenum_ai import efficient_execution as e


def fixture(domain):
    return {"domain": domain, "verified_fixture": True,
            "limitation": "Reviewed historical numerical fixture, not new science."}


class EfficientExecutionTests(unittest.TestCase):
    def test_single_thermal_question_uses_one_tool_not_four(self):
        report=e.execute("Demonstrate thermal cooling dynamics",solver=fixture)
        self.assertEqual(report["domains"],["materials"])
        self.assertEqual(report["approved_tool_count"],1)
        self.assertEqual(report["unnecessary_default_fixture_calls_avoided"],3)
        self.assertEqual(len(report["results"]),1)
        self.assertTrue(report["known_model_checks_passed"])
        self.assertFalse(report["AGI_demonstrated"])
        self.assertFalse(report["scientific_discovery_verified"])
        self.assertFalse(report["user_specific_problem_solved"])
        self.assertEqual(report["estimated_model_calls"],0)
        self.assertEqual(report["status"],"known_fixtures_completed")

    def test_multiple_domains_do_not_repeat_the_same_tool(self):
        called=[]
        def observer(domain):
            called.append(domain)
            return fixture(domain)
        report=e.execute("Compare orbital gravity and thermal heat dissipation",solver=observer)
        self.assertEqual(called,["mechanics","materials"])
        self.assertEqual(report["approved_tool_count"],2)
        self.assertEqual(report["unnecessary_default_fixture_calls_avoided"],2)

    def test_word_boundaries_prevent_accidental_chemical_matches(self):
        report=e.plan("How does wheat grow during evolution?")
        self.assertEqual(report["decision"],"review_required")
        self.assertEqual(report["approved_tool_count"],0)
        self.assertNotIn("materials",report["domains"])
        self.assertNotIn("chemistry",report["domains"])

    def test_unrecognized_problem_never_executes_or_fabricates(self):
        executed=[]
        def forbidden(domain):
            executed.append(domain)
            raise AssertionError("No tool should have run")
        report=e.execute("Discover a new unified theory of consciousness",solver=forbidden)
        self.assertEqual(executed,[])
        self.assertEqual(report["status"],"requires_review")
        self.assertFalse(report["known_model_checks_passed"])
        self.assertEqual(report["results"],[])

    def test_confidential_query_not_routed_or_copied_to_artifact(self):
        question="Review my confidential rocket design secret"
        report=e.execute(question,solver=lambda _domain: self.fail("No private execution"))
        self.assertEqual(report["decision"],"review_required")
        self.assertEqual(report["reason"],
                         "private_or_confidential_content_not_suitable_for_public_actions")
        self.assertNotIn(question,json.dumps(report))
        self.assertEqual(report["approved_tool_count"],0)

    def test_dry_run_is_side_effect_free_even_for_matching_science(self):
        called=[]
        def side_effect(domain):
            called.append(domain)
        result=e.execute("Solve an RC circuit",dry_run=True,solver=side_effect)
        self.assertEqual(result["status"],"planned_without_execution")
        self.assertEqual(called,[])
        self.assertEqual(result["approved_tool_count"],1)
        self.assertEqual(result["results"],[])

    def test_more_than_three_distinct_domains_requires_review(self):
        report=e.plan("Compare gravity, heat, chemical reaction, and RC circuit")
        self.assertEqual(report["decision"],"review_required")
        self.assertEqual(report["approved_tool_count"],0)
        self.assertEqual(report["reason"],
                         "too_many_distinct_domains_for_a_bounded_fixture_run")

    def test_unverified_result_does_not_promote_success(self):
        result=e.execute("Circuit and capacitor physics",solver=lambda domain: {
            "domain":domain,"verified_fixture":False})
        self.assertEqual(result["status"],"fixture_failed")
        self.assertFalse(result["known_model_checks_passed"])
        self.assertFalse(result["scientific_discovery_verified"])

    def test_solver_failure_is_recorded_without_fabricated_response(self):
        def fail(_domain):
            raise RuntimeError("User data should not leak into artifact")
        result=e.execute("Demonstrate orbit propagation",solver=fail)
        self.assertEqual(result["results"][0]["error_type"],"RuntimeError")
        self.assertNotIn("User data should not leak",json.dumps(result))
        self.assertEqual(result["status"],"fixture_failed")

    def test_public_report_has_only_bounded_metadata(self):
        question="Simulate known ethanol molecular formula"
        report=e.execute(question,solver=fixture)
        self.assertEqual(report["domains"],["molecules"])
        self.assertFalse(report["question_text_in_public_artifact"])
        self.assertNotIn(question,json.dumps(report))
        self.assertFalse(report["external_requests_authorized"])
        self.assertFalse(report["paid_inference_authorized"])
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"report.json"
            e.save_report(target,report)
            disk=json.loads(target.read_text())
            self.assertEqual(disk["question_sha256"],report["question_sha256"])
            self.assertEqual(disk["estimated_model_calls"],0)

    def test_rejects_empty_and_long_queries(self):
        for value in ("", "  ", "a"*601, None, 17):
            with self.subTest(value=str(value)[:20]),self.assertRaises(ValueError):
                e.plan(value)

    def test_real_mathematical_fixture_works_when_scipy_installed(self):
        from plenum_ai.lab import solve
        output=e.execute("Review Earth orbit equations",solver=solve)
        self.assertTrue(output["known_model_checks_passed"])
        self.assertLess(output["results"][0]["output"]["relative_error"],2e-6)
        self.assertFalse(output["scientific_discovery_verified"])


if __name__ == "__main__":
    unittest.main()
