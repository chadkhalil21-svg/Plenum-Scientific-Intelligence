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
        self.assertEqual(len(EXACT_PUBLIC_ACCEPTANCE_GOALS), 2)
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

    def test_real_original_specialists_recover_after_transient_code_worker_failure(self):
        # Actual original Research output and code worker are executed.
        # Only the first code worker invocation is interrupted by a test shim.
        from unittest.mock import patch
        from plenum_ai.chief_team_mission import execute
        from plenum_ai.workforce_public_inbox import (
            run_issue as original_worker, parse_public_issue
        )
        objective = ("Survey official NOAA station metadata sources and "
                     "run existing Python station validator")
        event = {"action": "opened",
                 "repository": {"full_name": "chadkhalil21-svg/Plenum-Scientific-Intelligence"},
                 "issue": {"number": 1001, "user": {"login": "chadkhalil21-svg"},
                           "title": "[Plenum Chief] public mission",
                           "body": "PLENUM_CHIEF_PUBLIC_MISSION_V1\nobjective: " + objective}}
        title, publisher, url = DOMAIN_SOURCES["noaa_water_station_metadata"][0]
        records = [{"source": publisher, "title": title, "url": url,
                    "http_status": 200, "independently_quoted_page_text": False}]

        def interrupt_only_code(event, *, output_dir):
            if parse_public_issue(event)["kind"] == "public_program":
                raise RuntimeError("test-only first-invocation transient")
            return original_worker(event, output_dir=output_dir)

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("plenum_ai.chief_team_mission.run_issue",
                       side_effect=interrupt_only_code), patch(
                "plenum_ai.reviewed_domain_workers.official_source_records",
                return_value=records,
            ):
                first = execute(event, output_dir=root)
            self.assertEqual(first["status"], "BLOCKED_PARTIAL_TEAM")
            self.assertEqual(first["successfully_verified_workers"], 1)
            self.assertEqual(first["reused_prior_verified_workers"], 0)
            self.assertEqual(first["new_worker_invocations"], 2)
            self.assertTrue((root / "chief-checkpoint-1001.json").is_file())
            # Exercise the unmodified production agent and ORIGINAL saved
            # research; no second network read or invented precomputed code.
            second = execute(event, output_dir=root)
            self.assertEqual(second["status"], "VERIFIED_BOUNDED_TEAM")
            self.assertEqual(second["reused_prior_verified_workers"], 1)
            self.assertEqual(second["new_worker_invocations"], 1)
            self.assertTrue(second["founder_objective_verified"])
            self.assertEqual(second["bounded_founder_goal_evidence"]["status"],
                             "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE")
            self.assertTrue((root /
                "workers/public_program/retry-2/issue-1001/code/main.py").is_file())
            self.assertEqual(inspect_chief_report(second)["disposition"],
                             "VERIFIED_FULL_BOUNDED_PUBLIC_OBJECTIVE_NOT_GENERAL_AUTONOMY")


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
            # A later reporting retry must retain acceptance without repeating
            # either completed worker or its external source request.
            with patch("plenum_ai.chief_team_mission.run_issue",
                       side_effect=AssertionError("completed worker repeated")):
                resumed = execute(event, output_dir=root)
            self.assertEqual(resumed["new_worker_invocations"], 0)
            self.assertEqual(resumed["reused_prior_verified_workers"], 2)
            self.assertTrue(resumed["founder_objective_verified"])
            self.assertEqual(inspect_chief_report(resumed)["disposition"],
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
