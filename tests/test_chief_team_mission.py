"""No-model, PUBLIC founder team dispatch: independently check ACTUAL old tools."""
from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from plenum_ai.chief_team_mission import (
    MISSION_MAGIC, MISSION_TITLE, independent_expected_team,
    independently_accept_team, parse_mission, preflight, execute,
)
from plenum_ai.chief_workforce_command import worker_event
from plenum_ai.workforce_public_inbox import parse_public_issue

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"


def mission(objective="Survey public research sources and create a data validator program",
            actor=OWNER, issue_number=1001, title=MISSION_TITLE, body=None):
    return {
        "action": "opened", "repository": {"full_name": REPO},
        "issue": {
            "number": issue_number, "title": title, "user": {"login": actor},
            "body": body if body is not None else
                MISSION_MAGIC + "\nobjective: " + objective,
        },
    }


class ChiefTeamMissionTests(TestCase):
    def test_founder_can_route_only_distinct_existing_tools(self):
        e = mission()
        parsed = parse_mission(e)
        self.assertEqual(parsed["team"], ("public_research", "public_program"))
        self.assertEqual(preflight(e)["expected_team"], list(parsed["team"]))
        self.assertFalse(preflight(e)["model_called"])
        for kind in parsed["team"]:
            self.assertEqual(
                parse_public_issue(worker_event(parsed["original"], kind))["kind"], kind
            )

    def test_founder_team_identifies_relevant_free_upstream_without_inference(self):
        task=mission("Survey public battery sources and create a code validator")
        with patch("urllib.request.urlopen", side_effect=AssertionError("No network allowed")):
            report=preflight(task)
        self.assertEqual(report["expected_team"],["public_research","public_program"])
        self.assertIn("pybamm",[x["id"] for x in report["candidate_sources"]])
        self.assertFalse(report["model_called"])
        self.assertEqual(report["source_selection_inference_calls"],0)
        self.assertEqual(report["upstream_sources_installed"],0)
        self.assertEqual(report["new_external_models_started"],0)
        self.assertTrue(all(x["activation"]=="SOURCE_REFERENCE_ONLY_NOT_INSTALLED"
                            and x["additional_paid_services_enabled"] is False
                            for x in report["candidate_sources"]))

    def test_second_pair_and_three_roles(self):
        e = mission("Create a public data validator program and an original SVG illustration")
        self.assertEqual(parse_mission(e)["team"], ("public_program", "public_creative"))
        e = mission("Survey sources, create code validator, and draw an original SVG map")
        self.assertEqual(parse_mission(e)["team"],
                         ("public_research", "public_program", "public_creative"))
        with self.assertRaises(ValueError):
            independent_expected_team("Survey public research sources only")
        with self.assertRaises(ValueError):
            independent_expected_team("Survey sources, create code, simulate thermal, draw SVG")

    def test_exact_public_founder_identity_and_sensitivity(self):
        blocked = [
            mission(actor="someone-else"),
            mission(title="[Plenum Chief] public assignment"),
            mission(body=MISSION_MAGIC+"\nobjective: too short"),
            mission(body=MISSION_MAGIC+"\nobjective: Deploy program with private password"),
            mission(body=MISSION_MAGIC+"\nobjective: Survey research sources\npermission: all"),
            mission(issue_number=0),
            {**mission(), "repository": {"full_name":"someone-else/repo"}},
            {**mission(), "action":"edited"},
        ]
        for e in blocked:
            with self.subTest(e=str(e)[:60]), self.assertRaises((ValueError, PermissionError)):
                parse_mission(e)

    def test_actual_distinct_worker_outputs_recovered_and_verified_without_llm(self):
        e = mission("Create a public data validator program and an original SVG illustration")
        calls = []
        def actual_public_worker(event, *, output_dir):
            task = parse_public_issue(event)
            calls.append((task["kind"], output_dir))
            return {
                "status":"DRAFT_READY_FOR_FOUNDER", "verified":True,
                "worker":task["worker"], "verified_scope":"syntactic artifact check",
                "output_artifact":"issue-1001/code" if task["kind"] == "public_program" else "issue-1001/creative",
            }
        with tempfile.TemporaryDirectory() as d, patch(
            "plenum_ai.chief_team_mission.run_issue", side_effect=actual_public_worker
        ):
            outcome = execute(e, output_dir=Path(d))
        self.assertEqual(outcome["status"], "VERIFIED_BOUNDED_TEAM")
        self.assertEqual(outcome["executed_workers"], 2)
        self.assertEqual(outcome["successfully_verified_workers"], 2)
        self.assertTrue(outcome["independent_verified"])
        self.assertFalse(outcome["model_called"])
        self.assertFalse(outcome["chief_model_delegated"])
        self.assertEqual([x[0] for x in calls], ["public_program","public_creative"])
        self.assertEqual(len(set(str(x[1]) for x in calls)), 2)
        self.assertEqual(len(outcome["worker_results"]), 2)
        self.assertTrue(all(x["output_artifact"].startswith("workers/") for x in outcome["worker_results"]))

    def test_failure_is_explicit_and_other_worker_preserved(self):
        e = mission("Create a public data validator program and an original SVG illustration")
        def worker(event, *, output_dir):
            t = parse_public_issue(event)
            if t["kind"] == "public_program":
                raise RuntimeError("syntactic error")
            return {"status":"DRAFT_READY_FOR_FOUNDER","verified":True,
                    "worker":t["worker"],"output_artifact":"issue-1001/creative"}
        with tempfile.TemporaryDirectory() as d, patch(
            "plenum_ai.chief_team_mission.run_issue", side_effect=worker
        ):
            result = execute(e, output_dir=Path(d))
        self.assertEqual(result["status"], "BLOCKED_PARTIAL_TEAM")
        self.assertFalse(result["independent_verified"])
        self.assertEqual(result["successfully_verified_workers"], 1)
        self.assertEqual(result["worker_results"][0]["failure_type"],"RuntimeError")
        self.assertEqual(result["worker_results"][1]["status"],"DRAFT_READY_FOR_FOUNDER")

    def test_verifier_rejects_missing_workers_or_unverified_artifacts(self):
        expected = ("public_program","public_creative")
        ok = {
            kind: {"status":"DRAFT_READY_FOR_FOUNDER","verified":True,
                   "worker":"existing_original","output_artifact":"issue-1001"}
            for kind in expected
        }
        self.assertTrue(independently_accept_team(expected,ok))
        self.assertFalse(independently_accept_team(expected,{"public_program":ok["public_program"]}))
        self.assertFalse(independently_accept_team(expected,{**ok,"public_research":ok["public_program"]}))
        self.assertFalse(independently_accept_team(expected,{**ok,"public_creative":{**ok["public_creative"],"verified":False}}))


if __name__ == "__main__":
    import unittest
    unittest.main()
