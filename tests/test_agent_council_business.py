"""Business lenses reuse the original model runner and original council guards."""
from unittest import TestCase
from unittest.mock import patch
from plenum_ai import agent_council as council


class BusinessAdvisoryContractTests(TestCase):
    def test_business_agenda_selects_four_real_perspective_calls(self):
        objective = "Compare business advisory council structure and operating priorities"
        self.assertEqual(len(council.council_seats(objective)), 4)
        self.assertIs(council.council_seats(objective), council.BUSINESS_SEATS)
        self.assertIs(council.council_seats("Review research evidence"), council.SEATS)
        self.assertEqual({name for name, _ in council.BUSINESS_SEATS},
                         {"operations", "finance", "strategy", "governance"})
        event = {
            "action": "opened",
            "repository": {"full_name": council.REPO},
            "issue": {"number": 991, "title": council.TITLE,
                      "user": {"login": council.FOUNDER},
                      "body": council.MARKER + "\nobjective: " + objective},
        }
        with patch.dict("os.environ", {
            "PLENUM_EPHEMERAL_RUNNER": "confirmed",
            "PLENUM_COUNCIL_MODEL_URL": council.MODEL_URL,
        }), patch.object(council, "_ask_local", return_value=
                        "Public-only tentative recommendation; establish independently verifiable milestones.") as ask:
            report = council.deliberate(event)
        self.assertEqual(report["council_type"], "business_advisory")
        self.assertEqual([x["role"] for x in report["perspectives"]],
                         ["operations", "finance", "strategy", "governance"])
        self.assertEqual(ask.call_count, 6)
        self.assertTrue(report["founder_business_advisor_recommendation"])
        self.assertFalse(report["recommendation_verified_against_external_sources"])
        self.assertFalse(report["sources_independently_checked"])
        self.assertFalse(report["account_actions_executed"])
        self.assertFalse(report["next_steps_approved"])
