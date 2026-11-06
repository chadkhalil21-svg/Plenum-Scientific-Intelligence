"""Evidence that candidates train on distinct splits and cannot auto-deploy."""
import copy
import unittest

from plenum_ai.trainlab import TASKS, _dataset, _model, audit, propose, run_training_lab


class TrainedModelsTests(unittest.TestCase):
    def test_actual_training_and_heldout_evaluation(self):
        report = run_training_lab()
        self.assertEqual(report["evaluated_tasks"], 4)
        self.assertTrue(report["candidate_beats_dummy_in_all_tasks"], report)
        self.assertFalse(report["deployment_authorized"])
        self.assertFalse(report["AGI_demonstrated"])
        for item in report["tasks"]:
            case = item["audit"]
            self.assertTrue(case["independent_selection_reproduced"])
            self.assertFalse(case["holdout_used_for_selection"])
            self.assertGreater(case["manifest"]["train_size"], 30)
            self.assertGreater(case["manifest"]["holdout_size"], 25)
            self.assertEqual(item["proposal"]["test_results"],
                             "sealed_until_independent_audit")

    def test_leakage_and_out_of_domain_gravity(self):
        X, y, train, dev, holdout, meta = _dataset("gravity")
        self.assertLess(float(X[train].max()), float(X[holdout].min()))
        self.assertEqual(len(set(train) & set(dev)), 0)
        self.assertEqual(len(set(train) & set(holdout)), 0)
        self.assertEqual(len(set(dev) & set(holdout)), 0)
        self.assertIn("out-of-range", meta["source"])

    def test_tampered_candidate_rejected(self):
        proposal = propose("botany")
        changed = copy.deepcopy(proposal)
        changed["manifest"]["split_sha256"] = "fabricated"
        with self.assertRaises(ValueError):
            audit("botany", changed)
        changed = copy.deepcopy(proposal)
        changed["selected"] = "malicious_model"
        with self.assertRaises(ValueError):
            audit("botany", changed)
        changed = copy.deepcopy(proposal)
        changed["test_results"] = {"accuracy": 1.0}
        with self.assertRaises(ValueError):
            audit("botany", changed)

    def test_explicit_allowlist_and_bounds(self):
        with self.assertRaises(ValueError):
            _dataset("nonexistent")
        with self.assertRaises(ValueError):
            _model("chemistry", "arbitrary_code")
        with self.assertRaises(ValueError):
            run_training_lab(("botany", "botany"))
        with self.assertRaises(ValueError):
            run_training_lab(("invalid",))

    def test_separate_model_training_and_scientific_claims(self):
        report = run_training_lab(("botany",))
        self.assertFalse(report["scientific_discovery_verified"])
        self.assertFalse(report["automatic_model_promotion"])
        self.assertFalse(report["tasks"][0]["audit"]["trained_weights_persisted"])


if __name__ == "__main__":
    unittest.main()
