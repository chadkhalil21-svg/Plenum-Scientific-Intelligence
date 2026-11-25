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
                self.assertEqual(json.loads(model.call_args_list[1].args[1]["messages"][1]["content"])["authorized_goal_divisions"],mp.ROLE_MAP)
            with patch.object(mp,"read_json",side_effect=AssertionError("no repeated inference")):
                self.assertEqual(mp.model_plan(Path(tmp),cid,pid),first)
                with self.assertRaises(ValueError):mp.model_plan(Path(tmp),cid,str(uuid4()))
        print("MODEL RECEIPT REUSE PASS one simulated chat, zero replay",flush=True)

    def test_nondefault_authorized_goal_binding(self):
        from sequential_mission import goal_texts
        from typed_scope_smoke import BUDGET, STATION
        tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
        reply={"model":mp.MODEL,"done":True,"message":{"content":json.dumps(valid_plan())},"eval_count":105,"prompt_eval_count":311}
        for scope in (BUDGET,STATION):
            goals=goal_texts(scope)
            cid,pid=str(uuid4()),str(uuid4())
            self.assertNotEqual(mp.digest(goals),mp.digest(mp.GOALS))
            with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
                directory=Path(tmp)
                with patch.object(mp,"read_json",side_effect=[tag,reply]) as model:
                    roles,receipt=mp.model_plan(directory,cid,pid,goals=goals)
                    self.assertEqual(roles,mp.ORDER)
                    self.assertEqual(receipt["goals_sha256"],mp.digest(goals))
                    self.assertEqual(json.loads(model.call_args_list[1].args[1]["messages"][1]["content"])["goals"],goals)
                    self.assertEqual(model.call_count,2)
                self.assertFalse((directory/"minister-model-rejection.json").exists())
                self.assertEqual(mp.validate_receipt(receipt,cid,pid,goals=goals),mp.ORDER)
                with patch.object(mp,"read_json",side_effect=AssertionError("no replay")):
                    self.assertEqual(mp.model_plan(directory,cid,pid,goals=goals),(roles,receipt))
                    for wrong in (mp.GOALS,dict(goals,A="Different authorized objective"),dict(goals,Z="Unauthorized goal ID")):
                        with self.assertRaises(ValueError):mp.model_plan(directory,cid,pid,goals=wrong)
                    with self.assertRaises(ValueError):mp.validate_receipt(receipt,cid,pid)
                    with self.assertRaises(ValueError):mp.validate_receipt(dict(receipt,paid_inference=True),cid,pid,goals=goals)
        print("NONDEFAULT GOAL RECEIPT PASS bibliography and station fresh/restart binding; cross-scope and unauthorized IDs denied; no replay",flush=True)

    def test_natural_objective_selection_is_held_out_and_drives_real_program(self):
        import objective_mission as om
        from mission_scope import validate_scope
        chosen=["median","shared_terms"]
        scope={"kind":"public_objective","objective":"Which words occur in both summaries and what is the middle ordered observation?",
               "dois":["10.1145/3442188.3445922"],
               "inputs":{"documents":["resilient storage systems","resilient retrieval systems"],"samples":[12,3,9,44,18]},
               "operation_commitment":mp.digest(sorted(chosen))}
        self.assertEqual(validate_scope(scope),scope)
        kwargs=om.planning_kwargs(scope)
        good=valid_plan()
        good["step_3"].update(tool="stream",operations={"group_1":"median","group_2":"shared_terms"})
        self.assertEqual(mp.validate_choice(good,**kwargs),mp.ORDER)
        schema=mp.plan_schema(**kwargs)["properties"]["step_3"]["properties"]["operations"]
        self.assertEqual(set(schema["required"]),{"group_1","group_2"})
        self.assertIn("median",schema["properties"]["group_1"]["enum"])
        self.assertIn("median+range",schema["properties"]["group_1"]["enum"])
        self.assertNotIn("median+median",schema["properties"]["group_1"]["enum"])
        self.assertNotIn("shared_terms",schema["properties"]["group_1"]["enum"])
        for bad in (["median","shared_terms"],{"group_1":"median"},
                    {"group_1":"mean","group_2":"shared_terms"},
                    {"group_1":"median","group_2":"shared_terms+word_counts"},
                    {"group_1":"median+median","group_2":"shared_terms"},
                    {"group_1":"median","group_2":"shell"}):
            changed=dict(good,step_3=dict(good["step_3"],operations=bad))
            with self.subTest(bad=bad),self.assertRaises(mp.PlanRejected):
                mp.validate_choice(changed,**kwargs)
        tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
        reply={"model":mp.MODEL,"done":True,"message":{"content":json.dumps(good)},"eval_count":155,"prompt_eval_count":451}
        cid,pid=str(uuid4()),str(uuid4())
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            directory=Path(tmp)
            with patch.object(mp,"read_json",side_effect=[tag,reply]) as model:
                order,receipt=mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs)
                request=model.call_args_list[1].args[1]
                self.assertNotIn(scope["operation_commitment"],json.dumps(request))
                payload=json.loads(request["messages"][1]["content"])
                self.assertEqual(set(payload["approved_operations"]),set(om.OPS))
                self.assertEqual(payload["question"],scope["objective"])
                self.assertEqual(set(payload["operation_definitions"]),set(om.OPS))
                self.assertNotIn("goals",payload)
                self.assertEqual(set(payload["required_operation_groups"]["group_1"]),om.NUMERIC)
                self.assertEqual(set(payload["required_operation_groups"]["group_2"]),om.TEXT)
            self.assertEqual(order,mp.ORDER)
            (directory/"minister-plan.json").write_text(json.dumps({"company":cid,"parent":pid,"model_receipt_sha256":mp.digest(receipt)}))
            actual=om.engineering(scope,directory,"stream")
            self.assertEqual(actual["validation"],{"results":{"median":{"numerator":12,"denominator":1},"shared_terms":["resilient","systems"]}})
            with patch.object(mp,"read_json",side_effect=AssertionError("no repeated inference")):
                self.assertEqual(mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs),(order,receipt))

    def test_rejection_diagnostic_keeps_only_reviewed_choices(self):
        policy={"allowed":("range","median","shared_terms"),
                "required_groups":(("range","median"),("shared_terms",)),
                "commitment":mp.digest(["range","shared_terms"])}
        with tempfile.TemporaryDirectory() as tmp:
            choice=valid_plan()
            choice["step_3"]["operations"]={"group_1":"median","group_2":"SECRET_RAW_TEXT"}
            mp.rejected_choice(Path(tmp),"company","parent",choice,"OPERATION_SCOPE",policy)
            raw=(Path(tmp)/"minister-model-rejection.json").read_text()
            self.assertNotIn("SECRET_RAW_TEXT",raw)
            self.assertEqual(json.loads(raw)["reviewed_operation_selections"],
                             {"group_1":"median","group_2":None})

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
