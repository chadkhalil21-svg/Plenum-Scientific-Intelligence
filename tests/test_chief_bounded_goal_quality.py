"""Validate original Chief acceptance without mistaking code CI for live owner work."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from unittest import TestCase

from plenum_ai.chief_team_mission import (
    EXACT_PUBLIC_ACCEPTANCE_GOALS, grade_complete_bounded_public_goal,
)
from plenum_ai.reviewed_domain_workers import DOMAIN_FILES, DOMAIN_SOURCES
from plenum_ai.ambient_quality_insights import inspect_chief_report


class RealBoundedFounderGoalVerifierTests(TestCase):
    OBJECTIVE = "Survey official Cloudflare Workers AI sources and run existing Python neuron budget validator"

    def test_every_declared_goal_routes_to_existing_two_specialists(self):
        from plenum_ai.chief_team_mission import independent_expected_team
        from plenum_ai.reviewed_domain_workers import match_original_capability
        self.assertEqual(len(EXACT_PUBLIC_ACCEPTANCE_GOALS), 3)
        for task, capability in EXACT_PUBLIC_ACCEPTANCE_GOALS.items():
            with self.subTest(task=task):
                self.assertEqual(
                    independent_expected_team(task),
                    ("public_research", "public_program"),
                )
                self.assertEqual(match_original_capability(task), capability)

    def original_artifacts(self, root):
        domain = EXACT_PUBLIC_ACCEPTANCE_GOALS[self.OBJECTIVE]
        public = root / "workers" / "public_research" / "workforce-public-1001.json"
        public.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            {"source": org, "title": title, "url": url,
             "http_status": 200, "independently_quoted_page_text": False}
            for title, org, url in DOMAIN_SOURCES[domain]
        ]
        public.write_text(json.dumps({
            "schema": "plenum-public-horizon-snapshot-v1",
            "topic": self.OBJECTIVE, "records": rows,
            "publisher_document_text_verified": False,
        }))
        program = root / "workers" / "public_program" / "issue-1001" / "code"
        program.mkdir(parents=True, exist_ok=True)
        code = DOMAIN_FILES[domain].read_bytes()
        (program / "main.py").write_bytes(code)
        (program / "test_generated.py").write_text("import unittest\n")
        (program / "manifest.json").write_text(json.dumps({
            "schema": "plenum-reviewable-program-v1",
            "kind": domain, "public_topic": self.OBJECTIVE,
            "functional_verifier_executed_and_passed": True,
            "main_sha256": sha256(code).hexdigest(),
            "generated_program_has_not_been_deployed": True,
            "human_code_review_required": True,
        }))
        return {
            "public_research": {"_artifact_path": public.relative_to(root).as_posix()},
            "public_program": {
                "_artifact_path": program.parent.relative_to(root).as_posix(),
                "actual_offline_functional_test_passed": True,
            },
        }, public, program

    def test_both_authorized_exact_goals_route_to_two_original_agents(self):
        from plenum_ai.chief_team_mission import parse_mission
        for objective in EXACT_PUBLIC_ACCEPTANCE_GOALS:
            event = {"action": "opened",
                     "repository": {"full_name": "chadkhalil21-svg/Plenum-Scientific-Intelligence"},
                     "issue": {
                         "number": 1001,
                         "user": {"login": "chadkhalil21-svg"},
                         "title": "[Plenum Chief] public mission",
                         "body": "PLENUM_CHIEF_PUBLIC_MISSION_V1\nobjective: " + objective,
                     }}
            with self.subTest(objective=objective):
                self.assertEqual(parse_mission(event)["team"],
                                 ("public_research", "public_program"))

    def test_real_existing_specialists_resume_after_one_controlled_first_run_failure(self):
        from unittest.mock import patch
        from plenum_ai.chief_team_mission import execute
        from plenum_ai.reviewed_domain_workers import DOMAIN_SOURCES
        objective = ("Survey NOAA station metadata sources and run existing "
                     "Python coastal validator recovery")
        event = {"action": "opened",
                 "repository": {"full_name": "chadkhalil21-svg/Plenum-Scientific-Intelligence"},
                 "issue": {"number": 1001, "user": {"login": "chadkhalil21-svg"},
                           "title": "[Plenum Chief] public mission",
                           "body": "PLENUM_CHIEF_PUBLIC_MISSION_V1\nobjective: " + objective}}
        title, publisher, url = DOMAIN_SOURCES["noaa_water_station_metadata"][0]
        source_records = [{"source": publisher, "title": title, "url": url,
                           "http_status": 200, "independently_quoted_page_text": False}]
        env = {"GITHUB_ACTIONS": "true",
               "GITHUB_REPOSITORY": "chadkhalil21-svg/Plenum-Scientific-Intelligence",
               "GITHUB_EVENT_NAME": "issues",
               "GITHUB_RUN_ATTEMPT": "1",
               "GITHUB_RUN_ID": "54321"}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch.dict("os.environ", env, clear=True), patch(
                "plenum_ai.reviewed_domain_workers.official_source_records",
                return_value=source_records,
            ):
                first = execute(event, output_dir=root)
            self.assertEqual(first["status"], "BLOCKED_PARTIAL_TEAM")
            self.assertEqual(first["successfully_verified_workers"], 1)
            self.assertEqual(first["reused_prior_verified_workers"], 0)
            self.assertEqual(first["new_worker_invocations"], 2)
            self.assertTrue((root / "chief-checkpoint-1001.json").is_file())
            with patch.dict("os.environ", {**env, "GITHUB_RUN_ATTEMPT": "2"}, clear=True):
                recovered = execute(event, output_dir=root)
            self.assertEqual(recovered["status"], "VERIFIED_BOUNDED_TEAM")
            self.assertEqual(recovered["reused_prior_verified_workers"], 1)
            self.assertEqual(recovered["new_worker_invocations"], 1)
            self.assertTrue(recovered["founder_objective_verified"])
            self.assertEqual(recovered["bounded_founder_goal_evidence"]["status"],
                             "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE")
            self.assertTrue((root /
                "workers/public_program/retry-2/issue-1001/code/main.py").is_file())
            self.assertEqual(inspect_chief_report(recovered)["disposition"],
                             "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE_NOT_GENERAL_AUTONOMY")

    def test_one_time_recovery_guard_is_exact_public_original_run_only(self):
        from unittest.mock import patch
        from plenum_ai.chief_team_mission import _one_time_live_public_recovery_probe
        mission = {"objective": "Survey NOAA station metadata sources and run existing Python coastal validator recovery"}
        verified_original = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "chadkhalil21-svg/Plenum-Scientific-Intelligence",
            "GITHUB_EVENT_NAME": "issues",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_RUN_ID": "1234567",
        }
        with patch.dict("os.environ", verified_original, clear=True):
            self.assertTrue(_one_time_live_public_recovery_probe(mission, "public_program"))
            self.assertFalse(_one_time_live_public_recovery_probe(mission, "public_research"))
            self.assertFalse(_one_time_live_public_recovery_probe(
                {"objective": self.OBJECTIVE}, "public_program"))
        with patch.dict("os.environ", {**verified_original, "GITHUB_RUN_ATTEMPT": "2"},
                        clear=True):
            self.assertFalse(_one_time_live_public_recovery_probe(mission, "public_program"))
        with patch.dict("os.environ", {**verified_original, "GITHUB_EVENT_NAME": "pull_request"},
                        clear=True):
            self.assertFalse(_one_time_live_public_recovery_probe(mission, "public_program"))

    def test_actual_original_chief_executes_both_workers_and_rejects_no_evidence(self):
        # Unlike synthetic manifests, this uses both real original workers,
        # the REAL output_artifact shapes, SHA checkpoint, and functional test.
        # The only stub is the outbound source GET, to avoid external network
        # and to isolate the precise original end-to-end artifact contract.
        from unittest.mock import patch
        from plenum_ai.chief_team_mission import execute
        objective = ("Survey official NOAA station metadata sources and "
                     "run existing Python station validator")
        event = {"action": "opened",
                 "repository": {"full_name": "chadkhalil21-svg/Plenum-Scientific-Intelligence"},
                 "issue": {"number": 1001,
                           "user": {"login": "chadkhalil21-svg"},
                           "title": "[Plenum Chief] public mission",
                           "body": "PLENUM_CHIEF_PUBLIC_MISSION_V1\nobjective: " + objective}}
        source = DOMAIN_SOURCES["noaa_water_station_metadata"][0]
        records = [{"title": source[0], "source": source[1], "url": source[2],
                    "http_status": 200, "independently_quoted_page_text": False}]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("plenum_ai.reviewed_domain_workers.official_source_records",
                       return_value=records):
                actual = execute(event, output_dir=root)
            self.assertEqual(actual["executed_workers"], 2)
            self.assertTrue(actual["worker_artifacts_technically_verified"])
            self.assertTrue(actual["founder_objective_verified"])
            self.assertEqual(actual["bounded_founder_goal_evidence"]["status"],
                             "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE")
            self.assertTrue((root / "workers/public_program/issue-1001/code/main.py").is_file())
            self.assertEqual(inspect_chief_report(actual)["disposition"],
                             "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE_NOT_GENERAL_AUTONOMY")

    def test_exact_goal_accepts_real_original_primary_source_and_functional_code(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            observed, _, _ = self.original_artifacts(root)
            result = grade_complete_bounded_public_goal(
                self.OBJECTIVE, ("public_research", "public_program"),
                observed, root, True,
                {"status": "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF",
                 "irrelevant_kinds": []},
            )
            self.assertEqual(result["status"], "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE")
            self.assertEqual(len(result["http_200_official_urls"]), 2)
            self.assertFalse(result["new_provider_account_or_paid_host_used"])
            self.assertIn("no website login", result["scope"])

    def test_never_promote_page_content_checks_or_unknown_objectives(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            observed, public, program = self.original_artifacts(root)
            base = ("public_research", "public_program")
            gate = {"irrelevant_kinds": []}
            inspect = lambda obj=self.OBJECTIVE: grade_complete_bounded_public_goal(
                obj, base, observed, root, True, gate,
            )["status"]
            self.assertEqual(inspect("Survey Cloudflare pricing facts and make a new AI model"),
                             "NOT_A_FULLY_GRADED_GOAL")
            raw = json.loads(public.read_text())
            raw["records"][0]["http_status"] = 403
            public.write_text(json.dumps(raw))
            self.assertEqual(inspect(), "NOT_A_FULLY_GRADED_GOAL")
            raw["records"][0]["http_status"] = 200
            public.write_text(json.dumps(raw))
            manifest = program / "manifest.json"
            value = json.loads(manifest.read_text())
            value["functional_verifier_executed_and_passed"] = False
            manifest.write_text(json.dumps(value))
            self.assertEqual(inspect(), "NOT_A_FULLY_GRADED_GOAL")

    def test_quality_check_grades_real_goal_and_handles_relevance_rejection(self):
        real = {
            "schema": "plenum-chief-founder-team-v2",
            "issue_number": 1001, "status": "VERIFIED_BOUNDED_TEAM",
            "worker_artifacts_technically_verified": True,
            "founder_objective_verified": True,
            "bounded_founder_goal_evidence": {
                "status": "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE"
            },
            "named_entity_evidence": "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF",
            "external_account_changes": False, "paid_api_used": False,
        }
        v = inspect_chief_report(real)
        self.assertEqual(
            v["disposition"],
            "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE_NOT_GENERAL_AUTONOMY",
        )
        self.assertEqual(v["findings"], [])
        real.update({
            "status": "BLOCKED_OBJECTIVE_RELEVANCE",
            "founder_objective_verified": False,
        })
        blocked = inspect_chief_report(real)
        self.assertEqual(blocked["disposition"],
                         "BLOCKED_OR_UNVERIFIED_DO_NOT_PROMOTE")
        self.assertIn("ORIGINAL_WORKFORCE_NOT_COMPLETED",
                      [x["code"] for x in blocked["findings"]])
