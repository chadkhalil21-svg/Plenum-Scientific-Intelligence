"""Only NEW integration: one founder instruction routed to existing Plenum teams."""
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from plenum_ai.workforce_public_inbox import parse_public_issue, run_issue
from plenum_ai.workforce_team_dispatch import dispatch, PUBLIC_GROUNDING_RECEIPTS


def event(kind="public_program", objective="Create a public data validator for scientific observations"):
    return {
        "action":"opened",
        "repository":{"full_name":"chadkhalil21-svg/Plenum-Scientific-Intelligence"},
        "issue":{"number":901,"user":{"login":"chadkhalil21-svg"},
                 "title":"[Plenum Workforce] public research",
                 "body":"PLENUM_PUBLIC_WORKFORCE_V2\nkind: "+kind+"\nobjective: "+objective}
    }


class TeamDispatchIntegration(unittest.TestCase):
    def test_public_verification_routes_real_approved_receipt_not_science_replay(self):
        objective = "Ground gpqa claim / pass_rate_delta_rounded was -0.33"
        with tempfile.TemporaryDirectory() as d:
            result = run_issue(event("public_verification", objective), output_dir=Path(d))
            self.assertEqual(result["status"], "DRAFT_READY_FOR_FOUNDER")
            self.assertEqual(result["worker"], "existing_cmbagent_numeric_grounding")
            self.assertEqual(result["upstream_numeric_token_grounding"], "grounded")
            self.assertTrue(result["field_value_matches"])
            self.assertTrue(result["field_grounded"])
            self.assertEqual(result["field_grounding_status"], "exact_field_match")
            self.assertFalse(result["semantic_truth_verified"])
            report = json.loads((Path(d)/"issue-901"/"numeric-claim-grounding.json").read_text())
            self.assertEqual(report["claims"][0]["quantities"][0]["hits"][0]["value"], "-0.33")
            self.assertEqual(report["artifact_sha256"], "bd389be2a068c0d99bffebf70259b9cfea9f58bb0c2098a255ed8f4cd77819d2")

    def test_public_verification_exact_small_counts_and_wrong_field_value(self):
        prefix = "Ground gpqa claim / "
        cases = (
            ("candidate_qwen35_4b.correct was 0", True, "exact_field_match"),
            ("reference_qwen3_06b.correct was 1", True, "exact_field_match"),
            # The number 1 exists for reference, but candidate actually scored 0.
            ("candidate_qwen35_4b.correct was 1", False, "field_value_mismatch"),
        )
        for claim, expected, status in cases:
            with self.subTest(claim=claim), tempfile.TemporaryDirectory() as d:
                result = run_issue(event("public_verification", prefix + claim), output_dir=Path(d))
                self.assertEqual(result["status"], "DRAFT_READY_FOR_FOUNDER")
                self.assertEqual(result["field_value_matches"], expected)
                self.assertEqual(result["field_grounded"], expected)
                self.assertEqual(result["field_grounding_status"], status)
                self.assertFalse(result["semantic_truth_verified"])
                self.assertEqual(result["upstream_numeric_token_grounding"], "grounded")
                self.assertIn(status, result["verified_scope"])
                if not expected:
                    report = json.loads((Path(d)/"issue-901"/"numeric-claim-grounding.json").read_text())
                    self.assertEqual(report["field_verification"]["requested_value"], "1")
                    self.assertEqual(report["field_verification"]["recorded_value"], "0")
                    self.assertFalse(report["field_verification"]["exact_labelled_token_hit"])

    def test_public_verification_wrong_receipt_hash_fails_before_adapter(self):
        source, _, fields = PUBLIC_GROUNDING_RECEIPTS["gpqa"]
        objective = "Ground gpqa claim / pass_rate_delta_rounded was -0.33"
        with tempfile.TemporaryDirectory() as d, patch.dict(
            PUBLIC_GROUNDING_RECEIPTS, {"gpqa": (source, "0" * 64, fields)}
        ), patch("plenum_ai.workforce_team_dispatch.subprocess.run") as run:
            result = run_issue(event("public_verification", objective), output_dir=Path(d))
            self.assertEqual(result["status"], "BLOCKED_WORKER_OR_VERIFICATION")
            self.assertFalse(result["verified"])
            run.assert_not_called()

    def test_public_verification_rejects_unapproved_alias_field_and_extra_text(self):
        for objective in (
            "Ground arbitrary claim / pass_rate_delta_rounded was -0.33",
            "Ground ../private claim / pass_rate_delta_rounded was -0.33",
            "Ground gpqa claim / unrelated_field was -0.33",
            "Ground gpqa claim / pass_rate_delta_rounded was -0.33 and other text",
        ):
            with self.subTest(objective=objective), self.assertRaises(ValueError):
                parse_public_issue(event("public_verification", objective))

    def test_four_role_routes_preserve_original_no_model_path(self):
        roles={
            "public_research":"existing_plenum_world_horizon",
            "public_program":"existing_plenum_program_foundry",
            "public_science":"existing_plenum_durable_science",
            "public_creative":"existing_plenum_creative_studio",
        }
        for kind, worker in roles.items():
            with self.subTest(kind=kind):
                t=parse_public_issue(event(kind=kind))
                self.assertEqual(t["worker"],worker)
                self.assertEqual(t["cost_ceiling_usd"],0)

    def test_unapproved_tasks_cannot_run_tools(self):
        for kind in ["private_email","browser_login","send_invoice","payments","admin_delete"]:
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                parse_public_issue(event(kind=kind))

    def test_existing_program_foundry_has_actual_artifact_and_independent_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            result=run_issue(event(),output_dir=Path(d))
            self.assertEqual(result["status"],"DRAFT_READY_FOR_FOUNDER")
            self.assertEqual(result["generated_source_files"],3)
            self.assertFalse(result["code_executed"])
            self.assertFalse(result["production_written"])
            self.assertTrue((Path(d)/"issue-901"/"code"/"main.py").exists())

    def test_original_creative_worker_outputs_valid_xml(self):
        with tempfile.TemporaryDirectory() as d:
            result=run_issue(event("public_creative"),output_dir=Path(d))
            self.assertEqual(result["status"],"DRAFT_READY_FOR_FOUNDER")
            self.assertEqual(result["generated_artifacts"],3)
            self.assertFalse(result["creative_quality_independently_verified"])

    def test_science_dispatched_only_to_original_durable_graph_and_readback(self):
        evidence={"status":"executed_and_checkpointed",
                  "result":{"known_model_integration_passed":True}}
        restored={"finished":True,"workers_recorded":2,
                  "question":"Create a public data validator for scientific observations"}
        with tempfile.TemporaryDirectory() as d, patch(
            "plenum_ai.durable_graph.run_persistent", return_value=evidence
        ) as run, patch(
            "plenum_ai.durable_graph.inspect_persistent",return_value=restored
        ) as inspect:
            t=parse_public_issue(event("public_science"))
            result=dispatch(t,Path(d))
            self.assertTrue(result["checkpoint_restored"])
            self.assertFalse(result["original_scientific_discovery"])
            self.assertEqual(run.call_count,1)
            self.assertEqual(inspect.call_count,1)

    def test_worker_failure_is_recorded_not_marked_success(self):
        with tempfile.TemporaryDirectory() as d, patch(
            "plenum_ai.workforce_team_dispatch.dispatch",
            side_effect=RuntimeError("unverified")
        ):
            r=run_issue(event(),output_dir=Path(d))
            self.assertEqual(r["status"],"BLOCKED_WORKER_OR_VERIFICATION")
            self.assertFalse(r["verified"])

    def test_v1_legacy_founder_issue_keeps_its_existing_route(self):
        e=event()
        e["issue"]["body"]=("PLENUM_PUBLIC_WORKFORCE_V1\n"
                           "objective: Review free open source AI agents and their security safeguards")
        t=parse_public_issue(e)
        self.assertEqual(t["kind"],"public_research")
        self.assertEqual(t["worker"],"existing_plenum_world_horizon")


    def test_science_dispatch_uses_only_one_bounded_continuation(self):
        objective="Run known orbital and thermal science fixtures"
        saved={"finished":False,"workers_recorded":2,"question":objective,
               "requested_tools":["scipy.orbit","scipy.thermal"]}
        complete={**saved,"finished":True}
        evidence={"status":"executed_and_checkpointed","resumed_unfinished_graph":True,
                  "result":{"known_model_integration_passed":True}}
        with tempfile.TemporaryDirectory() as folder, patch(
            "plenum_ai.durable_graph.run_persistent",
            side_effect=[RuntimeError("interruption"),evidence]
        ) as run, patch(
            "plenum_ai.durable_graph.inspect_persistent", side_effect=[saved,complete]
        ):
            result=run_issue(event("public_science",objective),output_dir=Path(folder))
            self.assertTrue(result["verified"])
            self.assertTrue(result["continued_unfinished_graph"])
            self.assertEqual(run.call_count,2)
            self.assertEqual(run.call_args_list[0],run.call_args_list[1])


if __name__=="__main__":
    unittest.main()
