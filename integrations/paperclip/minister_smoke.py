"""Offline regression for native Process adapter without a task environment hint."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import sequential_mission as mission


class MinisterTests(unittest.TestCase):
    def setUp(self):
        self.agent, self.company, self.parent = (str(uuid4()) for _ in range(3))
        self.env = {"PAPERCLIP_AGENT_ID": self.agent, "PAPERCLIP_COMPANY_ID": self.company}
        self.task = {"id": self.parent, "assigneeAgentId": self.agent,
                     "title": mission.TITLE, "description": mission.MISSION, "status": "todo"}
        self.roster = [{"name": spec[0], "id": str(uuid4()), "reportsTo": self.agent}
                       for spec in mission.SPECS.values()]

    def test_missing_task_hint_real_minister_entrypoint(self):
        children = []
        calls = []
        def fake(path, method="GET", body=None, *, worker=False):
            self.assertTrue(worker)
            calls.append((path, method))
            if path == "/api/agents/me":
                return {"id": self.agent, "companyId": self.company, "name": "Minister of Operations"}
            if path.startswith("/api/companies/"+self.company+"/issues?"):
                return [self.task]
            if path == "/api/issues/"+self.parent+"/checkout":
                return {}
            if path == "/api/companies/"+self.company+"/agents":
                return self.roster
            if path == "/api/companies/"+self.company+"/issues" and method=="POST":
                child={"id":str(uuid4()), **body}
                self.assertEqual(child["parentId"],self.parent)
                self.assertEqual(child.get("blockedByIssueIds",[]),[children[-1]["id"]] if children else [])
                children.append(child)
                return child
            if path == "/api/issues/"+self.parent and method=="PATCH":
                self.assertEqual(body["status"],"done")
                return {}
            self.fail("Unexpected API call")
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,self.env,clear=True), patch.object(mission,"ROOT",Path(tmp)), patch.object(mission,"api",side_effect=fake):
            mission.minister()
            plan=json.loads((Path(tmp)/self.company/"minister-plan.json").read_text())
        self.assertEqual(len(children),5)
        self.assertEqual([x["title"] for x in children],[mission.SPECS[k][1] for k in mission.MISSION_ORDER])
        self.assertEqual(plan["parent"],self.parent)
        print("MINISTER MISSING TASK ENV FALLBACK PASS five dependent children",flush=True)

    def test_missing_and_ambiguous_tasks_fail_closed(self):
        with patch.dict(os.environ,self.env,clear=True):
            for rows in ([],[self.task,self.task],[{**self.task,"assigneeAgentId":str(uuid4())}]):
                with patch.object(mission,"api",return_value=rows), self.assertRaisesRegex(ValueError,"exactly one"):
                    mission.minister_task(self.agent,self.company)
            with patch.object(mission,"api",return_value=[{k:v for k,v in self.task.items() if k!="id"}]), self.assertRaisesRegex(ValueError,"minister_task.id"):
                mission.minister_task(self.agent,self.company)
        print("MISSING AND AMBIGUOUS NATIVE TASKS DENIED",flush=True)

    def test_explicit_task_hint_scope_checked(self):
        with patch.dict(os.environ,{**self.env,"PAPERCLIP_TASK_ID":self.parent},clear=True), patch.object(mission,"api",return_value=self.task) as api:
            row,pid=mission.minister_task(self.agent,self.company)
            self.assertEqual(pid,self.parent)
            api.assert_called_once_with("/api/issues/"+self.parent,worker=True)

    def test_failure_receipt_redacts_unknown_key(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(mission,"ROOT",Path(tmp)):
            try: raise KeyError("PAPERCLIP_TASK_ID")
            except KeyError as exc: mission.failure_receipt("minister",exc)
            try: raise KeyError("fixture-must-not-appear-in-evidence")
            except KeyError as exc: mission.failure_receipt("research",exc)
            files=list(Path(tmp).glob("failure-*.json"))
            self.assertEqual(len(files),2)
            data={json.loads(p.read_text())["stage"]:json.loads(p.read_text()) for p in files}
            self.assertEqual(data["minister"]["missing_field"],"PAPERCLIP_TASK_ID")
            self.assertIsNone(data["research"]["missing_field"])
            self.assertNotIn("fixture-must-not-appear",json.dumps(data))
        print("FAILURE ARTIFACT REDACTION PASS",flush=True)


if __name__=="__main__":
    unittest.main(verbosity=2)
