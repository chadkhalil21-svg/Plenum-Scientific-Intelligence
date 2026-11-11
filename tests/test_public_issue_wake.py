"""Focused no-network proof: only original founder issue can wake, exactly once."""
import unittest
from plenum_ai.public_issue_wake import build_original_event, checked_issue_number

def issue(**kwargs):
    data={
        "number":789, "state":"open", "title":"[Plenum Workforce] public research",
        "body":"PLENUM_PUBLIC_WORKFORCE_V2\nkind: public_research\nobjective: Review source quality for Plenum repository",
        "user":{"login":"chadkhalil21-svg"}
    }
    data.update(kwargs)
    return data

class PublicWakeAcceptance(unittest.TestCase):
    def test_existing_public_founder_issue_allowed(self):
        e=build_original_event(issue(),[])
        self.assertEqual(e["issue"]["number"],789)

    def test_already_handled_public_issue_is_not_rerun(self):
        comments=[{"user":{"login":"github-actions[bot]"},
                   "body":"<!-- plenum-public-workforce-run:123 -->\nStatus: **DRAFT_READY_FOR_FOUNDER**."}]
        self.assertIsNone(build_original_event(issue(),comments))
        # Third-party comments may never claim GitHub Actions completion.
        comments[0]["user"]["login"]="outsider"
        self.assertIsNotNone(build_original_event(issue(),comments))

    def test_closed_untrusted_or_unbounded_issues_rejected(self):
        for bad in (issue(state="closed"),issue(user={"login":"attacker"}),
                    issue(title="misc"),issue(body="free text"),
                    issue(pull_request={"url":"none"})):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError,PermissionError)):
                    build_original_event(bad,[])
        with self.assertRaises(ValueError):
            build_original_event(issue(),[{}]*100)
        for value in (-1,0,1000000000,True,"45"):
            with self.assertRaises(ValueError):
                checked_issue_number(value)

if __name__=="__main__":
    unittest.main()
