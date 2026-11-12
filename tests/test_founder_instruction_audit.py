"""Focused checks for *new* founder-instruction acceptance gate, no network."""
import unittest
import io
import json
from unittest.mock import patch

from plenum_ai import founder_instruction_audit as a


def objective(scope, pr=None, issue=None):
    return {
        "id":"sample", "owner_role":"verification",
        "acceptance_scope":scope,"pr":pr,"issue":issue,
        "priority":1,"remaining_action":"Obtain genuine owner-approved result",
        "public_objective_summary":"Verify one source"
    }


class FounderInstructionAuditTests(unittest.TestCase):
    def test_original_github_read_does_not_truncate_large_valid_comment_json(self):
        from plenum_ai.weekly_founder_brief import github_json, REPO
        big = json.dumps({"body": "x" * 181000}).encode("utf-8")
        with patch("plenum_ai.weekly_founder_brief.urlopen", return_value=io.BytesIO(big)):
            result = github_json(
                "https://api.github.com/repos/" + REPO + "/issues/432/comments",
                "redacted-test-only",
            )
        self.assertEqual(len(result["body"]), 181000)

    def test_all_user_abstracts_have_owners_and_no_false_complete_history(self):
        doc=a.load_coverage()
        self.assertFalse(doc["complete_reconstruction"])
        self.assertEqual(doc["founder_instructions_count"],31)
        self.assertEqual(len({x["id"] for x in doc["requirements"]}),31)
        self.assertTrue(all(x.get("owner_role") for x in doc["requirements"]))
        self.assertFalse(any(x["private_chat_transcript_read"] for x in doc["requirements"]))

    def test_public_git_source_merge_does_not_mark_live_host(self):
        task=objective("external_live",pr=454,issue=384)
        report=a.evidence_for(task,pulls={454:{"merged":True}},comments={384:[]})
        self.assertEqual(report["status"],"OPEN_LIVE_ACCEPTANCE_MISSING")
        self.assertFalse(report["live_account_operation_verified"])

    def test_only_real_merged_source_is_accepted_as_source(self):
        t=objective("source_only",pr=459)
        self.assertEqual(a.evidence_for(t,pulls={459:{"merged":False}},comments={})["status"],
                         "OPEN_NO_VERIFIED_MERGE")
        self.assertEqual(a.evidence_for(t,pulls={459:{"merged":True}},comments={})["status"],
                         "ACCEPTED_SOURCE_MERGE_ONLY")

    def test_only_original_bot_chief_completed_narrow_public_execution(self):
        t=objective("narrow_public_worker",issue=456)
        message={"body":"<!-- plenum-founder-chief-run:example -->\nChief status: VERIFIED_CHIEF_DELEGATION specialist_executed=True"}
        outsider={**message,"user":{"login":"random"}}
        allowed={**message,"user":{"login":"github-actions[bot]"}}
        self.assertEqual(a.evidence_for(t,pulls={},comments={456:[outsider]})["status"],
                         "OPEN_NO_VERIFIED_AGENT_RUN")
        self.assertEqual(a.evidence_for(t,pulls={},comments={456:[allowed]})["status"],
                         "LIMITED_REAL_WORKER_EXECUTED")

    def test_council_draft_is_not_private_operations_or_external_fact_check(self):
        t=objective("partial",issue=457)
        comment={"user":{"login":"github-actions[bot]"},
                 "body":"Plenum council status: ADVISORY_DELIBERATION_AWAITING_FOUNDER\nIndependent model perspectives completed: 4/4."}
        x=a.evidence_for(t,pulls={},comments={457:[comment]})
        self.assertEqual(x["status"],"PARTIAL_ADVISORY_RAN_NOT_COMPLETE")

    def test_render_keeps_open_requests_visible_and_never_promises_chat_access(self):
        doc=a.load_coverage()
        rows=[a.evidence_for(t,pulls={448:{"merged":True},454:{"merged":True},
                                        459:{"merged":True}},comments={})
              for t in doc["requirements"]]
        report=a.render(rows,as_of_date="2026-11-11",doc=doc)
        self.assertIn("partial reconstruction",report)
        self.assertIn("plenum-founder-instruction-audit:2026-11-11",report)
        self.assertIn("OPEN_LIVE_ACCEPTANCE_MISSING",report)
        self.assertIn("prompts",report.lower())
        self.assertNotIn("all tasks completed",report.lower())
        changed = [dict(x) for x in rows]
        changed[0]["status"] = "OPEN_LIVE_ACCEPTANCE_MISSING"
        changed_report = a.render(changed, as_of_date="2026-11-11", doc=doc)
        self.assertNotEqual(report.splitlines()[0], changed_report.splitlines()[0])
        self.assertEqual(report.splitlines()[0], a.render(rows, as_of_date="2026-11-11", doc=doc).splitlines()[0])


if __name__=="__main__":
    unittest.main()
