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

    def test_topic_discovery_reuses_source_bound_contracts(self):
        topic="Survey public concrete corrosion papers"
        mission={"objective":"Find public concrete corrosion papers and verify the discovered records.",
                 "authorized_inputs":{"literature_discovery":topic,"commercial":True}}
        selection={"literature_discovery":True,"commercial":False}
        scope,nodes=nv.vm.graph(mission,selection)
        plan={"nodes":nodes}
        self.assertEqual(nv.partition(plan),{"intelligence":["paper_discovery"],
            "research":["paper_readback"],"engineering":[],"commercial":["evidence_report"]})
        self.assertEqual(scope["paper_survey"],topic)
        self.assertEqual(scope["dois"],[])
        self.assertNotIn("business",scope)
        doi="10.1234/example"
        title="Concrete corrosion in coastal structures"
        discovery={"schema":"plenum-public-horizon-snapshot-v1","topic":topic,"category":"journals",
            "independent_breakthrough_verified":False,"records":[{"source":"crossref_journals",
            "category":"journals","independent_fact_check_complete":False,
            "title":title,"url":"https://doi.org/"+doi}]}
        record={"doi":doi,"title":title,"year":2024,"publisher":"Example publisher"}
        with patch("plenum_ai.world_horizon.scan_horizon",return_value=discovery) as search, \
             patch("plenum_ai.chief_contract_plan.read_crossref",return_value=record) as readback:
            first=nv.vm.run_contract("paper_discovery",scope,{})
            nv.vm.check_contract_result("paper_discovery",scope,{},first)
            search.assert_called_once_with(topic,category="journals",online=True)
            prior={"paper_discovery":first}
            second=nv.vm.run_contract("paper_readback",scope,prior)
            nv.vm.check_contract_result("paper_readback",scope,prior,second)
            readback.assert_called_once_with(doi,approved_dois=frozenset({doi}))
            prior["paper_readback"]=second
            report=nv.vm.run_contract("evidence_report",scope,prior)
            nv.vm.check_contract_result("evidence_report",scope,prior,report)
            self.assertEqual(set(report["sections"]),{"papers"})
            with self.assertRaises(ValueError):
                nv.vm.check_contract_result("paper_readback",scope,{"paper_discovery":first},
                    {doi:{**record,"title":"Unrelated result"}})
        for unsafe in ("https://example.com","Survey public private papers","Survey public one two three four five six papers"):
            with self.assertRaises(ValueError):
                nv.vm.validate({**mission,"authorized_inputs":{"literature_discovery":unsafe}})
        other,_=nv.vm.graph(mission,{"literature_discovery":False,"commercial":True})
        self.assertNotIn("paper_survey",other)

    def test_discovery_rejection_retains_safe_facts_without_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            local_scope={k:v for k,v in nv.fixture("discovery").items() if k!="planning_engine"}
            with patch.object(nv,"fixture",return_value=local_scope):
                scope,dispatch,plan=self.setup_plan(root,"discovery",["literature_discovery","thermal"])
            evidence=nv.evidence_root(root)
            rejected={"records":[],"providers":[{"source":"crossref_journals",
                "status":"unavailable","records":[],"error_type":"HTTPError",
                "query_strategy":"bibliographic_recovery","raw":"secret marker",
                "first_attempt":{"status":"retrieved_metadata","records":[]}}]}
            with patch.dict(os.environ,{"GITHUB_ACTIONS":"true"}), \
                 patch.object(nv.vm,"run_contract",return_value=rejected) as worker:
                with self.assertRaises(ValueError):
                    nv.collect(evidence,dispatch,plan,nv.ORDER[:1],execute_role="intelligence")
                receipt=json.loads((evidence/"paper_discovery.rejected.json").read_text())
                self.assertFalse(receipt["accepted"])
                self.assertEqual(receipt["diagnostic"],{"records":0,"providers":[{
                    "status":"unavailable","records":0,"error_type":"HTTPError",
                    "bibliographic_recovery":True,"first_attempt":{
                        "status":"retrieved_metadata","records":0,"error_type":None}}]})
                self.assertNotIn("secret marker",json.dumps(receipt))
                self.assertFalse((evidence/"paper_discovery.result.json").exists())
                with self.assertRaises(FileExistsError):
                    nv.collect(evidence,dispatch,plan,nv.ORDER[:1],execute_role="intelligence")
                self.assertEqual(worker.call_count,1)

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

    def test_native_setup_retry_only_before_provider_work(self):
        import sequential_mission as seq
        from unittest.mock import Mock
        for blocked in (None, "provider", "reserved", "missing_bootstrap", "system_blocked", "user_blocked", "scheduled", "unknown_blocked"):
            with self.subTest(blocked=blocked), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                scope,plan,graph=self.setup_plan(root,"science",["bibliography","stations"])
                cid,mid=plan["company"],plan["parent"]
                plan["scope_sha256"]=seq.scope_digest(scope)
                (root/"minister-plan.json").write_text(json.dumps(plan))
                agents={r:str(uuid4()) for r in seq.MISSION_ORDER}
                iid=plan["tasks"]["research"]
                rid=str(uuid4())
                value={"input_sha256":{}}
                exclusive(root/"intelligence.json",{"company":cid,"issue":plan["tasks"]["intelligence"],
                          "role":"intelligence","result":value,"sha256":seq.digest(value)})
                if blocked=="reserved":
                    contract=nv.partition(graph)["research"][0]
                    exclusive(nv.evidence_root(root)/(contract+".reserved.json"),{})
                def call(path,method=None,payload=None):
                    for role in ("intelligence","research"):
                        if path=="/api/issues/"+plan["tasks"][role]:
                            interruption={"observedRunId":rid}
                            status="done" if role=="intelligence" else "todo"
                            if role=="research" and blocked in ("system_blocked","user_blocked","scheduled","unknown_blocked"):
                                status="blocked"
                                if blocked!="unknown_blocked":
                                    interruption.update(responsibility="user" if blocked=="user_blocked" else "system",
                                        state="waiting_for_user" if blocked=="user_blocked" else "retry_scheduled" if blocked=="scheduled" else "failed",
                                        canRetry=blocked!="user_blocked",userAction="approval" if blocked=="user_blocked" else None)
                            return {"id":plan["tasks"][role],"companyId":cid,"parentId":mid,
                                    "assigneeAgentId":agents[role],"status":status,
                                    "interruption":interruption}
                    if path=="/api/heartbeat-runs/"+rid:
                        return {"id":rid,"companyId":cid,"agentId":agents["research"],
                                "contextSnapshot":{"issueId":iid},"status":"failed","errorCode":"setup_failed",
                                "exitCode":None,"finishedAt":"2026-11-27T00:00:00Z",
                                "resultJson":{"executionRecovery":{"kind":"other" if blocked=="missing_bootstrap" else "bootstrap",
                                                "providerWorkStarted":blocked=="provider"}}}
                    if path=="/api/issues/"+iid+"/retry" and method=="POST":
                        self.assertEqual(payload["observedRunId"],rid)
                        return {"accepted":True,"stale":False,"requestId":str(uuid4())}
                    raise AssertionError(path)
                api=Mock(side_effect=call)
                # Isolate the retry gate while preserving exact dependency and
                # local reservation checks; no real provider or board action.
                with patch.dict(os.environ,{"GITHUB_ACTIONS":"true","PLENUM_EPHEMERAL_RUNNER":"confirmed"}), \
                     patch("production_wiring.load_prepared",return_value={"checkpoint_mode":"local"}), \
                     patch.object(nv,"load",return_value=graph):
                    self.assertEqual(seq.retry_unstarted_verifier(api,root,cid,mid,plan,agents,scope,target="research"),blocked in (None,"system_blocked"))
                    self.assertFalse(seq.retry_unstarted_verifier(api,root,cid,mid,plan,agents,scope,target="research"))
                posts=[c for c in api.call_args_list if len(c.args)>1 and c.args[1]=="POST"]
                self.assertEqual(len(posts),1 if blocked in (None,"system_blocked") else 0)
                self.assertEqual((root/"research-setup-retry-accepted.json").is_file(),blocked in (None,"system_blocked"))

if __name__=="__main__":unittest.main(verbosity=2)
