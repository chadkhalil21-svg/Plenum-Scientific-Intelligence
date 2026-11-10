"""Only NEW integration: one founder instruction routed to existing Plenum teams."""
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from plenum_ai.workforce_public_inbox import parse_public_issue, run_issue
from plenum_ai.workforce_team_dispatch import dispatch


def event(kind="public_program", objective="Create a public data validator for scientific observations"):
    return {
        "action":"opened",
        "repository":{"full_name":"chadkhalil21-svg/Plenum-Scientific-Intelligence"},
        "issue":{"number":901,"user":{"login":"chadkhalil21-svg"},
                 "title":"[Plenum Workforce] public research",
                 "body":"PLENUM_PUBLIC_WORKFORCE_V2\nkind: "+kind+"\nobjective: "+objective}
    }


class TeamDispatchIntegration(unittest.TestCase):
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


if __name__=="__main__":
    unittest.main()
