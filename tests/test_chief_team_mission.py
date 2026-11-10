"""Multi-specialist mission contract: real original tool routes, no new supervisor."""
from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch
from pathlib import Path

from plenum_ai.chief_team_mission import (
    MISSION_MAGIC, MISSION_TITLE, independent_expected_team,
    independently_accept_team, parse_mission, preflight, execute,
)
from plenum_ai.chief_workforce_command import KIND_TO_AGENT, worker_event
from plenum_ai.workforce_public_inbox import parse_public_issue

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"


def mission(objective="Survey public research sources and create a data validator program",
            actor=OWNER, issue_number=1001, title=MISSION_TITLE, body=None):
    return {
        "action": "opened", "repository": {"full_name": REPO},
        "issue": {
            "number": issue_number, "title": title,
            "user": {"login": actor},
            "body": body if body is not None else
                MISSION_MAGIC + "\nobjective: " + objective,
        },
    }


class ChiefTeamMissionTests(TestCase):
    def test_founder_carries_two_real_original_worker_kinds(self):
        e = mission()
        parsed = parse_mission(e)
        self.assertEqual(parsed["team"], ("public_research", "public_program"))
        self.assertEqual(preflight(e)["expected_team"], list(parsed["team"]))
        for kind in parsed["team"]:
            routed = worker_event(parsed["legacy_event"], kind)
            self.assertEqual(parse_public_issue(routed)["kind"], kind)
            self.assertEqual(routed["issue"]["number"], 1001)

    def test_two_other_approved_actual_artifact_kinds(self):
        e = mission("Create a public data validator program and an original SVG illustration")
        self.assertEqual(parse_mission(e)["team"], ("public_program", "public_creative"))
        e = mission("Survey public research sources and calculate known thermal numerical model")
        self.assertEqual(parse_mission(e)["team"], ("public_research", "public_science"))

    def test_exact_founder_policy_and_sensitive_rejection(self):
        blocked = [
            mission(actor="someone-else"),
            mission(title="[Plenum Chief] public assignment"),
            mission(body=MISSION_MAGIC+"\nobjective: too short"),
            mission(body=MISSION_MAGIC+"\nobjective: Deploy program with private password"),
            mission(body=MISSION_MAGIC+"\nobjective: Survey research sources\npermission: all"),
            mission(issue_number=0),
            {**mission(), "repository":{"full_name":"another/repo"}},
            {**mission(), "action":"edited"},
        ]
        for e in blocked:
            with self.subTest(e=str(e)[:70]), self.assertRaises((ValueError, PermissionError)):
                parse_mission(e)
        with self.assertRaises(ValueError):
            independent_expected_team("Survey public research sources only")
        with self.assertRaises(ValueError):
            independent_expected_team("Survey sources, create code, simulate thermal model, and draw SVG")

    def test_independent_verifier_requires_distinct_genuine_outcomes(self):
        kinds = ("public_program", "public_creative")
        roles = [KIND_TO_AGENT[k] for k in kinds]
        actual = {k: {"status":"DRAFT_READY_FOR_FOUNDER", "verified":True} for k in kinds}
        self.assertTrue(independently_accept_team(kinds, roles, actual, 2))
        self.assertTrue(independently_accept_team(kinds, roles+roles[:1], actual, 3))
        self.assertFalse(independently_accept_team(kinds, roles[:1], actual, 1))
        self.assertFalse(independently_accept_team(kinds, roles+["research-specialist"], actual, 3))
        self.assertFalse(independently_accept_team(kinds, roles, {kinds[0]:actual[kinds[0]]}, 2))
        actual[kinds[1]] = {"status":"BLOCKED_WORKER_OR_VERIFICATION","verified":False}
        self.assertFalse(independently_accept_team(kinds, roles, actual, 2))

    def test_execution_fails_closed_without_real_runner(self):
        with patch.dict("os.environ", {
            "PLENUM_EPHEMERAL_RUNNER":"", "PLENUM_CHIEF_MODEL_URL":"http://127.0.0.1:11434",
        }):
            with self.assertRaises(PermissionError):
                execute(mission(), output_dir=Path("reports/workforce-chief"))


if __name__ == "__main__":
    import unittest
    unittest.main()
