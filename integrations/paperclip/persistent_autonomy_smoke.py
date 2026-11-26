"""Offline regression for persistent local model authorization, exact recovery, generic input."""
import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from uuid import uuid4
import model_plan as mp
import production_wiring as w
import recovery_audit as ra
from checkpoint_store import execute_once,exclusive
from model_plan_smoke import valid_plan
import sequential_mission as sm
from mission_scope import validate_scope
from dataset_mission import independent
class Tests(unittest.TestCase):
    def test_persistent_model_bound_to_prepared_and_activation(self):
        c,m,l=(str(uuid4()) for _ in range(3))
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{"PLENUM_PERSISTENT_BOARD":"confirmed"}):
            d=Path(tmp);w.prepared(d,c,m,"a"*64,"local","local")
            with self.assertRaises(ValueError):mp.model_plan(d,c,m)
            exclusive(d/"activation.json",{"company":c,"mission":m,"scope_sha256":"a"*64,"model_mode":"local"})
            tag={"models":[{"name":mp.MODEL,"digest":mp.MODEL_DIGEST+"a"*52}]}
            reply={"model":mp.MODEL,"done":True,"message":{"content":json.dumps(valid_plan())},"eval_count":100,"prompt_eval_count":300}
            goals=dict(mp.GOALS,B="Analyze approved unfamiliar samples")
            with patch.object(mp,"read_json",side_effect=[tag,reply]) as mock:
                roles,receipt=mp.model_plan(d,c,m,goals=goals)
                self.assertEqual(mock.call_count,2)
            with patch.object(mp,"read_json",side_effect=AssertionError("no replay")):
                self.assertEqual(mp.model_plan(d,c,m,goals=goals),(roles,receipt))
                with self.assertRaises(ValueError):mp.model_plan(d,c,m)
    def test_recovery_trace_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);c,i=str(uuid4()),str(uuid4())
            producer=Mock(side_effect=[TimeoutError("fixture"),{"ok":True}])
            rec=execute_once(d,c,"intelligence",i,producer)
            proof=ra.finalize(d,c,"intelligence",i,rec["sha256"])
            self.assertEqual(producer.call_count,2);self.assertEqual(proof["reason"],"transient_failure")
            self.assertEqual(ra.verify(d,c,"intelligence",i,rec["sha256"]),proof)
            (d/"intelligence.failure-1").write_text("{}")
            with self.assertRaises(ValueError):ra.verify(d,c,"intelligence",i,rec["sha256"])
    def test_generic_scope_and_five_work_products(self):
        scope={"kind":"public_dataset","subject":"Unfamiliar material test","dois":["10.1145/3442188.3445922"],"values":[-9,5,2,7],"operations":["median","mean","range"]}
        self.assertEqual(validate_scope(scope),scope)
        self.assertEqual(independent(scope)["results"]["mean"],{"numerator":5,"denominator":4})
        for bad in (dict(scope,operations=["exec"]),dict(scope,values=[True,2]),dict(scope,url="https://example.org")):
            with self.assertRaises(ValueError):validate_scope(bad)
        records={scope["dois"][0]:{"doi":scope["dois"][0],"title":"Fixture","year":2021,"publisher":"Fixture"}}
        def contract(tool,scope,prior):
            if tool=="crossref_metadata":return records
            if tool=="bibliography_readback":return {"same_provider_readback_agrees":True,"records":1,"full_paper_or_second_provider_verified":False}
            raise ValueError("unapproved tool")
        with tempfile.TemporaryDirectory() as tmp,patch("plenum_ai.chief_contract_plan.run_contract",side_effect=contract):
            d=Path(tmp);prior={}
            for role in sm.MISSION_ORDER:prior[role]=sm.mission_worker(role,prior,d,scope)
            self.assertEqual(sum(len(x["profile_receipts"]) for x in prior.values()),10)
            self.assertTrue(prior["verification"]["result"]["independent_actual_input_test"])
if __name__=="__main__":unittest.main(verbosity=2)
