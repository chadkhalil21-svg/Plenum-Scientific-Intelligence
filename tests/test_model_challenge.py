"""Isolation and comparison tests. Stubs are not model-performance evidence."""
import unittest
from plenum_ai.model_challenge import (
    MODELS, DOMAINS, HOLDOUTS, parse_hypothesis, propose_comparison,
    audit_comparison, HYPOTHESIS_PROMPT,
)
from plenum_ai.research_pilot import METHODS

REV = "a" * 40


def solver(domain, method):
    rows = {"materials": (120, 65, 190), "electronics": (90, 50, 175),
            "chemistry": (115, 80, 225), "mechanics": (100, 115, 245)}
    return {"domain": domain, "method": method, "verified_fixture": True,
            "solver_function_evaluations": rows[domain][METHODS.index(method)],
            "relative_error": 1e-10, "invariant_error": 0.0}


def draft(_prompt):
    return '{"hypothesis":"One solver could perform more efficiently in thermal cases.",' \
           '"experiment":"Compare all three solvers under fixed tolerance constraints.",' \
           '"falsification":"An alternative may require fewer derivative evaluations.",' \
           '"alternative_explanation":"One result may reflect numerical stiffness rather than skill."}'


def propose(model_id, choice="B", gen=draft):
    return propose_comparison(model_id, lambda prompt: choice, gen, REV, solver=solver)


class ModelChallengeTests(unittest.TestCase):
    def test_model_proposals_and_heldout_domain_separation(self):
        prompts = []
        def choose(text):
            prompts.append(text)
            return "B"
        p = propose_comparison(MODELS[0], choose, draft, REV, solver=solver)
        self.assertEqual(len(prompts), 2)
        self.assertIn("Development case: materials", prompts[0])
        self.assertNotIn("electronics", prompts[0])
        self.assertIn("Development case: chemistry", prompts[1])
        self.assertNotIn("mechanics", prompts[1])
        self.assertFalse(p["holdout_executed"])
        self.assertTrue(p["model_inference_executed"])
        self.assertFalse(p["auto_model_promotion"])

    def test_positive_and_negative_comparison_kept(self):
        a = propose(MODELS[0], "A")
        b = propose(MODELS[1], "B")
        audit = audit_comparison(a, b, solver=solver)
        self.assertEqual(audit["baseline"]["correct"], 0)
        self.assertEqual(audit["candidate"]["correct"], 1)
        self.assertTrue(audit["candidate_better_on_these_tasks"])
        self.assertTrue(audit["same_holdout_evidence"])
        self.assertFalse(audit["model_promoted"])
        self.assertFalse(audit["stronger_general_intelligence_proven"])
        self.assertEqual([x["holdout_domain"] for x in audit["candidate"]["cases"]],
                         list(HOLDOUTS))

    def test_no_model_gain_remains_no_model_gain(self):
        a = propose(MODELS[0], "B")
        b = propose(MODELS[1], "C")
        result = audit_comparison(a, b, solver=solver)
        self.assertFalse(result["candidate_better_on_these_tasks"])
        self.assertFalse(result["hypotheses_independently_verified"])

    def test_model_swap_is_rejected(self):
        p = propose(MODELS[0])
        p["model_id"] = MODELS[1]
        with self.assertRaises(ValueError):
            audit_comparison(p, propose(MODELS[1]), solver=solver)

    def test_model_attribution_in_seal_is_rejected(self):
        p = propose(MODELS[0])
        p["proposals"][0]["sealed"]["model"] = "spoof"
        with self.assertRaises(ValueError):
            audit_comparison(p, propose(MODELS[1]), solver=solver)

    def test_mutated_prediction_is_rejected(self):
        p = propose(MODELS[0])
        p["proposals"][0]["sealed"]["answer"] = "C"
        with self.assertRaises(ValueError):
            audit_comparison(p, propose(MODELS[1]), solver=solver)

    def test_hypothesis_schema_and_untrusted_output(self):
        parsed = parse_hypothesis(draft(HYPOTHESIS_PROMPT))
        self.assertEqual(parsed["status"], "unverified_draft")
        self.assertFalse(parsed["experiment_performed"])
        self.assertFalse(parsed["scientific_discovery_verified"])
        for response in ("not JSON", '{"hypothesis":"too short"}', "B"):
            with self.subTest(response=response):
                self.assertIsNone(parse_hypothesis(response)["draft"])

    def test_reject_unapproved_model_or_revision(self):
        with self.assertRaises(ValueError):
            propose_comparison("arbitrary/new-model", lambda q: "A", draft, REV,
                               solver=solver)
        with self.assertRaises(ValueError):
            propose_comparison(MODELS[0], lambda q: "A", draft, "main",
                               solver=solver)

    def test_reject_unverifiable_solver(self):
        def wrong(domain, method):
            row = solver(domain, method)
            row["verified_fixture"] = False
            return row
        with self.assertRaises(ValueError):
            propose_comparison(MODELS[0], lambda prompt: "B", draft, REV,
                               solver=wrong)

if __name__ == "__main__":
    unittest.main()
