"""Tests for a genuine two-round model-directed scientific research loop.

Model responses are deterministic stubs here. Only the separate GitHub
workflow proves actual Qwen inference, not these unit tests.
"""
import copy
import json
import unittest
from unittest.mock import patch
from plenum_ai import hypothesis_cycle as h


def fake_generator(prompt):
    if "Domain: thermal" in prompt:
        a,b=-0.22,0.0
    elif "Domain: chemical" in prompt:
        a,b=0.0,-0.24
    elif "Domain: electrical" in prompt:
        a,b=-0.11,-0.13
    else:
        raise AssertionError("Unapproved hypothesis context")
    if "Self-critique" not in prompt:
        a,b=-0.06,-0.02
    return json.dumps({
        "linear":a,"quadratic":b,
        "hypothesis":"An estimated continuous rate model predicts normalized future states.",
        "falsifier":"The model is rejected if withheld measured errors exceed a fit baseline."
    })


class ScientificHypothesisCycleTests(unittest.TestCase):
    def test_three_scientific_fields_and_revision(self):
        p=h.propose("Public synthetic scientific models",fake_generator)
        self.assertEqual(len(p["cases"]),3)
        self.assertEqual(p["model_calls"],6)
        self.assertFalse(p["holdout_seen"])
        self.assertFalse(p["AGI_demonstrated"])
        self.assertFalse(p["model_promoted"])
        for case in p["cases"]:
            self.assertEqual(case["chosen_round"],"revision")
            self.assertIsNotNone(case["chosen_hypothesis"])
            self.assertEqual(case["revision_history"][0]["round"],"initial")
            self.assertEqual(case["revision_history"][1]["round"],"revision")
            self.assertEqual(case["last_dev_time"],7)

    def test_proposer_never_accesses_holdout(self):
        orig=h.observations
        access=[]
        def guard(domain, last):
            access.append(last)
            if last==h.HOLDOUT_END:
                raise AssertionError("Holdout leaked to model")
            return orig(domain,last)
        with patch.object(h,"observations",side_effect=guard):
            h.propose("Public bounded study",fake_generator)
        self.assertEqual(set(access),{h.TRAIN_END,h.DEV_END})

    def test_independent_audit_compares_to_strongest_baseline(self):
        p=h.propose("Public bounded study",fake_generator)
        a=h.audit(p)
        self.assertEqual(a["domains_tested"],3)
        self.assertEqual(a["valid_hypotheses"],3)
        self.assertTrue(a["evidence_independently_reproduced"])
        self.assertFalse(a["independent_scientific_discovery"])
        self.assertFalse(a["recursive_self_improvement"])
        for finding in a["results"]:
            self.assertIn("fitted_linear",finding["baseline_test_mae"])
            self.assertIn("fitted_quadratic",finding["baseline_test_mae"])
            self.assertIsInstance(finding["better_than_strongest_baseline"],bool)

    def test_invalid_json_is_recorded_and_never_silent_fallback(self):
        def bad(_prompt):
            return "I discovered AGI and have no JSON."
        p=h.propose("Public bounded study",bad)
        self.assertTrue(all(x["chosen_hypothesis"] is None for x in p["cases"]))
        a=h.audit(p)
        self.assertEqual(a["valid_hypotheses"],0)
        self.assertEqual(a["wins_over_strongest_baseline"],0)

    def test_false_claims_and_arbitrary_code_cannot_be_executed(self):
        for raw in ('{"linear":-0.3,"quadratic":-0.2,"hypothesis":"too short","falsifier":"short"}',
                    '{"linear":9,"quadratic":0,"hypothesis":"A scientific rate model","falsifier":"It fails when future prediction error increases"}',
                    'import os; os.system("echo attack")',
                    '{"linear":-0.2,"quadratic":0,"hypothesis":"A physical rate model","falsifier":"A study could reject the prediction","command":"delete"}'):
            with self.subTest(raw=raw[:20]):
                self.assertIsNone(h.parse_output(raw)["candidate"])

    def test_tampering_with_rates_and_metrics_is_rejected(self):
        original=h.propose("Public bounded study",fake_generator)
        for field,value in [("chosen_dev_mae",0.0),("last_dev_time",11),
                            ("chosen_round","initial")]:
            p=copy.deepcopy(original)
            p["cases"][0][field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):
                h.audit(p)
        p=copy.deepcopy(original)
        p["cases"][0]["chosen_hypothesis"]["linear"]=-0.9
        with self.assertRaises(ValueError):
            h.audit(p)

    def test_model_provenance_must_be_exact(self):
        for model,revision in ((h.MODEL,"main"),("Qwen/unapproved",h.REVISION)):
            with self.assertRaises(ValueError):
                h.propose("public",fake_generator,model=model,revision=revision)

    def test_time_window_and_synthetic_physics_guardrails(self):
        with self.assertRaises(ValueError):
            h.observations("thermal",12)
        with self.assertRaises(ValueError):
            h.observations("unknown",4)
        with self.assertRaises(ValueError):
            h.advance(1.0,-1.1,0,1)
        with self.assertRaises(ValueError):
            h.advance(1.0,-0.1,0,999)
        self.assertAlmostEqual(h.advance(1.4,-0.22,0,4),
                               h.observations("thermal",4)[-1]["y"],places=7)

    def test_holdout_not_leaked_in_revision_prompt(self):
        prompts=[]
        def recorder(prompt):
            prompts.append(prompt)
            return fake_generator(prompt)
        h.propose("public",recorder)
        self.assertEqual(len(prompts),6)
        for x in prompts:
            self.assertNotIn('"t": 8, "y":',x)
            self.assertNotIn('"t": 11, "y":',x)
        self.assertIn("development",prompts[1].lower())
        self.assertIn("baseline",prompts[1].lower())


if __name__=="__main__":
    unittest.main()
