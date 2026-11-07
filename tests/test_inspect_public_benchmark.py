"""Regressions for the offline, non-promoting upstream science benchmark plan."""
import copy
import unittest
from unittest.mock import patch
from plenum_ai import inspect_public_benchmark as b

class PublicScienceInspectTests(unittest.TestCase):
    def test_offline_precommit_is_public_and_bounded(self):
        p=b.plan()
        self.assertEqual(p["model_id"],"Qwen/Qwen3-0.6B")
        self.assertEqual(len(p["model_revision"]),40)
        self.assertEqual(p["tasks"],["arc_easy","arc_challenge"])
        self.assertEqual(p["sample_limit_per_task"],12)
        self.assertEqual(p["max_model_connections"],1)
        for flag in ("inference_executed","paid_model_apis","private_data_used",
                     "automatic_promotion","AGI_demonstrated"):
            self.assertFalse(p[flag])
    def test_real_inspect_task_ids_are_normalized(self):
        self.assertEqual(b.normalize_task("inspect_evals/arc_easy"), "arc_easy")
        self.assertEqual(b.normalize_task("inspect_evals/arc_challenge"), "arc_challenge")
        self.assertEqual(b.normalize_task("arc_easy"), "arc_easy")
        for bad in ("inspect_evals/arc_unknown", "other/arc_easy", "", None):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                b.normalize_task(bad)

    def test_plan_explicitly_disables_qwen_thinking(self):
        p=b.plan()
        self.assertEqual(p["protocol_revision"], "v2-nonthinking-format-repair")
        self.assertFalse(p["chat_template_enable_thinking"])
        self.assertEqual(p["sample_limit_per_task"], 12)
        self.assertFalse(p["AGI_demonstrated"])

    def test_no_external_package_needed_for_default(self):
        with patch("importlib.metadata.version",side_effect=AssertionError("Unexpected package loaded")):
            self.assertFalse(b.plan()["inference_executed"])
    def test_unreviewed_model_is_rejected(self):
        with patch.object(b,"APPROVED_REVISION","bad"):
            with self.assertRaisesRegex(ValueError,"pin changed"):
                b.plan()
    def test_refuse_non_report_paths(self):
        for raw in ("/tmp/out.json","../out.json","private.json",
                    "reports/../../outside.json","reports/file.csv"):
            with self.subTest(path=raw), self.assertRaises(ValueError):
                b.checked_path(raw)
        self.assertEqual(str(b.checked_path("reports/score.json")),"reports/score.json")
    def test_no_log_directory(self):
        with patch("importlib.metadata.version",return_value="unreviewed"):
            with self.assertRaisesRegex(RuntimeError,"version changed"):
                b.audit("reports/missing")

if __name__=="__main__":
    unittest.main()
