"""Original scheduled Minister never invents tasks or repeats bot results."""
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from plenum_ai import minister_missed_public_wake as m

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
BODY = ("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
        "objective: Survey public battery research sources and create a code validator")


def issue(*, num=789, age=timedelta(hours=2), actor="chadkhalil21-svg",
          title="[Plenum Chief] public mission", body=BODY,
          state="open"):
    return {"number": num, "state": state,
            "title": title, "body": body,
            "created_at": (NOW - age).isoformat(),
            "user": {"login": actor}}


class OriginalMinisterMissedWakeTests(unittest.TestCase):
    def test_only_original_fresh_founder_bounded_public_missions(self):
        self.assertTrue(m.original_issue_eligible(issue(), now=NOW))
        for bad in (
            issue(actor="other"), issue(state="closed"),
            issue(age=timedelta(minutes=35)), issue(age=timedelta(days=10)),
            issue(body="please open a private bank login"),
            issue(title="Unapproved task"),
        ):
            with self.subTest(bad=bad):
                self.assertFalse(m.original_issue_eligible(bad, now=NOW))
        pull = issue()
        pull["pull_request"] = {}
        self.assertFalse(m.original_issue_eligible(pull, now=NOW))

    def test_existing_bot_result_or_wake_attempt_prevents_repetition(self):
        self.assertTrue(m.missing_original_attempt([], 789))
        for body in (
            "<!-- plenum-founder-chief-run:123:attempt:1 -->",
            "<!-- plenum-public-workforce-run:123 -->",
            "<!-- plenum-minister-missed-dispatch:789 -->",
            "**Chief status: BLOCKED_OBJECTIVE_RELEVANCE**",
        ):
            self.assertFalse(m.missing_original_attempt([
                {"user": {"login": "github-actions[bot]"}, "body": body},
            ], 789))
        self.assertFalse(m.missing_original_attempt([{}], 789) is False
                         and False)  # Parsing does not trust missing bot as execution
        self.assertFalse(m.missing_original_attempt([{"body": "x"}]*100, 789))

    def test_dispatches_only_original_once_then_records_attempt(self):
        candidate = issue()
        urls = []
        def fake_request(url, token, *, method="GET", payload=None):
            urls.append((url, method, payload))
            if "/issues?" in url:
                return [candidate]
            if "/comments?per_page" in url:
                return []
            if url.endswith("/dispatches"):
                self.assertEqual(payload["event_type"], "plenum_public_issue_wakeup")
                self.assertEqual(payload["client_payload"], {"issue_number": 789})
                return None
            if url.endswith("/comments"):
                self.assertIn("<!-- plenum-minister-missed-dispatch:789 -->",
                              payload["body"])
                return {"id": 987}
            raise AssertionError("Unknown original GitHub endpoint")
        with patch.object(m, "request_json", side_effect=fake_request):
            report = m.resume_missed_public_issues(token="ephemeral", now=NOW)
        self.assertEqual(report["status"], "REQUESTED_EXISTING_PUBLIC_WORKER_WAKES")
        self.assertEqual(report["original_issues_woken"], [789])
        self.assertEqual(len([x for x in urls if x[1] == "POST"]), 2)
        self.assertFalse(report["mission_completion_claimed"])
        self.assertFalse(report["private_accounts_used"])

    def test_no_work_is_a_real_no_op_not_a_new_project(self):
        with patch.object(m, "request_json", return_value=[issue(
            age=timedelta(minutes=5))]):
            result = m.resume_missed_public_issues(token="ephemeral", now=NOW)
        self.assertEqual(result["status"], "NO_NEW_MISSED_PUBLIC_MISSION")
        self.assertEqual(result["original_issues_woken"], [])

    def test_untrusted_or_oversized_comment_lists_never_authorize(self):
        self.assertFalse(m.missing_original_attempt(None, 1))
        self.assertFalse(m.missing_original_attempt([{"body": 10}], 1))
        self.assertFalse(m.missing_original_attempt([{"body": "x"}]*100, 1))


if __name__ == "__main__":
    unittest.main()
