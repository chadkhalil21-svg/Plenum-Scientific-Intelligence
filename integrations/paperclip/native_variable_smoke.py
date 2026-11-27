"""Isolated native variable graph boundary checks; no real model or provider call."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from checkpoint_store import exclusive
from model_plan import MODEL, MODEL_DIGEST, digest
import native_variable as nv

class NativeVariableTests(unittest.TestCase):
    def setup_plan(self, directory, case, selected):
        cid,mid=str(uuid4()),str(uuid4())
        scope=nv.fixture(case)
        reply={"model":MODEL,"done":True,"message":{"content":json.dumps({k:k in selected for k in scope["mission"]["authorized_inputs"]})},"eval_count":20,"prompt_eval_count":200}
        with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}), patch.object(nv,"check_local_model",return_value=MODEL_DIGEST+"a"*52),patch.object(nv,"read_json",return_value=reply) as call:
            plan=nv.prepare(directory,scope,cid,mid)
            self.assertEqual(nv.prepare(directory,scope,cid,mid),plan)
            self.assertEqual(call.call_count,1)
        tasks={r:str(uuid4()) for r in (*nv.ORDER,"verification")}
        dispatch={"company":cid,"parent":mid,"tasks":tasks,"order":[*nv.ORDER,"verification"],"variable_graph_sha256":digest(plan)}
        exclusive(directory/"minister-plan.json",dispatch)
        return scope,dispatch,plan

    def test_partition_exact_and_unselected_scope(self):
        for case,selected,count in (("science",["bibliography","stations"],5),("engineering",["thermal"],3),("commercial",["commercial"],3)):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                scope,dispatch,plan=self.setup_plan(root,case,selected)
                self.assertEqual(sum(map(len,nv.partition(plan).values())),count)
                self.assertEqual(nv.load(root,scope,dispatch["company"],dispatch["parent"]),plan)
                with self.assertRaises(ValueError):
                    nv.load(root,scope,dispatch["company"],str(uuid4()))

    def test_ambiguous_contract_does_not_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scope,dispatch,plan=self.setup_plan(root,"engineering",["thermal"])
            evidence=nv.evidence_root(root)
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}),patch.object(nv.vm,"run_contract",side_effect=TimeoutError) as worker:
                with self.assertRaises(TimeoutError):
                    nv.collect(evidence,dispatch,plan,nv.ORDER[:3],execute_role="engineering")
                with self.assertRaises(FileExistsError):
                    nv.collect(evidence,dispatch,plan,nv.ORDER[:3],execute_role="engineering")
                self.assertEqual(worker.call_count,1)

    def test_owner_authorized_correction_and_readback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scope={**nv.fixture("engineering"),"planning_recovery":True}
            cid,mid=str(uuid4()),str(uuid4())
            def reply(name):
                return {"model":MODEL,"done":True,"message":{"content":json.dumps({k:k==name for k in scope["mission"]["authorized_inputs"]})},"eval_count":20,"prompt_eval_count":200}
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}),patch.object(nv,"check_local_model",return_value=MODEL_DIGEST+"a"*52),patch.object(nv,"read_json",side_effect=[reply("commercial"),reply("thermal")]) as model,patch.object(nv.vm,"run_contract") as worker:
                plan=nv.prepare(root,scope,cid,mid)
                self.assertEqual(nv.prepare(root,scope,cid,mid),plan)
                self.assertEqual(model.call_count,2)
                self.assertNotEqual(model.call_args_list[0].args[1],model.call_args_list[1].args[1])
                for call in model.call_args_list:
                    self.assertNotIn(scope["selection_commitment"],json.dumps(call.args[1]))
                worker.assert_not_called()
                evidence=nv.evidence_root(root)
                receipt=evidence/"planning-response-1.json"
                saved=json.loads(receipt.read_text())
                self.assertIs(saved["accepted"],False)
                receipt.write_text(json.dumps({**saved,"accepted":True}))
                with self.assertRaises(ValueError):
                    nv.load(root,scope,cid,mid,require_dispatch=False)
                self.assertEqual(model.call_count,2)

    def test_correction_never_replays_interrupted_or_twice_rejected_request(self):
        for interrupted in (True,False):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                scope={**nv.fixture("engineering"),"planning_recovery":True}
                cid,mid=str(uuid4()),str(uuid4())
                reply={"model":MODEL,"done":True,"message":{"content":json.dumps({k:k=="commercial" for k in scope["mission"]["authorized_inputs"]})},"eval_count":20,"prompt_eval_count":200}
                responses=[TimeoutError()] if interrupted else [reply,reply]
                with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}),patch.object(nv,"check_local_model",return_value=MODEL_DIGEST+"a"*52),patch.object(nv,"read_json",side_effect=responses) as model,patch.object(nv.vm,"run_contract") as worker:
                    with self.assertRaises((TimeoutError,ValueError)):
                        nv.prepare(root,scope,cid,mid)
                    with self.assertRaises(FileExistsError):
                        nv.prepare(root,scope,cid,mid)
                    self.assertEqual(model.call_count,1 if interrupted else 2)
                    worker.assert_not_called()

    def test_wrong_selection_never_calls_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scope=nv.fixture("engineering")
            selected={k:k=="commercial" for k in scope["mission"]["authorized_inputs"]}
            reply={"model":MODEL,"done":True,"message":{"content":json.dumps(selected)},"eval_count":20,"prompt_eval_count":200}
            cid,mid=str(uuid4()),str(uuid4())
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}),patch.object(nv,"check_local_model",return_value=MODEL_DIGEST+"a"*52),patch.object(nv,"read_json",return_value=reply) as model,patch.object(nv.vm,"run_contract") as worker:
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError,"commitment mismatch"):
                        nv.prepare(root,scope,cid,mid)
                self.assertEqual(model.call_count,1)
                worker.assert_not_called()

if __name__=="__main__":unittest.main(verbosity=2)
