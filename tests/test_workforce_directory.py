"""Only the changed directory contract; no repeated model or hosting smoke tests."""
from unittest import TestCase
from plenum_ai.workforce_directory import build_directory, format_chart


class WorkforceDirectoryTests(TestCase):
    def test_five_logical_divisions_without_inflating_agent_count(self):
        report = build_directory()
        self.assertEqual(report["workforce_count"], 5)
        self.assertEqual(report["named_profile_definitions"], 10)
        self.assertIsNone(report["named_profiles_confirmed_running"])
        self.assertTrue(report["group_count_is_not_running_agent_count"])
        self.assertEqual(len({g["id"] for g in report["groups"]}), 5)
        self.assertIn("Global Intelligence", format_chart(report))
        self.assertIn("Verification & Advisory Council", format_chart(report))

    def test_business_advisory_spans_existing_divisions_and_has_no_private_access(self):
        report = build_directory()
        self.assertEqual(report["chief_role"], "chief")
        self.assertIn("Minister of Operations", report["chief_proposed_display_title"])
        advisory = report["business_advisory"]
        self.assertEqual(advisory["owner_divisions"], ["commercial_operations", "verification_council"])
        self.assertFalse(advisory["private_account_access"])
        self.assertTrue(all(
            m["named_hermes_profile"] for group in report["groups"] for m in group["members"]
        ))
