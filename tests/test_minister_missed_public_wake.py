"""Original scheduled Minister never invents tasks or repeats bot results."""
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from urllib.error import URLError

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


def original_coder_issue(marker="PLENUM_OPENHANDS_PUBLIC_REPAIR_V1"):
    return issue(num=750, age=timedelta(days=1), title=m.CODER_TITLE,
                 body=(marker + "\nfile: src/plenum_ai/mission_checkpoint.py\n"
                       "objective: Reject oversized public artifact before opening file"))


def original_coder_receipt(headline="OpenHands original public repair",
                           status=m.CODER_STATUS, run_id=123456):
    return {"user": {"login": "github-actions[bot]"},
            "created_at": (NOW - timedelta(days=1)).isoformat(),
            "body": (f"<!-- plenum-openhands-review:{run_id}:attempt:1 -->\n"
                     f"**{headline}: {status}**\n")}


def original_coder_run():
    return {"id": 123456, "event": "issues", "workflow_id": m.CODER_WORKFLOW_ID,
            "path": m.CODER_WORKFLOW, "display_title": m.CODER_TITLE,
            "head_branch": "main", "status": "completed", "conclusion": "failure",
            "run_attempt": 1, "repository": {"full_name": m.REPO, "id": 1447724141},
            "actor": {"login": m.OWNER, "id": 251133044},
            "created_at": (NOW - timedelta(days=1)).isoformat()}


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

    def test_coder_quota_recovery_never_ignores_another_engine_receipt(self):
        cloud_issue = original_coder_issue()
        receipt = original_coder_receipt()
        self.assertEqual(m.free_coder_nextday_candidate(cloud_issue, [receipt], NOW), 123456)
        local_receipt = original_coder_receipt("Aider local original public repair",
                                               "BLOCKED_NO_REVIEWABLE_PATCH", 654321)
        self.assertIsNone(m.free_coder_nextday_candidate(cloud_issue, [receipt, local_receipt], NOW))
        local_issue = original_coder_issue("PLENUM_AIDER_LOCAL_PUBLIC_REPAIR_V1")
        self.assertIsNone(m.free_coder_nextday_candidate(local_issue, [receipt], NOW))
        fallback = {**receipt, "body": receipt["body"] + "Local fallback attempted: true\n"}
        self.assertIsNone(m.free_coder_nextday_candidate(cloud_issue, [fallback], NOW))
        self.assertIsNone(m.free_coder_nextday_candidate({**cloud_issue, "state": "closed"}, [receipt], NOW))

    def test_lost_native_coder_rerun_response_keeps_one_durable_reservation(self):
        for failure in (TimeoutError("lost response"), URLError(TimeoutError("lost response"))):
            with self.subTest(failure=failure):
                task = original_coder_issue()
                comments = [original_coder_receipt()]
                posts = []

                def api(url, token, *, method="GET", payload=None):
                    if "/issues?" in url:
                        return [task]
                    if "/comments?per_page" in url:
                        return comments
                    if url.endswith("/actions/runs/123456"):
                        return original_coder_run()
                    if url.endswith("/comments") and method == "POST":
                        comments.append({"user": {"login": "github-actions[bot]"}, "body": payload["body"]})
                        posts.append("reserve")
                        return {"id": 987}
                    if url.endswith("/rerun") and method == "POST":
                        posts.append("rerun")
                        raise failure
                    raise AssertionError(url)

                with patch.object(m, "request_json", side_effect=api):
                    first = m.resume_missed_public_issues(token="ephemeral", now=NOW)
                    second = m.resume_missed_public_issues(token="ephemeral", now=NOW)
                self.assertEqual(posts, ["reserve", "rerun"])
                self.assertEqual(first["status"], "AMBIGUOUS_ORIGINAL_CODER_RERUN_RESERVED_NO_RETRY")
                self.assertEqual(first["original_coder_recovery"]["issue_number"], 750)
                self.assertFalse(first["original_coder_recovery"]["requested"])
                self.assertFalse(first["mission_completion_claimed"])
                self.assertIsNone(second["original_coder_recovery"])

    def test_unreceipted_coding_run_reserves_once_and_spoofed_receipt_cannot_hide_terminal(self):
        task = original_coder_issue()
        event = {"action": "opened", "repository": {"full_name": m.REPO},
                 "sender": {"login": m.OWNER}, "issue": task}
        spoof = {**original_coder_receipt(), "user": {"login": "visitor"}}
        comments = [spoof]
        posts = []

        def api(url, token, *, method="GET", payload=None):
            if url.endswith("/issues/750"):
                return {**task, "comments": len(comments)}
            if url.endswith("/comments?per_page=100"):
                return comments
            if url.endswith("/comments") and method == "POST":
                posts.append(payload["body"])
                reply = {"user": {"login": "github-actions[bot]"},
                         "body": payload["body"], "html_url": "https://github.com/example"}
                comments.append(reply)
                return reply
            if "/issues?" in url:
                return [task]
            raise AssertionError(url)

        with patch.object(m, "request_json", side_effect=api):
            self.assertTrue(m.reserve_native_coder(event, "ephemeral",
                                                  run_id=123456, attempt=1, now=NOW))
            self.assertFalse(m.reserve_native_coder(event, "ephemeral",
                                                   run_id=987654, attempt=1, now=NOW))
            self.assertFalse(m.reserve_native_coder(event, "ephemeral",
                                                   run_id=123456, attempt=2, now=NOW))
            sweep = m.resume_missed_public_issues(token="ephemeral", now=NOW)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].splitlines()[0], m._coder_execution_marker(123456, 1))
        self.assertFalse(m.has_original_coder_terminal_receipt(comments, 123456, 1))
        self.assertEqual(sweep["status"], "CODER_TERMINAL_RECEIPT_PENDING_NO_REPLAY")
        self.assertEqual(sweep["original_coder_awaiting_authentic_terminal_receipt_no_replay"], [750])
        self.assertIsNone(sweep["original_coder_recovery"])
        self.assertTrue(m.has_original_coder_terminal_receipt(
            comments + [original_coder_receipt()], 123456, 1))
        legacy = {"user": {"login": "github-actions[bot]"},
                  "body": "<!-- plenum-openhands-review:123456 -->"}
        self.assertTrue(m.has_original_coder_terminal_receipt([legacy], 123456, 1))
        self.assertFalse(m.has_original_coder_terminal_receipt([legacy], 123456, 2))

    def test_native_coder_attempt_two_needs_exact_post_reset_reservation_and_prior_run(self):
        task = original_coder_issue()
        event = {"action": "opened", "repository": {"full_name": m.REPO},
                 "sender": {"login": m.OWNER}, "issue": task}
        terminal = original_coder_receipt()
        first = {"user": {"login": "github-actions[bot]"},
                 "body": m._coder_execution_marker(123456, 1)}
        nextday = {"user": {"login": "github-actions[bot]"},
                   "body": f"{m.CODER_RESERVATION}750:123456 -->"}
        comments = [first, terminal]
        provider = original_coder_run()
        posts = []

        def api(url, token, *, method="GET", payload=None):
            if url.endswith("/issues/750"):
                return {**task, "comments": len(comments)}
            if url.endswith("/comments?per_page=100"):
                return comments
            if url.endswith("/actions/runs/123456/attempts/1"):
                return provider
            if url.endswith("/comments") and method == "POST":
                posts.append(payload["body"])
                reply = {"user": {"login": "github-actions[bot]"},
                         "body": payload["body"], "html_url": "https://github.com/example"}
                comments.append(reply)
                return reply
            raise AssertionError(url)

        with patch.object(m, "request_json", side_effect=api):
            self.assertFalse(m.reserve_native_coder(event, "ephemeral",
                                                   run_id=123456, attempt=2, now=NOW))
            comments.append(nextday)
            provider["run_attempt"] = 2
            self.assertFalse(m.reserve_native_coder(event, "ephemeral",
                                                   run_id=123456, attempt=2, now=NOW))
            provider["run_attempt"] = 1
            terminal["body"] += "Gemini fallback attempted: true\n"
            self.assertFalse(m.reserve_native_coder(event, "ephemeral",
                                                   run_id=123456, attempt=2, now=NOW))
            terminal["body"] = original_coder_receipt()["body"]
            self.assertTrue(m.reserve_native_coder(event, "ephemeral",
                                                  run_id=123456, attempt=2, now=NOW))
            self.assertFalse(m.reserve_native_coder(event, "ephemeral",
                                                   run_id=123456, attempt=2, now=NOW))
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].splitlines()[0], m._coder_execution_marker(123456, 2))


if __name__ == "__main__":
    unittest.main()

