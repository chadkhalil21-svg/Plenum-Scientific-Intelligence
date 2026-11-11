"""One focused audit of founder source registry, role-scoped skills and council facts."""
from pathlib import Path
import json
import unittest
from plenum_ai import agent_council

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"integrations/workforces/founder_all_tools_registry.json"

class FounderCatalogContract(unittest.TestCase):
    def test_complete_deduplicated_free_first_registry(self):
        d=json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(d["schema"],"plenum-founder-all-tools-registry-v1")
        self.assertEqual(len(d["items"]),81)
        self.assertEqual(len({x["key"] for x in d["items"]}),81)
        self.assertEqual(len(d["videos"]),4)
        self.assertEqual(len(d["screenshot_requested_milestones"]),5)
        self.assertFalse(d["summary"]["installed_all"])
        self.assertFalse(d["summary"]["video_transcripts_verified"])
        self.assertTrue(d["summary"]["no_new_spend_authorized"])
        self.assertTrue(all(not x["private_account_rights_granted"] for x in d["items"]))
        names={x["name"]:x for x in d["items"]}
        self.assertIn("UNVERIFIED",names["Google AQuA"]["adoption_status"])
        self.assertIn("PAID",names["Airia"]["adoption_status"])
        self.assertIn("QUOTA",names["Freebuff"]["adoption_status"])
        self.assertIn("SOURCE_READY",names["Cloudflare Workers Free"]["adoption_status"])

    def test_role_approved_specific_skills_exist(self):
        roster=json.loads((ROOT/"integrations/hermes/roster.json").read_text(encoding="utf-8"))
        union=set()
        for role in roster["roles"]:
            union.update(role["skill_ids"])
            self.assertTrue(role["load_skills_on_demand"])
        for name in ("plenum-platform-adoption","plenum-recency-research",
                     "plenum-design-audit","plenum-local-media"):
            self.assertIn(name,union)
            text=(ROOT/"skills"/name/"SKILL.md").read_text(encoding="utf-8")
            self.assertIn("name: "+name,text)
        self.assertNotIn("plenum-local-media",
            next(x for x in roster["roles"] if x["name"]=="verification")["skill_ids"])

    def test_original_council_uses_only_bounded_source_facts_on_demand(self):
        decisions=agent_council.read_public_tool_adoption_context(
            "Evaluate free specialist software tools")
        self.assertIn("not 81 installations",decisions)
        self.assertIn("Google AQuA=IDENTITY_UNVERIFIED",decisions)
        self.assertIn("Airia=PAID_DEFER",decisions)
        self.assertEqual(agent_council.read_public_tool_adoption_context(
            "Assess independent scientific predictions"),"")

    def test_readable_master_ledger_and_owner_gate(self):
        doc=(ROOT/"docs/PLENUM_FOUNDER_PLATFORM_ADOPTION_LEDGER.md").read_text(encoding="utf-8")
        self.assertIn("81 tools",doc)
        self.assertIn("Google AQuA",doc)
        self.assertIn("Cloudflare",doc)
        self.assertIn("founder_all_tools_registry.json",doc)
        self.assertIn("NOT established",doc)

if __name__=="__main__":
    unittest.main()
