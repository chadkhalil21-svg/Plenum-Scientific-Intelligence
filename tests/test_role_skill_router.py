"""Only new role-specific skill-routing behavior."""
import unittest
from plenum_ai.role_skill_router import route

class PlenumRoleRoutingTests(unittest.TestCase):
    def test_specialist_does_not_inherit_full_humanizer(self):
        for role in ("coding","browser","simulation","verification","research","operations"):
            with self.subTest(role=role):
                d=route(role,"Write a natural technical email proposal for public research")
                self.assertNotIn("humanizer",d["selected_skills"])
                self.assertFalse(d["model_or_agent_started"])
                self.assertFalse(d["authorizes_new_tools"])

    def test_text_roles_can_load_humanizer_when_relevant_only(self):
        d=route("business_advisor","Polish natural email recommendation for founder")
        self.assertIn("humanizer",d["selected_skills"])
        self.assertIn("plenum-business-advisor",d["selected_skills"])
        self.assertFalse(d["every_skill_loaded"])
        q=route("business_advisor","Evaluate business strategy and return next decision")
        self.assertNotIn("humanizer",q["selected_skills"])

    def test_researcher_keeps_separate_research_domain(self):
        d=route("research","Research YouTube source videos on free agent hosting")
        self.assertIn("plenum-research-youtube",d["selected_skills"])
        self.assertNotIn("plenum-coding-delivery",d["selected_skills"])

    def test_original_model_patch_review_preserves_multiword_and_rejects_substrings(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            roster = Path(folder) / "roster.json"
            def pick(skills, objective):
                roster.write_text(json.dumps({
                    "schema": "plenum-hermes-profile-roster-v1",
                    "roles": [{"name": "bounded", "skill_ids": skills}],
                }), encoding="utf-8")
                return route("bounded", objective, roster_path=roster)

            # Real OpenHands #724 proposed text.split(), which would FAIL
            # these genuine pre-existing multiword skill triggers.
            self.assertEqual(
                pick(["plenum-finance-operations", "plenum-free-local-tools"],
                     "Inspect free local inference options")["selected_skills"][0],
                "plenum-free-local-tools")
            # A substring may not appoint an unrelated specialist.
            self.assertEqual(
                pick(["plenum-finance-operations", "plenum-growth-sales"],
                     "Investigate presales opportunities")["selected_skills"][0],
                "plenum-finance-operations")
            self.assertEqual(
                pick(["plenum-finance-operations", "plenum-growth-sales"],
                     "Investigate sales opportunities")["selected_skills"][0],
                "plenum-growth-sales")
            # Writing/editorial permissions must also use exact words.
            self.assertNotIn(
                "plenum-editorial-quality",
                pick(["plenum-business-advisor", "plenum-editorial-quality"],
                     "Investigate writeups for reporting")["selected_skills"])
            self.assertIn(
                "plenum-editorial-quality",
                pick(["plenum-business-advisor", "plenum-editorial-quality"],
                     "Write a public proposal")["selected_skills"])

    def test_unauthorized_role_and_unbounded_objective_rejected(self):
        with self.assertRaises(PermissionError):
            route("unlisted_executor","Research professional sources")
        with self.assertRaises(ValueError):
            route("research","x")

if __name__ == "__main__":
    unittest.main()
