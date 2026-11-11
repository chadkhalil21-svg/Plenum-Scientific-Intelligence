"""Focused test for the NEW public weekly minister report, no network or model."""
import unittest
from plenum_ai import weekly_founder_brief as b


class WeeklyPublicEvidenceTests(unittest.TestCase):
    def test_statuses_are_from_comments_not_inferred_from_open_issue(self):
        self.assertEqual(b.verified_comment_status([]), "NO_VERIFIED_RESULT_IN_COMMENTS")
        self.assertEqual(b.verified_comment_status([{"body": "Status: **DRAFT_READY_FOR_FOUNDER**"}]), "DRAFT_READY_FOR_FOUNDER")
        self.assertEqual(b.verified_comment_status([{"body": "**Chief status: VERIFIED_BOUNDED_TEAM**"}]), "VERIFIED_BOUNDED_TEAM")

    def test_brief_lists_all_original_dependencies_without_claiming_host(self):
        rows = [{"number": n, "state": "open", "status": "NO_VERIFIED_RESULT_IN_COMMENTS"}
                for n, _ in b.ISSUES]
        report = b.render_brief(rows, as_of_date="2026-11-11")
        self.assertIn("Minister of Operations", report)
        self.assertEqual(report.count("https://github.com/" + b.REPO + "/issues/"), len(b.ISSUES))
        self.assertIn("not independently established as live", report)
        self.assertIn("plenum-weekly-public-operating-brief:2026-11-11", report)
        with self.assertRaises(ValueError):
            b.render_brief(rows[:2], as_of_date="2026-11-11")
