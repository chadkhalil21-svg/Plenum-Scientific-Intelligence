"""No-network checks of official free-only Workers AI inference preflight."""
from datetime import timedelta
import unittest

from tools.cloudflare_workers_ai_budget import validate, REVIEWED


def valid(**extras):
    value = {
        "plan": "free",
        "model": "@cf/zai-org/glm-4.7-flash",
        "usage_day_utc": REVIEWED.isoformat(),
        "neurons_used_today": 100,
        "neurons_reserved": 200,
        "input_tokens_upper_bound": 1000,
        "output_tokens_upper_bound": 1000,
    }
    value.update(extras)
    return value


class FreeAIPreflightTests(unittest.TestCase):
    def test_source_neuron_rates_are_used_without_calling_provider(self):
        v = validate(valid(), today=REVIEWED)
        self.assertEqual(v["status"], "LOCAL_BUDGET_ESTIMATE_ONLY_ACCOUNT_UNVERIFIED")
        self.assertEqual(v["estimate_neurons"], 42)
        self.assertEqual(v["local_remaining_after"], 9658)
        self.assertFalse(v["zero_cost_guaranteed"])
        self.assertFalse(v["inference_executed"])

    def test_exact_limit_and_exceeding_limit(self):
        self.assertEqual(validate(valid(neurons_used_today=9950, neurons_reserved=8),
                                  today=REVIEWED)["local_remaining_after"], 0)
        self.assertEqual(validate(valid(neurons_used_today=9951, neurons_reserved=8),
                                  today=REVIEWED)["status"], "BLOCK")

    def test_paid_or_unknown_models_rejected(self):
        for model in ["@cf/zai-org/glm-5.2",
                      "@cf/moonshotai/kimi-k2.6",
                      "@cf/deepseek-ai/deepseek-v4-pro-0813",
                      "@cf/unknown/model"]:
            with self.subTest(model=model):
                self.assertEqual(validate(valid(model=model), today=REVIEWED)["status"], "BLOCK")

    def test_stale_pricing_usage_and_plan_fail_closed(self):
        self.assertEqual(validate(valid(), today=REVIEWED + timedelta(days=31))["status"], "BLOCK")
        self.assertEqual(validate(valid(usage_day_utc="2026-11-12"), today=REVIEWED)["status"], "BLOCK")
        self.assertEqual(validate(valid(plan="paid"), today=REVIEWED)["status"], "BLOCK")

    def test_incorrect_numbers_and_unknown_inputs_fail_closed(self):
        for kwargs in [{"neurons_used_today": True}, {"neurons_reserved": -1},
                       {"output_tokens_upper_bound": 1.4},
                       {"input_tokens_upper_bound": 0},
                       {"neurons_used_today": 10001}]:
            self.assertEqual(validate(valid(**kwargs), today=REVIEWED)["status"], "BLOCK")
        self.assertEqual(validate([], today=REVIEWED)["status"], "BLOCK")

    def test_other_explicitly_free_models(self):
        for model in ["@cf/google/gemma-4-26b-a4b-it",
                      "@cf/nvidia/nemotron-3-120b-a12b"]:
            with self.subTest(model=model):
                self.assertEqual(validate(valid(model=model), today=REVIEWED)["status"],
                                 "LOCAL_BUDGET_ESTIMATE_ONLY_ACCOUNT_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
