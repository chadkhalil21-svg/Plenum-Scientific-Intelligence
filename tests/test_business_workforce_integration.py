"""No-model integration contracts: no paid API, external writes, or n8n server."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from plenum_ai import openhands_coding_agent as coder

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "integrations/n8n/plenum-business-workforce.json"


class BusinessWorkforceContractTest(unittest.TestCase):
    def test_openhands_plan_does_not_invoke_model(self):
        result = coder.plan()
        self.assertEqual(result["status"], "CONFIGURATION_ONLY")
        self.assertFalse(result["model_run_completed"])
        self.assertFalse(result["production_written"])
        self.assertTrue(result["human_review_required"])

    def test_rejects_unbounded_or_external_output_paths(self):
        for path in ("/tmp/x.json", "../secret.json", "reports/../../a.json", "plan.json"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    coder._output_path(path)
        self.assertEqual(str(coder._output_path("reports/coder.json")), "reports/coder.json")

    def test_openhands_cannot_run_without_isolated_runner(self):
        with patch.dict("os.environ", {"PLENUM_EPHEMERAL_RUNNER": ""}):
            with self.assertRaisesRegex(RuntimeError, "isolated ephemeral"):
                coder.execute()

    def test_n8n_importable_draft_only_workflow(self):
        flow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
        self.assertFalse(flow["active"])
        kinds = {n["type"] for n in flow["nodes"]}
        self.assertIn("n8n-nodes-base.manualTrigger", kinds)
        self.assertIn("@n8n/n8n-nodes-langchain.agent", kinds)
        self.assertIn("@n8n/n8n-nodes-langchain.lmChatOllama", kinds)
        self.assertIn("@n8n/n8n-nodes-langchain.toolCalculator", kinds)
        self.assertNotIn("n8n-nodes-base.webhook", kinds)
        self.assertNotIn("@n8n/n8n-nodes-langchain.chatTrigger", kinds)
        self.assertFalse(any("credentials" in n for n in flow["nodes"]))
        names = {n["name"] for n in flow["nodes"]}
        self.assertEqual(len(names), len(flow["nodes"]))
        self.assertIn("Founder Review Queue", names)
        assignments = next(n for n in flow["nodes"] if n["name"] == "Assign Nine Roles")
        script = assignments["parameters"]["jsCode"]
        self.assertEqual(script.count('["'), 9)
        self.assertIn("rubric:rubrics[role]", script)
        self.assertIn("NEEDS_VERIFICATION", script)
        self.assertIn("Do not claim", next(n for n in flow["nodes"] if n["name"] == "Plenum Specialist Agent")["parameters"]["options"]["systemMessage"])
        for role in ("research", "engineering", "browser", "creative", "marketing",
                     "operations", "simulation", "support", "verification"):
            self.assertIn('["' + role + '"', script)
        review = next(n for n in flow["nodes"] if n["name"] == "Founder Review Queue")
        self.assertIn("DRAFT_AWAITING_FOUNDER_REVIEW", review["parameters"]["jsCode"])
        self.assertIn("quality_rubric", review["parameters"]["jsCode"])
        self.assertIn("external_actions_executed: false", review["parameters"]["jsCode"])
        self.assertEqual(len(flow["connections"]), 5)


if __name__ == "__main__":
    unittest.main()
