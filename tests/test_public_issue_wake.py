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


    def test_existing_original_chief_multi_specialist_issue_is_allowlisted(self):
        original = issue(
            title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Survey public research sources and create a code validator"),
        )
        event = build_original_event(original, [])
        self.assertEqual(event["issue"]["number"], 789)
        self.assertEqual(event["issue"]["title"], original["title"])
        # A bot result from either original issue workflow OR signed wake
        # must block a repeated execution of the SAME issue.
        for marker in (
            "<!-- plenum-founder-chief-run:123:attempt:1 -->",
            "<!-- plenum-public-workforce-run:456 -->",
        ):
            comment = [{"user": {"login": "github-actions[bot]"}, "body": marker}]
            self.assertIsNone(build_original_event(original, comment))
            # Third-party comments are never trusted completion receipts.
            comment[0]["user"]["login"] = "untrusted-person"
            self.assertIsNotNone(build_original_event(original, comment))
        for bad in (
            issue(title="[Plenum Chief] public mission", body="free text"),
            issue(title="[Plenum Chief] public mission", user={"login": "outsider"},
                  body=original["body"]),
            issue(title="[Plenum Chief] public mission",
                  body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                        "objective: Sign into a private banking account and send email")),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises((ValueError, PermissionError)):
                    build_original_event(bad, [])

    def test_rewake_uses_exact_existing_chief_team_engine_once(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from plenum_ai import public_issue_wake as wake
        original = issue(
            title="[Plenum Chief] public mission",
            body=("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                  "objective: Survey public research sources and create a code validator"),
        )
        completed = {
            "status": "VERIFIED_BOUNDED_TEAM", "issue_number": 789,
            "executed_workers": 2, "independent_verified": True,
        }
        requests = []
        def fake_gh(url, token, *, body=None):
            requests.append((url, body))
            if url.endswith("/789"): return original
            if "comments?per_page" in url: return []
            if url.endswith("/comments"): return {"html_url": "https://github.com/safe#comment"}
            raise AssertionError("Unexpected resource")
        with tempfile.TemporaryDirectory() as folder, patch.object(
            wake, "gh_json", side_effect=fake_gh
        ), patch.object(
            wake, "execute_original_team", return_value=completed
        ) as team, patch.object(
            wake, "run_issue"
        ) as single, patch.dict("os.environ", {"GITHUB_RUN_ID":"123"}):
            result = wake.process(789, "scoped", Path(folder))
            self.assertEqual(result["status"], "VERIFIED_BOUNDED_TEAM")
            self.assertTrue(result["independent_verified"])
            self.assertTrue(result["original_multi_specialist"])
            self.assertTrue((Path(folder)/"chief-result-789.json").is_file())
            self.assertEqual(
                json.loads((Path(folder)/"chief-result-789.json").read_text())["executed_workers"], 2
            )
            self.assertEqual(team.call_count, 1)
            single.assert_not_called()
            self.assertIn("multi-specialist", requests[-1][1]["body"])
            self.assertNotIn("Survey public research", requests[-1][1]["body"])

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
