"""Focused regression for actual original #733 local Free AI budget exhaustion.

No provider, model, container, original mission or paid service is called.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from plenum_ai import openhands_coding_agent as coder


class OriginalFreeBudgetRecovery(unittest.TestCase):
    def test_reuse_upstream_retry_config_only_for_exact_free_cloud_route(self):
        self.assertEqual(coder.original_free_retry_options(
            "openai/glm-4.7-flash", coder.ORIGINAL_FREE_CODING_ENDPOINT),
            {"num_retries": 1})
        for model, url in (
            ("ollama/qwen3:1.7b", "http://127.0.0.1:11434"),
            ("openai/glm-4.7-flash", "https://another-provider.example/ai/v1"),
            ("openai/other-model", coder.ORIGINAL_FREE_CODING_ENDPOINT),
        ):
            self.assertEqual(coder.original_free_retry_options(model, url), {})

    def test_true_daily_local_cap_retains_nonsecret_failure_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            old = Path.cwd()
            try:
                os.chdir(temporary)
                with patch.object(sys, "argv", ["coder", "--execute",
                                               "--out", "reports/free-cap.json"]), \
                     patch.dict(os.environ, {
                         "PLENUM_OPENHANDS_MODEL": "openai/glm-4.7-flash",
                         "PLENUM_OPENHANDS_BASE_URL": coder.ORIGINAL_FREE_CODING_ENDPOINT,
                     }), \
                     patch.object(coder, "execute",
                         side_effect=RuntimeError("429 original_daily_ai_budget_exhausted")) as model:
                    with self.assertRaises(SystemExit) as failure:
                        coder.main()
                    self.assertEqual(failure.exception.code, 2)
                    self.assertEqual(model.call_count, 1)
                report = json.loads(Path("reports/free-cap.json").read_text())
                self.assertEqual(report["status"], "BLOCKED_ORIGINAL_DAILY_FREE_AI_CAP")
                self.assertFalse(report["provider_account_quota_verified"])
                self.assertFalse(report["model_run_completed"])
                self.assertFalse(report["candidate_persisted"])
                self.assertFalse(report["retry_same_day_authorized"])
                self.assertNotIn("original_daily_ai_budget_exhausted", str(report))
            finally:
                os.chdir(old)

    def test_unrelated_failure_is_not_silently_relabelled(self):
        with tempfile.TemporaryDirectory() as temporary:
            old = Path.cwd()
            try:
                os.chdir(temporary)
                with patch.object(sys, "argv", ["coder", "--execute",
                                               "--out", "reports/other.json"]), \
                     patch.dict(os.environ, {
                         "PLENUM_OPENHANDS_MODEL": "openai/glm-4.7-flash",
                         "PLENUM_OPENHANDS_BASE_URL": coder.ORIGINAL_FREE_CODING_ENDPOINT,
                     }), \
                     patch.object(coder, "execute", side_effect=RuntimeError("unknown failure")):
                    with self.assertRaisesRegex(RuntimeError, "unknown failure"):
                        coder.main()
                self.assertFalse(Path("reports/other.json").exists())
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
