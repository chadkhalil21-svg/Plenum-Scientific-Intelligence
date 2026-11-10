"""Source-only policies for five shared Plenum divisions and Oracle candidate."""
from __future__ import annotations

import json
from pathlib import Path
import re
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "integrations/workforces/five-workforces.json"
COMPOSE = ROOT / "deploy/oracle-always-free/compose.yaml"
ENV = ROOT / "deploy/oracle-always-free/.env.example"


class FiveWorkforceContractTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_five_distinct_divisions_have_actual_capability_status(self):
        expected = {
            "scientific_research", "engineering_manufacturing",
            "commercial_operations", "global_intelligence",
            "verification_council",
        }
        teams = self.registry["workforces"]
        self.assertEqual({team["id"] for team in teams}, expected)
        self.assertEqual(len(teams), len(expected))
        self.assertEqual(self.registry["default_cost_ceiling_usd"], 0)
        for team in teams:
            self.assertTrue(team["roles"])
            self.assertTrue(team["state"])
            self.assertTrue(team["runtime"])
            self.assertEqual(team["private_integrations"], "blocked_pending_owner_scope")
            self.assertEqual(len(team["public_kinds"]), len(set(team["public_kinds"])))
            self.assertTrue(set(team["public_kinds"]).issubset({
                "public_research", "public_program", "public_science",
                "public_creative",
            }))
        self.assertEqual(
            next(x for x in teams if x["id"] == "commercial_operations")["public_kinds"], []
        )

    def test_catalogues_stay_dormant_and_not_mislabeled_live_agents(self):
        catalog = self.registry["catalogues"]
        self.assertEqual([(item["items"], item["status"]) for item in catalog], [
            (283, "indexed_idle"), (1106, "metadata_only"),
        ])
        self.assertIn("not yet provisioned", self.registry["hosting_candidate"])
        self.assertIn("No OCI provisioning", self.registry["rules"]["deployment"])

    def test_source_registry_reuses_existing_five_workforces_without_paid_defaults(self):
        pointer=self.registry["free_first_capability_registry"]
        self.assertGreaterEqual(pointer["registered_reusable_sources"],27)
        self.assertFalse(pointer["automatic_install_or_execution"])
        self.assertEqual(pointer["selection_inference_calls"],0)
        self.assertTrue(pointer["no_silent_paid_api_or_model_provisioning"])
        self.assertEqual(pointer["relative_path"],"../agent-catalog/upstream-sources.json")
        source=ROOT/"integrations/workforces"/pointer["relative_path"]
        d=json.loads(source.resolve().read_text())
        self.assertEqual(len(d["entries"]),pointer["registered_reusable_sources"])
        self.assertEqual(len(self.registry["workforces"]),5)
        self.assertIn("GitHub terms",self.registry["rules"]["github_usage"])

    def test_oracle_compose_has_loopback_only_editor_and_private_model(self):
        txt = COMPOSE.read_text(encoding="utf-8")
        self.assertIn('127.0.0.1:5678:5678', txt)
        self.assertNotIn("0.0.0.0:5678", txt)
        self.assertNotRegex(txt, r"(?m)^\\s+- [\"']?11434:11434")
        self.assertIn("N8N_ENCRYPTION_KEY", txt)
        self.assertIn("private_workforce", txt)
        self.assertIn("n8n_owner_data", txt)
        self.assertIn("ollama_models", txt)
        self.assertIn('OLLAMA_NUM_PARALLEL: "1"', txt)
        self.assertNotIn("GH_TOKEN", txt)
        self.assertNotIn("STRIPE_", txt)
        env = ENV.read_text(encoding="utf-8")
        self.assertIn("REPLACE_WITH_OWNER_GENERATED_RANDOM_KEY", env)
        self.assertNotIn("sk-", env)

    def test_existing_workers_and_n8n_workflow_reused(self):
        self.assertTrue((ROOT / "src/plenum_ai/chief_team_mission.py").exists())
        self.assertTrue((ROOT / "integrations/n8n/plenum-business-workforce.json").exists())
        self.assertTrue((ROOT / "src/plenum_ai/agent_library.py").exists())
        self.assertTrue((ROOT / "src/plenum_ai/agent_council.py").exists())
