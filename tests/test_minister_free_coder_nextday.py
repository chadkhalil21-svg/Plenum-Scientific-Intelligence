"""Only real original signed issue runs may retry once after UTC quota reset.

Focused source regression; no model, cloud quota, or external account calls.
"""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from plenum_ai import minister_missed_public_wake as m

NOW = datetime(2026, 11, 16, 0, 22, tzinfo=timezone.utc)
RUN_ID = 43668940080
ISSUE = {
    "number": 812, "state": "open", "title": m.CODER_TITLE,
    "user": {"login": "chadkhalil21-svg"},
    "body": "PLENUM_OPENHANDS_PUBLIC_REPAIR_V1\n"
            "file: src/plenum_ai/agent_library.py\n"
            "objective: Reject unsupported registry records before acceptance",
}
RECEIPT = {
    "user": {"login": "github-actions[bot]"},
    "created_at": "2026-11-15T02:44:44Z",
    "body": ("<!-- plenum-openhands-review:43668940080:attempt:1 -->\n"
             "**OpenHands original public repair: "
             "BLOCKED_LOCAL_FREE_AI_DAILY_CAP_NO_SAME_DAY_RETRY**\n"
             "Evidence from original actions runner only."),
}
RUN = {
    "id": RUN_ID, "event": "issues", "workflow_id": m.CODER_WORKFLOW_ID,
    "path": m.CODER_WORKFLOW, "display_title": m.CODER_TITLE,
    "head_branch": "main", "status": "completed", "conclusion": "failure",
    "run_attempt": 1, "repository": {"full_name": m.REPO, "id": 1447724141},
    "actor": {"login": m.OWNER, "id": 251133044},
    "created_at": "2026-11-15T02:41:17Z",
}


class OriginalFreeCoderNextDayRecovery(unittest.TestCase):
    def test_exact_real_cap_receipt_no_same_day_or_repeat(self):
        with patch("plenum_ai.openhands_coding_agent.parse_owner_repair_event",
                   return_value={"source_file": "src/plenum_ai/agent_library.py"}):
            self.assertEqual(m.free_coder_nextday_candidate(
                ISSUE, [RECEIPT], NOW), RUN_ID)
            self.assertIsNone(m.free_coder_nextday_candidate(
                ISSUE, [RECEIPT],
                datetime(2026, 11, 15, 23, 59, tzinfo=timezone.utc)))
            self.assertIsNone(m.free_coder_nextday_candidate(
                ISSUE, [RECEIPT, {
                    **RECEIPT,
                    "body": "<!-- plenum-minister-nextday-free-coder:812:43668940080 -->",
                }], NOW))
            self.assertIsNone(m.free_coder_nextday_candidate(
                ISSUE, [{**RECEIPT, "user": {"login": "untrusted"}}], NOW))
            self.assertIsNone(m.free_coder_nextday_candidate(
                ISSUE, [{**RECEIPT, "body": RECEIPT["body"].replace(
                    "attempt:1", "attempt:2")}], NOW))
            self.assertIsNone(m.free_coder_nextday_candidate(
                ISSUE, [{**RECEIPT, "body": RECEIPT["body"].replace(
                    m.CODER_STATUS, "REVIEW_ONLY_PATCH_READY_NOT_MERGED")}], NOW))
            self.assertIsNone(m.free_coder_nextday_candidate(
                {**ISSUE, "state": "closed"}, [RECEIPT], NOW))

    def test_original_minister_reserves_before_one_native_rerun(self):
        calls = []
        def api(url, token, *, method="GET", payload=None):
            calls.append((url, method, payload))
            if "/comments?per_page" in url:
                return [RECEIPT]
            if url.endswith("/actions/runs/" + str(RUN_ID)):
                return dict(RUN)
            if url.endswith("/comments") or url.endswith("/rerun"):
                return None
            raise AssertionError("Unexpected API: " + url)
        with (patch("plenum_ai.openhands_coding_agent.parse_owner_repair_event",
                    return_value={"source_file": "src/plenum_ai/agent_library.py"}),
              patch.object(m, "request_json", side_effect=api)):
            result = m.recover_one_post_reset_original_coder(
                items=[ISSUE], token="ephemeral", now=NOW)
        self.assertTrue(result["requested"])
        self.assertEqual(result["issue_number"], 812)
        self.assertEqual(result["run_id"], RUN_ID)
        posts = [x for x in calls if x[1] == "POST"]
        self.assertEqual(len(posts), 2)
        self.assertTrue(posts[0][0].endswith("/issues/812/comments"))
        self.assertIn("plenum-minister-nextday-free-coder:812:43668940080",
                      posts[0][2]["body"])
        self.assertTrue(posts[1][0].endswith("/actions/runs/43668940080/rerun"))

    def test_reject_wrong_run_identity_without_dispatch(self):
        posts = []
        def api(url, token, *, method="GET", payload=None):
            if method == "POST":
                posts.append(url)
                return None
            if "/comments?per_page" in url:
                return [RECEIPT]
            if "/actions/runs/" in url:
                return {**RUN, "actor": {"login": "intruder", "id": 1}}
            raise AssertionError(url)
        with (patch("plenum_ai.openhands_coding_agent.parse_owner_repair_event",
                    return_value={"source_file": "src/plenum_ai/agent_library.py"}),
              patch.object(m, "request_json", side_effect=api)):
            self.assertIsNone(m.recover_one_post_reset_original_coder(
                items=[ISSUE], token="ephemeral", now=NOW))
        self.assertEqual(posts, [])


if __name__ == "__main__":
    unittest.main()
