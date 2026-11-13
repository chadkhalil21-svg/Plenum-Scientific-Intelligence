"""Task-relevant original source & actual real first-party capability integration.

Exercises original pre-existing public research, Program Foundry and Chief
together. The fake HTTP transport only isolates external network; the real
already-reviewed Cloudflare/NOAA CLI and generated offline tests actually run.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from plenum_ai.reviewed_domain_workers import (
    DOMAIN_SOURCES, match_original_capability,
    official_source_records, reuse_original_program,
)
from plenum_ai.workforce_public_inbox import run_issue
from plenum_ai.chief_team_mission import execute, MISSION_MAGIC, MISSION_TITLE

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OBJECTIVE = ("Survey public Cloudflare Workers AI free tier sources "
             "and create a Python inference usage validator")
NOAA = "Survey public NOAA station metadata and create a Python validator"


def event(objective=OBJECTIVE, *, kind="public_research", chief=False, number=708):
    return {
        "action": "opened",
        "repository": {"full_name": REPO},
        "issue": {
            "number": number, "user": {"login": "chadkhalil21-svg"},
            "title": MISSION_TITLE if chief else "[Plenum Workforce] public research",
            "body": (MISSION_MAGIC + "\nobjective: " + objective) if chief else
                "PLENUM_PUBLIC_WORKFORCE_V2\nkind: " + kind + "\nobjective: " + objective,
        },
    }


def checked_official_results(capability):
    return [{"title": title, "source": source, "url": url, "http_status": 200}
            for title, source, url in DOMAIN_SOURCES[capability]]


class ExistingReviewedDomainWorkerTests(unittest.TestCase):
    def test_match_only_explicit_applicable_capability(self):
        self.assertEqual(match_original_capability(OBJECTIVE), "cloudflare_workers_ai_free")
        self.assertEqual(match_original_capability(NOAA), "noaa_water_station_metadata")
        for other in ("Create a public data validator for scientific observations",
                      "Survey general battery sources and create a program",
                      "Access Cloudflare private account and deploy billing",
                      "NOAA sources only"):
            self.assertIsNone(match_original_capability(other))

    def test_reuse_actual_original_verified_tools_with_functional_checks(self):
        for task, capability in ((OBJECTIVE, "cloudflare_workers_ai_free"),
                                 (NOAA, "noaa_water_station_metadata")):
            with self.subTest(task=task), TemporaryDirectory() as folder:
                root = Path(folder) / "checked"
                manifest = reuse_original_program(capability, task, root)
                self.assertEqual(manifest["file_count"], 3)
                self.assertTrue(manifest["functional_verifier_executed_and_passed"])
                self.assertTrue((root / "main.py").is_file())
                self.assertTrue((root / "manifest.json").is_file())
                self.assertFalse(manifest["generated_program_has_not_been_deployed"] is False)
                self.assertNotIn("api_key", json.dumps(manifest))
                with self.assertRaises(FileExistsError):
                    reuse_original_program(capability, task, root)

    def test_original_program_worker_runs_real_scoped_validator_not_generic_starter(self):
        with TemporaryDirectory() as folder:
            result = run_issue(event(kind="public_program"), output_dir=Path(folder))
            self.assertEqual(result["status"], "DRAFT_READY_FOR_FOUNDER")
            self.assertTrue(result["reused_existing_domain_program"])
            self.assertTrue(result["actual_offline_functional_test_passed"])
            self.assertTrue(result["code_executed"])
            self.assertFalse(result["production_written"])
            code = (Path(folder) / "issue-708/code/main.py").read_text()
            self.assertIn("FREE_NEURONS", code)
            self.assertIn("model_not_confirmed_free", code)
            self.assertNotIn("row.get(\"value\")", code)

    def test_only_first_party_real_http_200_metadata_is_accepted(self):
        class Response:
            status = 200
            def __init__(self, url):
                self.url = url
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def geturl(self):
                return self.url
            def read(self, size):
                return b"<html>official primary source</html>"
        urls = []
        def fake_opener(request, timeout):
            self.assertEqual(timeout, 15)
            urls.append(request.full_url)
            return Response(request.full_url)
        data = official_source_records("cloudflare_workers_ai_free", opener=fake_opener)
        self.assertEqual(len(data), 2)
        self.assertEqual(urls, [v[2] for v in DOMAIN_SOURCES["cloudflare_workers_ai_free"]])
        self.assertTrue(all(v["source"] == "Cloudflare" for v in data))
        self.assertTrue(all(v["independently_quoted_page_text"] is False for v in data))

    def test_real_original_chief_delegates_relevant_sources_and_real_code(self):
        with TemporaryDirectory() as folder, patch(
            "plenum_ai.reviewed_domain_workers.official_source_records",
            return_value=checked_official_results("cloudflare_workers_ai_free")
        ):
            outcome = execute(event(chief=True), output_dir=Path(folder))
            self.assertEqual(outcome["status"], "VERIFIED_BOUNDED_TEAM")
            self.assertTrue(outcome["worker_artifacts_technically_verified"])
            self.assertTrue(outcome["independent_verified"])
            self.assertFalse(outcome["founder_objective_verified"])
            self.assertEqual(outcome["named_entity_evidence"],
                             "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF")
            self.assertEqual(outcome["irrelevant_worker_kinds"], [])
            self.assertEqual(outcome["new_worker_invocations"], 2)
            scopes = [x["verified_scope"] for x in outcome["worker_results"]]
            self.assertTrue(any("primary source HTTP 200" in x for x in scopes))
            self.assertTrue(any("functional tests passed" in x for x in scopes))
            self.assertEqual(len(outcome["worker_results"]), 2)

    def test_failed_official_source_get_blocks_without_unrelated_articles(self):
        with TemporaryDirectory() as folder, patch(
            "plenum_ai.reviewed_domain_workers.official_source_records", return_value=[]
        ):
            result = run_issue(event(), output_dir=Path(folder))
            self.assertEqual(result["status"], "BLOCKED_NO_PRIMARY_SOURCE_EVIDENCE")
            self.assertFalse(result["verified"])
            self.assertEqual(result["source_linked_records"], 0)


if __name__ == "__main__":
    unittest.main()
