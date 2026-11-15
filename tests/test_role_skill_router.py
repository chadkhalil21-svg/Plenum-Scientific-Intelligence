"""Only new role-specific skill-routing behavior."""
import unittest
from plenum_ai.role_skill_router import route, _whole_term

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

    def test_openhands_724_review_preserves_whole_words_and_multiword_skills(self):
        # Real model proposal #724 used text.split(), incorrectly discarding
        # phrases such as "free local" and matching no punctuation boundaries.
        self.assertTrue(_whole_term("configure free local tooling", "free local"))
        self.assertTrue(_whole_term("audit:license, security", "license"))
        self.assertTrue(_whole_term("review last 30 days", "last 30"))
        self.assertFalse(_whole_term("presearch", "research"))
        self.assertFalse(_whole_term("rewrite", "write"))
        self.assertFalse(_whole_term("scarcity", "cash"))
        d = route("coding", "Configure free local inference with no purchased provider")
        self.assertIn("plenum-free-local-tools", d["selected_skills"])
        self.assertFalse(d["authorizes_new_tools"])
        q = route("business_advisor", "Examine hyperemail vocabulary for an unrelated strategy")
        self.assertNotIn("humanizer", q["selected_skills"])

    def test_unauthorized_role_and_unbounded_objective_rejected(self):
        with self.assertRaises(PermissionError):
            route("unlisted_executor","Research professional sources")
        with self.assertRaises(ValueError):
            route("research","x")

if __name__ == "__main__":
    unittest.main()
