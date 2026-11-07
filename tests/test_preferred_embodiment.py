"""Prevent the project registry from reverting to pre-integration screenshot statuses."""
import json
from pathlib import Path
import unittest
from plenum_ai.tool_registry import TOOLS, PARALLEL_TOOLS, approve_request

ROOT = Path(__file__).resolve().parents[1]

class PreferredEmbodimentTests(unittest.TestCase):
    def test_key_statuses_are_true_to_verified_evidence(self):
        spec=json.loads((ROOT/"protocols/prometheus_preferred_embodiment.json").read_text())
        self.assertEqual(spec["schema"], "plenum-preferred-embodiment-v1")
        self.assertIs(spec["AGI_demonstrated"], False)
        for key,evidence in spec["registry_evidence"].items():
            with self.subTest(key=key):
                self.assertEqual(TOOLS[key].status,evidence["status"])
                self.assertTrue(evidence["url"].startswith(
                    "https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/"))
                self.assertNotIn(key,PARALLEL_TOOLS)
                with self.assertRaises(ValueError):
                    approve_request([key])

    def test_preferred_embodiment_has_one_controller_and_no_false_deployments(self):
        spec=json.loads((ROOT/"protocols/prometheus_preferred_embodiment.json").read_text())
        architecture=spec["architecture"]
        self.assertEqual(architecture["orchestrator"]["primary"],"LangGraph")
        self.assertFalse(architecture["inference"]["execution_verified"])
        self.assertFalse(architecture["deployment"]["private_always_on_service_verified"])
        self.assertFalse(architecture["literature"]["reliable_end_to_end_citations_verified"])
        self.assertFalse(architecture["coding"]["real_external_repair_verified"])
        self.assertFalse(architecture["memory"]["private_production_deployed"])
        self.assertFalse(architecture["interface"]["operational"])
        self.assertTrue(spec["policy"]["do_not_install_every_candidate"])
        self.assertTrue(spec["policy"]["approval_required_for_paid_compute"])

    def test_optional_dependencies_reuse_existing_upstream(self):
        src=(ROOT/"pyproject.toml").read_text()
        for pin in ("langgraph==1.2.20","inspect-ai==0.3.287",
                    "paper-qa==2026.8.12","openhands-sdk==1.60.1",
                    "livekit-agents==1.8.9"):
            self.assertIn(pin,src)
        self.assertTrue((ROOT/"formal/PlenumFormal/ResearchAccounting.lean").exists())

if __name__ == "__main__":
    unittest.main()
