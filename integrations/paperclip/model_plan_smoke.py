"""Model plan gate and restart reuse regression, no live network."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import model_plan as mp


def valid_plan():
    return {slot:{"goal":goal,"division":mp.ROLE_MAP[goal]}
            for slot,goal in zip(mp.SLOTS,("A","D","B","C","E"))}


class PlanTests(unittest.TestCase):
    def test_scope_and_order(self):
        good=valid_plan()
        self.assertEqual(mp.validate_choice(good),mp.ORDER)
        swapped=dict(good,step_1=good["step_2"],step_2=good["step_1"])
        repeated=dict(good,step_2=good["step_1"])
        invalid=dict(good,step_1={"goal":"A","division":"shell"})
        missing={k:v for k,v in good.items() if k!="step_5"}
        for bad,code in ((swapped,"DEPENDENCY_ORDER"),(repeated,"DUPLICATE_ASSIGNMENT"),
                         (invalid,"ASSIGNMENT_SCOPE"),(missing,"PLAN_SHAPE")):
            with self.subTest(code=code),self.assertRaisesRegex(mp.PlanRejected,code):
                mp.validate_choice(bad)
        schema=mp.plan_schema()
        self.assertEqual(schema["required"],list(mp.SLOTS))
        for slot,role in zip(mp.SLOTS,mp.ORDER):
            props=schema["properties"][slot]["properties"]
            self.assertEqual(props["division"]["enum"],[role])
            self.assertEqual(set(props["goal"]["enum"]),set(mp.GOALS))
        print("ORDERED SLOT SCHEMA PASS distinct goals required, independent order gate retained",flush=True)

    def test_one_call_and_restart_reuse(self):
        good=valid_plan()
        tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
        reply={"model":mp.MODEL,"done":True,"message":{"content":json.dumps(good)},"eval_count":105,"prompt_eval_count":311}
        cid,pid=str(uuid4()),str(uuid4())
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            with patch.object(mp,"read_json",side_effect=[tag,reply]) as model:
                first=mp.model_plan(Path(tmp),cid,pid)
                self.assertEqual(model.call_count,2)
                self.assertEqual(model.call_args_list[1].args[0],"/api/chat")
                self.assertEqual(model.call_args_list[1].args[1]["format"],mp.plan_schema())
            with patch.object(mp,"read_json",side_effect=AssertionError("no repeated inference")):
                self.assertEqual(mp.model_plan(Path(tmp),cid,pid),first)
                with self.assertRaises(ValueError):mp.model_plan(Path(tmp),cid,str(uuid4()))
        print("MODEL RECEIPT REUSE PASS one simulated chat, zero replay",flush=True)

    def test_rejected_plan_no_fallback(self):
        good=valid_plan()
        bad=dict(good,step_1=good["step_2"],step_2=good["step_1"])
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
            reply={"model":mp.MODEL,"done":True,"message":{"content":json.dumps(bad)},"eval_count":105,"prompt_eval_count":311}
            with patch.object(mp,"read_json",side_effect=[tag,reply]) as model:
                with self.assertRaisesRegex(mp.PlanRejected,"DEPENDENCY_ORDER"):mp.model_plan(Path(tmp),"company","parent")
                with self.assertRaises(FileExistsError):mp.model_plan(Path(tmp),"company","parent")
                self.assertEqual(model.call_count,2)
            self.assertFalse((Path(tmp)/"minister-model-plan.json").exists())
            diag=json.loads((Path(tmp)/"minister-model-rejection.json").read_text())
            self.assertEqual(diag["reason"],"DEPENDENCY_ORDER")
            self.assertEqual(diag["assignments"][0],{"position":1,"goal":"D","division":"research"})
            self.assertFalse(diag["accepted"])
        print("REJECTED ORDER ARTIFACT PASS no fallback or second inference",flush=True)

    def test_untrusted_text_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad={"step_1":{"goal":"UNTRUSTED_FIXTURE_SECRET","division":"UNTRUSTED_FIXTURE_SECRET"},
                 "UNTRUSTED_FIXTURE_SECRET":"arbitrary"}
            mp.rejected_choice(Path(tmp),"company","parent",bad,"ASSIGNMENT_SCOPE")
            raw=(Path(tmp)/"minister-model-rejection.json").read_text()
            self.assertNotIn("UNTRUSTED_FIXTURE_SECRET",raw)
            self.assertEqual(json.loads(raw)["assignments"][0],{"position":1,"goal":None,"division":None})
        print("REJECTION DIAGNOSTIC REDACTION PASS",flush=True)


if __name__=="__main__":
    unittest.main(verbosity=2)
