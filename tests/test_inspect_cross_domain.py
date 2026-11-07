"""Deterministic and offline tests for the 96-example external benchmark."""
import unittest
from unittest.mock import patch

from plenum_ai import inspect_cross_domain as b


class InspectCrossDomainTests(unittest.TestCase):
    def test_plan_is_cost_gated_and_not_agi(self):
        p = b.plan()
        self.assertEqual(p["expected_total"], 96)
        self.assertEqual(p["samples_per_task"], 24)
        self.assertEqual(len(p["tasks"]), 4)
        self.assertEqual(p["max_generation_tokens"], 128)
        self.assertEqual(p["gsm8k_fewshot"], 0)
        self.assertFalse(p["enable_thinking"])
        for field in ("inference_executed", "AGI_demonstrated",
                      "private_documents_used", "trained_or_promoted_model"):
            self.assertFalse(p[field])
        self.assertEqual(p["model_calls"], 0)
        self.assertEqual(p["paid_api_calls"], 0)

    def test_normalize_only_approved_upstream_tasks(self):
        for item in b.TASKS:
            self.assertEqual(b.normalized_task(item), item)
            self.assertEqual(b.normalized_task("inspect_evals/" + item), item)
        for item in ("unknown", "inspect_evals/humaneval",
                     "other/arc_challenge", "", None):
            with self.subTest(item=item), self.assertRaises(ValueError):
                b.normalized_task(item)

    def test_only_approved_paths(self):
        self.assertEqual(str(b.permitted_report("reports/test.json")),
                         "reports/test.json")
        for bad in ("../output.json", "/tmp/private.json", "other/data.json",
                    "reports/../../outside.json", "reports/test.csv"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                b.permitted_report(bad)

    def test_model_revision_drift_rejected(self):
        with patch.object(b, "APPROVED_REVISION", "unsafe"):
            with self.assertRaisesRegex(ValueError, "Unreviewed"):
                b.plan()

    def test_audit_refuses_wrong_distribution(self):
        with patch("importlib.metadata.version", return_value="wrong"):
            with self.assertRaisesRegex(RuntimeError, "Unreviewed"):
                b.audit("reports/inspect-cross-logs")


if __name__ == "__main__":
    unittest.main()
