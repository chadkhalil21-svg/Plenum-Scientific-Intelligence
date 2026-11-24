import os,tempfile,unittest,json
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock,patch
from checkpoint_store import checked,exclusive
from production_wiring import prepared
from supervisor_resume import validate_resume,finalize
from mission_scope import validate_scope
from objective_mission import independent,evaluate,SOURCE,TOOLS
from model_plan import digest

class Tests(unittest.TestCase):
    def test_assigned_only_no_write(self):
        c,m,l=(str(uuid4()) for _ in range(3))
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);binding={"scope_sha256":"a"*64,"parent_title":"title","parent_description":"desc"}
            prepared(d,c,m,binding["scope_sha256"],"local","local")
            exclusive(d/"activation.json",{"company":c,"mission":m,"minister":l,"scope_sha256":binding["scope_sha256"],"model_mode":"local","remote_checkpoint_preflight":False})
            row={"id":m,"companyId":c,"parentId":None,"assigneeAgentId":l,"status":"in_progress","title":"title","description":"desc"}
            api=Mock(return_value=row)
            self.assertEqual(validate_resume(api,d,c,m,l,binding),row)
            api.assert_called_once_with("/api/issues/"+m)
            for field,value in (("assigneeAgentId",None),("status","cancelled"),("description","changed"),("companyId",str(uuid4()))):
                api.return_value={**row,field:value}
                with self.assertRaises(ValueError):validate_resume(api,d,c,m,l,binding)
    def test_atomic_finalization_readback(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{"PLENUM_ISSUE_CREATED_AT":""}):
            d=Path(tmp);q={"parent":str(uuid4()),"paid_inference":False,"minister_model_executed":True,"verified_divisions":5}
            import time
            with patch("supervisor_resume.exclusive",side_effect=lambda p,v: (_ for _ in ()).throw(RuntimeError("interrupted")) if p.name=="qualification.json" else exclusive(p,v)):
                with self.assertRaises(RuntimeError):finalize(d,q,time.monotonic(),time.monotonic(),resuming=True)
            self.assertFalse((d/"qualification.json").exists())
            t=checked(d/"event-timing.json",{"qualification_sha256":digest(q)})
            self.assertIsNone(t["native_assignment_to_verified_seconds"])
            self.assertEqual(finalize(d,q,0,0,resuming=True),t)
            self.assertEqual(finalize(d,q,0,0,resuming=True),t)
            self.assertEqual(checked(d/"qualification.json",q),q)
            with self.assertRaises(ValueError):finalize(d,{**q,"verified_divisions":4},0,0,resuming=True)
    def test_strict_checkpoint_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);p=d/"record"
            for raw in ('{"x":true,"x":false}','{"x":NaN}','{"x":1}','[]'):
                p.write_text(raw)
                with self.assertRaises(ValueError):checked(p,{"x":True})
            p.unlink();os.mkfifo(p)
            with self.assertRaises(ValueError):checked(p,{})
            p.unlink();p.symlink_to(d/"missing")
            with self.assertRaises(ValueError):checked(p,{})
    def test_new_exact_engineering_operations(self):
        scope={"kind":"public_objective","objective":"Quantify engineering sample drift and stability","dois":["10.1145/3442188.3445922"],"inputs":{"samples":[1,3,5,7]},"operations":["population_variance","least_squares_slope","max_step_change"]}
        validate_scope(scope);data={**scope["inputs"],"operations":scope["operations"]}
        expected={"results":{"population_variance":{"numerator":5,"denominator":1},"least_squares_slope":{"numerator":2,"denominator":1},"max_step_change":{"numerator":2,"denominator":1}}}
        self.assertEqual(independent(data),expected)
        for tool in TOOLS:self.assertEqual(evaluate(SOURCE,data,tool),expected)
        for samples in ([10,-3,4,9],[-10,-10],[10**9,-10**9]):
            case={**data,"samples":samples}
            for tool in TOOLS:self.assertEqual(evaluate(SOURCE,case,tool),independent(case))
if __name__=="__main__":unittest.main(verbosity=2)
