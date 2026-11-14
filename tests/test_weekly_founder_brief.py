"""Focused test for the NEW public weekly minister report, no network or model."""
import unittest
from plenum_ai import weekly_founder_brief as b


class WeeklyPublicEvidenceTests(unittest.TestCase):
    def test_statuses_are_from_comments_not_inferred_from_open_issue(self):
        self.assertEqual(b.verified_comment_status([]), "NO_VERIFIED_RESULT_IN_COMMENTS")
        self.assertEqual(b.verified_comment_status([{"body": "Status: **DRAFT_READY_FOR_FOUNDER**"}]), "DRAFT_READY_FOR_FOUNDER")
        self.assertEqual(b.verified_comment_status([{"body": "**Chief status: VERIFIED_BOUNDED_TEAM**"}]), "VERIFIED_BOUNDED_TEAM")
        self.assertEqual(b.verified_comment_status([{"body": "**Overall: BLOCKED_UPSTREAM_CAPTIONS**"}]), "BLOCKED_UPSTREAM_CAPTIONS")

    def test_brief_lists_all_original_dependencies_without_claiming_host(self):
        rows = [{"number": n, "state": "open", "status": "NO_VERIFIED_RESULT_IN_COMMENTS"}
                for n, _ in b.ISSUES]
        report = b.render_brief(rows, as_of_date="2026-11-11")
        self.assertIn("Minister of Operations", report)
        self.assertIn("Six-video Research Engineering Verification receipt", report)
        self.assertIn("Cloudflare signed wake and private memory (bounded accepted)", report)
        self.assertIn("Scientific evidence reconciliation (original repair accepted)", report)
        self.assertEqual(report.count("https://github.com/" + b.REPO + "/issues/"), len(b.ISSUES))
        self.assertIn("FOUNDER OVERRIDE (14 Nov 2026)", report)
        self.assertIn("custom Plenum browser #310 is RETIRED", report)
        self.assertIn("original scientific evidence reconciliation #482", report.lower())
        self.assertIn("FOUNDER HOST DECISION (14 Nov 2026)", report)
        self.assertNotIn("Persistent host #384 is still UNVERIFIED", report)
        self.assertNotIn("Verify a real owner-approved signed-in website task", report)
        self.assertNotIn("Route specific research-memory continuity schema fault", report)
        self.assertIn("not established as live private persistent services", report)
        self.assertIn("plenum-weekly-public-operating-brief:2026-11-11", report)
        # Closed issue is not necessarily completed: the founder retired #310.
        modified = [dict(x) for x in rows]
        for item in modified:
            if item["number"] == 310:
                item["state"] = "closed"
                item["state_reason"] = "not_planned"
        updated = b.render_brief(modified, as_of_date="2026-11-14")
        self.assertIn("issue **closed (not_planned)**", updated)
        self.assertNotIn("browser #310; source/CI alone cannot close", updated)
        with self.assertRaises(ValueError):
            b.render_brief(rows[:2], as_of_date="2026-11-11")
