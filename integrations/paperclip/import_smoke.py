"""Offline import/entrypoint gate; no network, secrets or inference."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
ROLES = {"chief", "research", "coding", "browser", "creative", "marketing",
         "operations", "simulation", "support", "verification", "business_advisor"}


class ImportGate(unittest.TestCase):
    def test_all_eleven_profiles(self):
        from plenum_ai.role_skill_router import route
        roster = json.loads((ROOT / "integrations/hermes/roster.json").read_text())
        self.assertEqual({row["name"] for row in roster["roles"]}, ROLES)
        self.assertEqual(len(roster["roles"]), 11)
        for role in sorted(ROLES):
            with self.subTest(role=role):
                receipt = route(role, "Review public evidence and verify the task output")
                self.assertEqual(receipt["role"], role)
                self.assertTrue(receipt["selected_skills"])
                self.assertFalse(receipt["model_or_agent_started"])
                print("PROFILE PASS", role)

    def test_all_five_divisions_and_entrypoints(self):
        for name in ("acceptance", "division_adapter", "five_division_acceptance"):
            module = importlib.import_module(name)
            self.assertIsNotNone(module)
            print("ENTRYPOINT IMPORT PASS", name)
        from division_adapter import SPECS, public_worker
        self.assertEqual(set(SPECS), {"research", "engineering", "commercial", "intelligence", "verification"})
        for name in ("chief_contract_plan", "chief_team_mission", "workforce_team_dispatch",
                     "reviewed_domain_workers", "world_horizon", "business_public_watch",
                     "ambient_quality_insights", "public_issue_wake"):
            importlib.import_module("plenum_ai." + name)
        self.assertTrue(callable(public_worker))
        # Exercise the actual existing engineering routine through the same
        # entrypoint used by Paperclip; no live provider or model needed.
        proof = public_worker("engineering")
        self.assertIs(proof["functional_verifier_executed_and_passed"], True)
        for role in sorted(SPECS):
            print("DIVISION IMPORT PASS", role)
        print("ENGINEERING ENTRYPOINT FUNCTIONAL PASS", proof["main_sha256"])

    def test_memory_import_and_ci_boundary(self):
        from plenum_ai.owner_private_memory_client import PrivateMemoryClient, PrivateMemoryUnavailable
        from unittest.mock import patch
        with patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
            with self.assertRaises(PrivateMemoryUnavailable):
                PrivateMemoryClient(secret="x" * 32)
        result = subprocess.run(["node", "--input-type=module", "-e",
            "const m=await import('./integrations/cloudflare/plenum-github-wake-worker.mjs');"
            "if(typeof m.PrivateContinuityMemory!=='function'||typeof m.default.fetch!=='function') process.exit(1);"
            "console.log('CLOUDFLARE WORKER + MEMORY IMPORT PASS')"],
            cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        print(result.stdout.strip())
        print("PRIVATE MEMORY CI ACCESS DENIED PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
