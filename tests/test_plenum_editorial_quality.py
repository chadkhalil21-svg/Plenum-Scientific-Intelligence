"""Focused tests for source-level Humanizer and source-preserving editorial wiring."""
import json
from pathlib import Path
import unittest
from plenum_ai.agent_council import EDITORIAL_DIRECTIVE

ROOT=Path(__file__).resolve().parents[1]


class PlenumEditorialQualityTests(unittest.TestCase):
    def test_reviewed_original_vendor_skill_with_license_and_provenance(self):
        source=(ROOT/"skills/humanizer/SKILL.md").read_text(encoding="utf-8")
        license_text=(ROOT/"skills/humanizer/LICENSE").read_text(encoding="utf-8")
        notice=(ROOT/"skills/humanizer/UPSTREAM.md").read_text(encoding="utf-8")
        self.assertIn("name: humanizer",source)
        self.assertIn('version: "4.0.0"',source)
        self.assertIn("Copyright (c) 2025 Siqi Chen",license_text)
        self.assertIn("b48c832f0f809c1b5658edbb838c2521b72f2413",notice)
        self.assertIn("facts",source)

    def test_both_editorial_skills_reach_every_defined_profile(self):
        data=json.loads((ROOT/"integrations/hermes/roster.json").read_text())
        self.assertEqual(len(data["roles"]),11)
        for role in data["roles"]:
            with self.subTest(name=role["name"]):
                self.assertIn("humanizer",role["skill_ids"])
                self.assertIn("plenum-editorial-quality",role["skill_ids"])
        self.assertFalse(data["defaults"]["private_app_access"])
        self.assertFalse(data["defaults"]["auto_start_gateway"])

    def test_edited_council_and_existing_n8n_are_grounded(self):
        self.assertIn("names, financial values or uncertainty",EDITORIAL_DIRECTIVE)
        self.assertIn("source verification",EDITORIAL_DIRECTIVE)
        workflow=json.loads((ROOT/"integrations/n8n/plenum-business-workforce.json").read_text())
        self.assertFalse(workflow["active"])
        node=next(x for x in workflow["nodes"] if x["name"]=="Plenum Specialist Agent")
        system=node["parameters"]["options"]["systemMessage"]
        self.assertIn("EDITORIAL QUALITY",system)
        self.assertIn("preserving every source",system)
        self.assertIn("no private document standards",system)

    def test_company_policy_protects_scientific_and_legal_meaning(self):
        skill=(ROOT/"skills/plenum-editorial-quality/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scientific paper",skill)
        self.assertIn("operative",skill)
        self.assertIn("Apple HIG",skill)
        self.assertIn("Humanizer",skill)
        self.assertIn("private Google Drive",skill)


if __name__=="__main__":
    unittest.main()
