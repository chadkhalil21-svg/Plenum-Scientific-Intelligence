"""Target one of Plenum's EXISTING native n8n model agents, public-only."""
import json
from pathlib import Path
from unittest import TestCase

from plenum_ai.workforce_department_command import (
    MAGIC, TITLE, ROLES, parse_founder_department, tailor_original_n8n_workflow,
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

    def test_no_model_network_write_or_private_credentials_in_parser(self):
        src=(ROOT/"src/plenum_ai/workforce_department_command.py").read_text()
        for forbidden in ("subprocess.run(", "requests.post(", "gcloud run deploy",
                          "PLENUM_WHATSAPP_TOKEN", "GMAIL_ACCESS_TOKEN="):
            self.assertNotIn(forbidden,src)
