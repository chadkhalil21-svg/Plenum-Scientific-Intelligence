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
        good["step_3"].update(tool="stream",operations={op:op in chosen for op in om.OPS})
        self.assertEqual(mp.validate_choice(good,**kwargs),mp.ORDER)
        schema=mp.plan_schema(**kwargs)["properties"]["step_3"]["properties"]["operations"]
        self.assertEqual(set(schema["required"]),set(om.OPS))
        self.assertTrue(all(x=={"type":"boolean"} for x in schema["properties"].values()))
        valid=good["step_3"]["operations"]
        for bad in (["median","shared_terms"],{"median":True},
                    dict(valid,median=False,mean=True),
                    dict(valid,word_counts=True),
                    dict(valid,median=1),
                    dict(valid,shell=True)):
            changed=dict(good,step_3=dict(good["step_3"],operations=bad))
            with self.subTest(bad=bad),self.assertRaises(mp.PlanRejected):
                mp.validate_choice(changed,**kwargs)
        tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
        route={k:dict(v) for k,v in good.items()}
        route["step_3"].pop("operations")
        def reply(value):
            return {"model":mp.MODEL,"done":True,"message":{"content":json.dumps(value)},"eval_count":55,"prompt_eval_count":251}
        policy=kwargs["operation_policy"]
        groups=policy["required_groups"]
        replies=[tag,reply(route)]+[reply({op:op in chosen for op in group}) for group in groups]
        cid,pid=str(uuid4()),str(uuid4())
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            directory=Path(tmp)
            with patch.object(mp,"read_json",side_effect=replies) as model:
                order,receipt=mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs)
                self.assertEqual(model.call_count,4)
                for index,group in enumerate(groups,2):
                    request=model.call_args_list[index].args[1]
                    self.assertNotIn(scope["operation_commitment"],json.dumps(request))
                    payload=json.loads(request["messages"][1]["content"])
                    self.assertEqual(payload["question"],scope["objective"])
                    self.assertEqual(set(payload["operations"]),set(group))
                    self.assertEqual(set(request["format"]["required"]),set(group))
                self.assertEqual(len(receipt["operation_classifications"]),2)
                for index,group in enumerate(groups,2):
                    payload=json.loads(model.call_args_list[index].args[1]["messages"][1]["content"])
                    self.assertEqual(payload["source_phrase_cues"],mp.semantic_evidence(scope["objective"],group))
                    self.assertTrue(all(span in scope["objective"] for spans in payload["source_phrase_cues"].values() for span in spans))
                self.assertEqual(receipt["response"],good)
            self.assertEqual(order,mp.ORDER)
            (directory/"minister-plan.json").write_text(json.dumps({"company":cid,"parent":pid,"model_receipt_sha256":mp.digest(receipt)}))
            actual=om.engineering(scope,directory,"stream")
            self.assertEqual(actual["validation"],{"results":{"median":{"numerator":12,"denominator":1},"shared_terms":["resilient","systems"]}})
            with patch.object(mp,"read_json",side_effect=AssertionError("no repeated inference")):
                self.assertEqual(mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs),(order,receipt))
                (directory/"minister-operation-2.attempt.json").unlink()
                with self.assertRaises(ValueError):mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs)

    def test_semantic_evidence_covers_reviewed_catalogue_without_acceptance_key(self):
        cases=[
            ("Calculate the arithmetic average of these readings","mean"),
            ("Report the central entry in the ordered observations","median"),
            ("Determine the difference between highest and lowest observations","range"),
            ("Compute the population variance of the measured series","population_variance"),
            ("Find the least-squares slope for the readings","least_squares_slope"),
            ("Measure the greatest jump between consecutive readings","max_step_change"),
            ("List vocabulary shared by every report","shared_terms"),
            ("Report the number of words in each report","word_counts"),
            ("Compute term frequency in the reports","term_frequency")]
        for question,operation in cases:
            with self.subTest(operation=operation):
                cues=mp.semantic_evidence(question,tuple(mp.OPERATION_CUES))
                self.assertTrue(cues[operation])
                self.assertTrue(all(span in question for spans in cues.values() for span in spans))
                if operation in ("range","median"):
                    self.assertFalse(cues["max_step_change"])
        self.assertTrue(all(not spans for spans in mp.semantic_evidence("Review the supplied public records",tuple(mp.OPERATION_CUES)).values()))

    def test_observed_1003_global_extrema_and_adjacent_change(self):
        # The original #1003 response omitted range. A missing lexical hint
        # does not authorize adding the answer or replaying its reservation.
        question = ("Determine the average narration word count per scene, the "
                    "difference between longest and shortest scenes, and the largest "
                    "word count change between consecutive scenes for the revised Terra documentary.")
        group = ("mean", "median", "range", "population_variance",
                 "least_squares_slope", "max_step_change")
        hints = mp.semantic_evidence(question, group)
        self.assertIn("difference between longest and shortest", hints["range"])
        self.assertTrue(hints["mean"])
        self.assertTrue(hints["max_step_change"])
        self.assertFalse(hints["median"])
        self.assertFalse(mp.semantic_evidence("Find the longest scene only", group)["range"])
        self.assertFalse(mp.semantic_evidence("Find changes between consecutive scenes", group)["range"])
        goals = dict(mp.GOALS, B="Select operations; objective: " + question)
        req = mp.classification_request(goals, group)
        payload = json.loads(req["messages"][1]["content"])
        self.assertEqual(payload["question"], question)
        self.assertEqual(payload["source_phrase_cues"], hints)
        self.assertNotIn("commitment", payload)
        self.assertTrue(all(span in question for spans in hints.values() for span in spans))

    def test_distinct_correction_after_complete_semantic_rejection(self):
        import objective_mission as om
        scope={"kind":"public_objective",
               "objective":"Find the average, global range and greatest adjacent change in the public readings.",
               "dois":["10.1145/3442188.3445922"],"inputs":{"samples":[7,2,10,4]},
               "operation_commitment":mp.digest(["max_step_change","mean","range"])}
        kwargs=om.planning_kwargs(scope)
        group=kwargs["operation_policy"]["allowed"]
        first={op:op in ("mean","max_step_change") for op in group}
        final=dict(first,range=True)
        route=valid_plan();route["step_3"]["tool"]="stream"
        tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
        def reply(value):
            return {"model":mp.MODEL,"done":True,"message":{"content":json.dumps(value)},
                    "eval_count":40,"prompt_eval_count":250}
        cid,pid=str(uuid4()),str(uuid4())
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            directory=Path(tmp)
            with patch.object(mp,"read_json",side_effect=[tag,reply(route),reply(first),reply(final)]) as model:
                result=mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs)
                self.assertEqual(model.call_count,4)
                first_request=model.call_args_list[2].args[1]
                correction_request=model.call_args_list[3].args[1]
                self.assertNotEqual(mp.digest(first_request),mp.digest(correction_request))
                self.assertNotIn(scope["operation_commitment"],json.dumps(correction_request))
                self.assertEqual(json.loads(correction_request["messages"][1]["content"])["previous_rejected_selection"],first)
            receipt=result[1]
            self.assertEqual(receipt["response"]["step_3"]["operations"],final)
            self.assertEqual(receipt["operation_classifications"][0]["selection"],first)
            self.assertEqual(receipt["operation_correction"]["selection"],final)
            with patch.object(mp,"read_json",side_effect=AssertionError("no replay")):
                self.assertEqual(mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs),result)
                (directory/"minister-correction-attempt.json").unlink()
                with self.assertRaises(ValueError):
                    mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_PAPERCLIP_MODEL":"local"}):
            directory=Path(tmp)
            with patch.object(mp,"read_json",side_effect=[tag,reply(route),reply(first),reply(first)]) as model:
                with self.assertRaises(ValueError):
                    mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs)
                with self.assertRaises(FileExistsError):
                    mp.model_plan(directory,cid,pid,goals=om.goals(scope),**kwargs)
                self.assertEqual(model.call_count,4)
            self.assertFalse((directory/"minister-model-plan.json").exists())
            self.assertTrue((directory/"minister-correction-result.json").exists())
        print("DISTINCT CORRECTION PASS exact rejection, hidden acceptance, immutable attempt, no replay",flush=True)

    def test_strict_deliverables_not_extra_operations(self):
        import objective_mission as om
        scope={"kind":"public_objective","objective":"Report the population variance of the synthetic measurements.",
               "dois":["10.1145/3442188.3445922"],
               "inputs":{"samples":[13,5,8,21]},
               "operation_commitment":mp.digest(["population_variance"])}
        policy=om.operation_policy(scope)
        group=policy["required_groups"][0]
        req=mp.classification_request(om.goals(scope),group)
        self.assertIn("intermediate computations",req["messages"][0]["content"])
        self.assertIn("Default every field to false",req["messages"][0]["content"])
        self.assertNotIn(scope["operation_commitment"],json.dumps(req))
        chosen={op:op=="population_variance" for op in group}
        self.assertEqual(mp.validate_operations(chosen,policy),["population_variance"])
        with self.assertRaisesRegex(mp.PlanRejected,"OPERATION_ACCEPTANCE"):
            mp.validate_operations(dict(chosen,mean=True),policy)
        print("STRICT DELIVERABLE SCOPE PASS no implied intermediate output or acceptance key",flush=True)

    def test_rejection_diagnostic_keeps_only_reviewed_choices(self):
        policy={"allowed":("range","median","shared_terms"),
                "required_groups":(("range","median"),("shared_terms",)),
                "commitment":mp.digest(["range","shared_terms"])}
        with tempfile.TemporaryDirectory() as tmp:
            choice=valid_plan()
            choice["step_3"]["operations"]={"median":True,"range":False,"shared_terms":"SECRET_RAW_TEXT"}
            mp.rejected_choice(Path(tmp),"company","parent",choice,"OPERATION_SCOPE",policy)
            raw=(Path(tmp)/"minister-model-rejection.json").read_text()
            self.assertNotIn("SECRET_RAW_TEXT",raw)
            self.assertEqual(json.loads(raw)["reviewed_operation_selections"],
                             {"median":True,"range":False,"shared_terms":None})

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
