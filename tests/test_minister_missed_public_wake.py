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
        self.assertTrue(m.missing_original_attempt([{}], 789))  # no trusted bot attempt
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

    def test_legacy_backlog_needs_exact_founder_approval_on_same_issue(self):
        historical = issue(num=498, age=timedelta(days=4))
        historical["created_at"] = "2026-11-11T20:38:55Z"
        historical["body"] = ("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                             "objective: Research free documentary sources and original SVG music illustration for Plenum Terra")
        historical["comments"] = 1
        self.assertFalse(m.original_issue_eligible(historical, now=NOW))
        self.assertTrue(m.original_issue_eligible(
            historical, now=NOW, legacy_approved=True))
        founder = {"user": {"login": m.OWNER},
                   "body": m.LEGACY_OWNER_APPROVAL + "\nScope: existing public mission only"}
        outsider = {**founder, "user": {"login": "untrusted"}}
        self.assertTrue(m.approved_legacy_public_backlog(
            historical, [founder], now=NOW))
        self.assertFalse(m.approved_legacy_public_backlog(
            historical, [outsider], now=NOW))
        self.assertFalse(m.approved_legacy_public_backlog(
            historical, [founder, founder], now=NOW))
        closed = {**historical, "state": "closed"}
        self.assertFalse(m.approved_legacy_public_backlog(
            closed, [founder], now=NOW))

    def test_owner_approved_old_task_is_self_selected_once_and_reserved_before_wake(self):
        historical = issue(num=498, age=timedelta(days=4))
        historical["created_at"] = "2026-11-11T20:38:55Z"
        historical["body"] = ("PLENUM_CHIEF_PUBLIC_MISSION_V1\n"
                             "objective: Research free documentary sources and original SVG music illustration for Plenum Terra")
        historical["comments"] = 1
        approval = {"user": {"login": m.OWNER},
                    "body": m.LEGACY_OWNER_APPROVAL + "\nNo private data"}
        calls = []
        def api(url, token, *, method="GET", payload=None):
            calls.append((url, method, payload))
            if "/issues?" in url:
                return [historical]
            if "/comments?per_page" in url:
                return [approval]
            if url.endswith("/comments"):
                return {"id": 999}
            if url.endswith("/dispatches"):
                return None
            raise AssertionError(url)
        with patch.object(m, "request_json", side_effect=api):
            result = m.resume_missed_public_issues(token="ephemeral", now=NOW)
        self.assertEqual(result["original_issues_woken"], [498])
        posted = [x for x in calls if x[1] == "POST"]
        self.assertEqual(len(posted), 2)
        self.assertTrue(posted[0][0].endswith("/issues/498/comments"))
        self.assertIn("plenum-minister-missed-dispatch:498",
                      posted[0][2]["body"])
        self.assertTrue(posted[1][0].endswith("/dispatches"))

    def test_unknown_dispatch_result_never_happens_before_reservation(self):
        task = issue()
        calls = []
        def api(url, token, *, method="GET", payload=None):
            calls.append((url, method))
            if "/issues?" in url:
                return [task]
            if "/comments?per_page" in url:
                return []
            if url.endswith("/comments"):
                return {"id": 999}
            if url.endswith("/dispatches"):
                raise RuntimeError("ambiguous GitHub dispatch")
            raise AssertionError(url)
        with patch.object(m, "request_json", side_effect=api):
            with self.assertRaisesRegex(RuntimeError, "ambiguous"):
                m.resume_missed_public_issues(token="ephemeral", now=NOW)
        self.assertEqual([u for u, method in calls if method == "POST"],
                         [m.API + "/issues/789/comments", m.API + "/dispatches"])

    def test_no_work_is_a_real_no_op_not_a_new_project(self):
        with patch.object(m, "request_json", return_value=[issue(
            age=timedelta(minutes=5))]):
            result = m.resume_missed_public_issues(token="ephemeral", now=NOW)
        self.assertEqual(result["status"], "NO_NEW_MISSED_PUBLIC_MISSION")
        self.assertEqual(result["original_issues_woken"], [])

    def test_lost_dispatch_response_preserves_reservation_and_other_work(self):
        # GitHub may accept the first POST even when its response is lost.
        # A second issue can proceed, but the first must never be retried.
        candidates = [issue(num=n) for n in (789, 790, 791)]
        reserved = {}
        sent = []

        def api(url, token, *, method="GET", payload=None):
            if "/issues?" in url:
                return candidates
            if "/comments?per_page" in url:
                number = int(url.split("/issues/")[1].split("/")[0])
                return reserved.get(number, [])
            if url.endswith("/comments"):
                number = int(url.split("/issues/")[1].split("/")[0])
                reserved[number] = [{"user": {"login": "github-actions[bot]"},
                                     "body": payload["body"]}]
                return {"id": number}
            if url.endswith("/dispatches"):
                number = payload["client_payload"]["issue_number"]
                self.assertIn(number, reserved)
                sent.append(number)
                if number == 789:
                    raise TimeoutError("response lost")
                return None
            raise AssertionError(url)

        with patch.object(m, "request_json", side_effect=api):
            first = m.resume_missed_public_issues(token="ephemeral", now=NOW)
            self.assertEqual(first["original_issues_woken"], [790])
            self.assertEqual(first["ambiguous_dispatch_issues"], [789])
            self.assertFalse(first["mission_completion_claimed"])
            self.assertEqual(sent, [789, 790])  # reservation counts against cap
            second = m.resume_missed_public_issues(token="ephemeral", now=NOW)
        self.assertEqual(second["original_issues_woken"], [791])
        self.assertEqual(sent, [789, 790, 791])

    def test_untrusted_or_oversized_comment_lists_never_authorize(self):
        self.assertFalse(m.missing_original_attempt(None, 1))
        self.assertFalse(m.missing_original_attempt([{"body": 10}], 1))
        self.assertFalse(m.missing_original_attempt([{"body": "x"}]*100, 1))


if __name__ == "__main__":
    unittest.main()

