"""Focused existing-architecture acceptance for authentic Google EGM and offline AQuA method."""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from plenum_ai import agent_council as c
from plenum_ai.ambient_quality_insights import inspect_chief_report, main as quality_main


class OriginalGoogleEGMFiveStageTests(TestCase):
    def test_three_new_official_personas_are_pinned_and_read_only(self):
        for role in ("zoom_out", "comprehension", "implementation_readiness"):
            source = c.read_real_google_egm_role(role)
            self.assertIn("Strict Read-Only Protocol", source)
            self.assertIn("license: Apache-2.0", source)
        self.assertIn("Design Critic Goldfish",
                      c.read_real_google_egm_role("design_critic"))
        with self.assertRaises(ValueError):
            c.read_real_google_egm_role("unsafe/arbitrary/path")

    def test_five_stages_actually_get_isolated_original_model_calls(self):
        agenda = "Full EGM review of free Plenum agent quality and source verification for Google AQuA"
        event = {"action": "opened", "repository": {"full_name": c.REPO},
                 "issue": {"number": 570, "title": c.TITLE,
                           "user": {"login": c.FOUNDER},
                           "body": c.MARKER + "\nobjective: " + agenda}}
        calls = []
        def fake(system, user):
            calls.append((system, user))
            return "Review of actual task artifact only, with no authority to approve external source claims."
        with patch.dict("os.environ", {
            "PLENUM_EPHEMERAL_RUNNER": "confirmed",
            "PLENUM_COUNCIL_MODEL_URL": c.MODEL_URL,
        }), patch.object(c, "_ask_local", side_effect=fake):
            result = c.deliberate(event)
        self.assertEqual(len(calls), 10)  # four original + prior critic + five new real stages
        self.assertEqual(result["seats_completed"], 4)
        self.assertTrue(result["official_egm_full_stages_completed"])
        self.assertEqual([x["stage"] for x in result["official_egm_stage_reviews"]],
                         ["5_zoom_out", "6_comprehension", "7_design_critic",
                          "8_intermediate_zoom_out", "9_implementation_readiness"])
        self.assertTrue(all("Strict Read-Only Protocol" in x[0] for x in calls[5:]))
        self.assertTrue(all(x["fresh_model_context"] for x in result["official_egm_stage_reviews"]))
        self.assertNotIn("DATED PUBLIC ELEPHANT", calls[5][0])
        self.assertNotIn("Google AQuA:", calls[6][0])  # naive reader sees only artifact
        self.assertFalse(result["tasks_executed"])
        self.assertFalse(result["recommendation_verified_against_external_sources"])

    def test_full_egm_only_when_explicit_to_avoid_extra_inference(self):
        self.assertFalse(c.wants_full_egm_review("Review free public tools"))
        self.assertTrue(c.wants_full_egm_review("Full EGM review of public agent quality"))


class GoogleAQuAOfflineOriginalTraceTests(TestCase):
    @staticmethod
    def original():
        return {
            "schema": "plenum-chief-founder-team-v2", "issue_number": 569,
            "status": "VERIFIED_BOUNDED_TEAM",
            "worker_artifacts_technically_verified": True,
            "founder_objective_verified": False,
            "named_entity_evidence": "NAME_MENTION_ONLY_NOT_FULL_OBJECTIVE_PROOF",
            "external_account_changes": False, "paid_api_used": False,
        }

    def test_official_original_aqua_telemetry_schema_is_read_and_used(self):
        from plenum_ai.ambient_quality_insights import (
            read_official_aqua_event_schema, AQUA_EVENTS_GIT_BLOB_SHA
        )
        fields = read_official_aqua_event_schema()
        self.assertEqual(AQUA_EVENTS_GIT_BLOB_SHA,
                         "78b6fbe3319a0932cd2fcdf3f55ecca3ee5822e1")
        self.assertEqual([x["name"] for x in fields],
                         ["timestamp", "event_type", "agent", "session_id",
                          "invocation_id", "content", "attributes", "error_message"])
        output = inspect_chief_report(self.original())
        self.assertTrue(output["actual_google_aqua_event_schema_used"])
        self.assertEqual(output["offline_aqua_compatible_event"]["agent"],
                         "plenum-original-chief")
        self.assertFalse(output["official_google_aqua_engine_installed"])

    def test_real_chief_metadata_does_not_get_promoted_to_achieved_goal(self):
        output = inspect_chief_report(self.original())
        self.assertEqual(output["disposition"], "BOUNDED_DELIVERY_FOUNDER_OBJECTIVE_OPEN")
        self.assertEqual({x["code"] for x in output["findings"]},
                         {"NAME_MENTION_NOT_TASK_COMPLETION",
                          "FOUNDER_OBJECTIVE_NOT_PROVEN"})
        self.assertFalse(output["official_google_aqua_engine_installed"])
        self.assertFalse(output["google_cloud_telemetry_queried"])
        self.assertFalse(output["full_general_autonomy_claimed"])
        self.assertEqual(output["external_model_calls"], 0)

    def test_failed_worker_and_cost_uncertainty_fail_closed(self):
        d = self.original()
        d["status"] = "BLOCKED_PARTIAL_TEAM"
        d["worker_artifacts_technically_verified"] = False
        d["paid_api_used"] = True
        self.assertEqual(
            inspect_chief_report(d)["disposition"],
            "BLOCKED_OR_UNVERIFIED_DO_NOT_PROMOTE",
        )

    def test_unrecognized_report_rejected(self):
        d = self.original()
        d["schema"] = "injected-agent-output"
        with self.assertRaises(ValueError):
            inspect_chief_report(d)

    def test_cli_reads_original_report_and_creates_exact_scoped_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "chief-result-569.json").write_text(
                json.dumps(self.original()), encoding="utf-8")
            with patch("sys.argv", ["ambient_quality_insights",
                                    "--issue", "569", "--root", str(root)]):
                quality_main()
            result = json.loads((root / "ambient-quality-569.json").read_text())
            self.assertEqual(result["original_issue_number"], 569)
            self.assertEqual(result["disposition"],
                             "BOUNDED_DELIVERY_FOUNDER_OBJECTIVE_OPEN")
