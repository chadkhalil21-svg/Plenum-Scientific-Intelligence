"""Target one of Plenum's EXISTING native n8n model agents, public-only."""
import json
from pathlib import Path
from unittest import TestCase

from plenum_ai.workforce_department_command import (
    MAGIC, TITLE, ROLES, parse_founder_department, tailor_original_n8n_workflow,
    audit_public_draft_repositories,
)

REPO="chadkhalil21-svg/Plenum-Scientific-Intelligence"
ROOT=Path(__file__).resolve().parents[1]
SOURCE=json.loads((ROOT/"integrations/n8n/plenum-business-workforce.json").read_text())


def event(role="operations",objective="Prepare a public weekly lab operating checklist",
          actor="chadkhalil21-svg",title=TITLE,body=None):
    return {"action":"opened","repository":{"full_name":REPO},
            "issue":{"user":{"login":actor},"number":612,"title":title,
                     "body":body if body is not None else
                       MAGIC+"\nrole: "+role+"\nobjective: "+objective}}


class DirectNineDepartmentTests(TestCase):
    def test_all_existing_department_names_and_one_role_selection(self):
        self.assertEqual(len(ROLES),9)
        self.assertEqual(ROLES,{"research","engineering","browser","creative",
                                "marketing","operations","simulation","support","verification"})
        for role in ROLES:
            with self.subTest(role=role):
                task=parse_founder_department(event(role=role))
                compiled=tailor_original_n8n_workflow(SOURCE,task)
                original=next(x for x in SOURCE["nodes"] if x["name"]=="Assign Nine Roles")
                change=next(x for x in compiled["nodes"] if x["name"]=="Assign Nine Roles")
                self.assertEqual(len(compiled["nodes"]),len(SOURCE["nodes"]))
                self.assertNotEqual(original["parameters"]["jsCode"],change["parameters"]["jsCode"])
                self.assertIn('return roles.filter(([role]) => role === "'+role+'")',change["parameters"]["jsCode"])
                self.assertIn(json.dumps(task["objective"]),change["parameters"]["jsCode"])
                self.assertEqual(compiled["active"],False)

    def test_department_gets_only_reviewed_free_sources_not_installed_tools(self):
        task=parse_founder_department(event(
            role="engineering",
            objective="Design a public PyBaMM battery benchmark with an independent physical baseline",
        ))
        compiled=tailor_original_n8n_workflow(SOURCE,task)
        script=next(x for x in compiled["nodes"] if x["name"]=="Assign Nine Roles")["parameters"]["jsCode"]
        self.assertIn("pybamm [pybamm-team/PyBaMM]",script)
        self.assertIn("not installed",script)
        self.assertIn("never claim code or a solver ran",script)
        self.assertEqual(len(compiled["nodes"]),6)
        self.assertEqual(compiled["active"],False)
        self.assertEqual(len([x for x in compiled["nodes"] if "credentials" in x]),0)

    def test_no_source_match_keeps_only_founder_objective(self):
        task=parse_founder_department(event(
            role="support",
            objective="Draft an internal FAQ about unfamiliar etiquette wording",
        ))
        compiled=tailor_original_n8n_workflow(SOURCE,task)
        script=next(x for x in compiled["nodes"] if x["name"]=="Assign Nine Roles")["parameters"]["jsCode"]
        self.assertIn(json.dumps(task["objective"]),script)
        self.assertNotIn("FREE-source references",script)

    def test_wrong_author_private_data_or_role_denied(self):
        for e in [
            event(actor="someone-else"),
            event(title="forged"),
            event(role="chief"),
            event(role="finance_admin"),
            event(objective="Send private customer records to marketing"),
            event(objective="Read patent secrets from the account"),
            event(body=MAGIC+"\nrole: operations\nobjective: \n<script>abc</script>"),
            event(body=MAGIC+"\nrole: operations"),
            event(objective="bad"),
        ]:
            with self.subTest(body=str(e)[:85]),self.assertRaises((ValueError,PermissionError)):
                parse_founder_department(e)

    def test_original_n8n_dispatcher_cannot_drift(self):
        task=parse_founder_department(event())
        changed=json.loads(json.dumps(SOURCE))
        node=next(x for x in changed["nodes"] if x["name"]=="Assign Nine Roles")
        node["parameters"]["jsCode"]="// arbitrary unreviewed workflow"
        with self.assertRaises(ValueError):
            tailor_original_n8n_workflow(changed,task)
        self.assertEqual(SOURCE["active"],False)
        self.assertEqual(len(SOURCE["nodes"]),6)

    def test_extract_actual_untrusted_model_text_not_n8n_plans(self):
        from plenum_ai.workforce_department_command import extract_untrusted_public_department_reply
        text='Execution successful: {"role": "operations", "draft_untrusted": "Review weekly actions\\nSchedule checks", "status": "DRAFT_AWAITING_FOUNDER_REVIEW"}'
        self.assertEqual(
            extract_untrusted_public_department_reply(text),
            "Review weekly actions\nSchedule checks",
        )
        for bad in [
            "No real agent output",
            '{"draft_untrusted": ""}',
            '{"draft_untrusted": "one", "draft_untrusted": "two"}',
            '{"draft_untrusted": 42}',
            1,
        ]:
            with self.assertRaises((ValueError,TypeError)):
                extract_untrusted_public_department_reply(bad)

    def test_nine_agent_inference_only_from_founder_issue_or_explicit_founder_manual(self):
        workflow=(ROOT/".github/workflows/business-workforce-n8n-agent-trial.yml").read_text()
        triggers=workflow.split("permissions:",1)[0]
        self.assertIn("workflow_dispatch:",triggers)
        self.assertIn("issues:",triggers)
        self.assertNotIn("schedule:",triggers)
        self.assertNotIn("pull_request:",triggers)
        self.assertNotIn("  push:",triggers)
        self.assertIn("github.actor == 'chadkhalil21-svg'",workflow)
        self.assertIn("github.event.issue.user.login == 'chadkhalil21-svg'",workflow)
        self.assertIn("[Plenum Department] public assignment",workflow)

    def test_offline_repo_auditor_catches_actual_su2_agent_link_error(self):
        # The first original SU2 model task #390 cited a nonexistent/wrong
        # upstream identity, rather than the vetted source repo.
        from unittest.mock import patch
        text=("[1](https://github.com/su2/su2) "
              "[2](https://github.com/su2code/SU2/tree/master)")
        with patch("urllib.request.urlopen", side_effect=AssertionError("No HTTP allowed")):
            result=audit_public_draft_repositories(text)
        self.assertEqual(result["matched_reviewed_repository_count"],1)
        self.assertEqual(result["unreviewed_github_repository_count"],1)
        self.assertEqual(result["unreviewed_github_repositories"],["su2/su2"])
        self.assertEqual(result["status"],"REVIEW_REQUIRED_UNREGISTERED_SOURCE")
        self.assertFalse(result["scientific_claims_independently_verified"])
        self.assertEqual(result["model_calls"],0)
        self.assertEqual(result["network_requests"],0)
        self.assertFalse(result["code_installed_or_executed"])

    def test_known_repo_never_means_technical_claim_is_verified(self):
        audit=audit_public_draft_repositories(
            "Use https://github.com/pybamm-team/PyBaMM for battery modeling.")
        self.assertEqual(audit["matched_reviewed_repository_count"],1)
        self.assertEqual(audit["unreviewed_github_repository_count"],0)
        self.assertEqual(audit["status"],"REVIEW_REQUIRED_CLAIMS_NOT_FACT_CHECKED")
        self.assertFalse(audit["scientific_claims_independently_verified"])
        invalid=audit_public_draft_repositories("See https://github.com/su2code")
        self.assertEqual(invalid["malformed_github_urls"],1)
        with self.assertRaises(ValueError):
            audit_public_draft_repositories("")
        with self.assertRaises(ValueError):
            audit_public_draft_repositories("x"*12001)

    def test_durable_issue_receipt_does_not_publish_untrusted_agent_content(self):
        text=(ROOT/".github/workflows/business-workforce-n8n-agent-trial.yml").read_text()
        self.assertIn("issues: write",text)
        self.assertIn("plenum-department-public:",text)
        self.assertIn("independent_fact_verification",text)
        self.assertIn("audit_public_draft_repositories(draft)",text)
        receipt=text.split("- name: Publish bounded public department status",1)[1]
        receipt=receipt.split("- name: Delete temporary credentials",1)[0]
        for forbidden in ("draft_untrusted","run.log","credentials.json",
                          "public-department-reply.json"):
            self.assertNotIn(forbidden,receipt)
        self.assertIn("Founder-visible department status published",receipt)

    def test_no_model_network_write_or_private_credentials_in_parser(self):
        src=(ROOT/"src/plenum_ai/workforce_department_command.py").read_text()
        for forbidden in ("subprocess.run(", "requests.post(", "gcloud run deploy",
                          "PLENUM_WHATSAPP_TOKEN", "GMAIL_ACCESS_TOKEN="):
            self.assertNotIn(forbidden,src)
