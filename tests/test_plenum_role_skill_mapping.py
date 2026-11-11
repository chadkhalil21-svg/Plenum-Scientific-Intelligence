import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
ROSTER=ROOT/"integrations/hermes/roster.json"

class PlenumSkillContract(unittest.TestCase):
    def test_eleven_profiles_and_skill_sources(self):
        x=json.loads(ROSTER.read_text())
        self.assertEqual(len(x["roles"]),11)
        self.assertFalse(x["defaults"]["private_app_access"])
        self.assertFalse(x["defaults"]["auto_start_gateway"])
        self.assertEqual(len({a["name"] for a in x["roles"]}),11)
        for role in x["roles"]:
            with self.subTest(role=role["name"]):
                self.assertTrue(role["skill_ids"])
                self.assertTrue(role["load_skills_on_demand"])
                if role["name"] in {"coding", "browser", "simulation", "verification"}:
                    self.assertNotIn("humanizer", role["skill_ids"])
                for slug in role["skill_ids"]:
                    content=(ROOT/"skills"/slug/"SKILL.md").read_text()
                    self.assertIn("name: "+slug,content)
        advisor=next(a for a in x["roles"] if a["name"]=="business_advisor")
        self.assertIn("plenum-business-advisor",advisor["skill_ids"])

    def test_preview_soul_includes_skills_without_creating_gateway(self):
        module_path=ROOT/"integrations/hermes/provision_profiles.py"
        spec=importlib.util.spec_from_file_location("plenum_hermes_profiles",module_path)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        adviser=module.inspect_roster()["business_advisor"]
        soul=module.build_soul(adviser)
        self.assertIn("plenum-business-advisor",soul)
        self.assertIn("does NOT automatically",soul)
        self.assertIn("no accounts",soul.lower())

if __name__=="__main__":
    unittest.main()
