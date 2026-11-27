"""Offline handoff tests: no model or board actions."""
import tempfile,unittest
from pathlib import Path
from uuid import uuid4
from checkpoint_store import exclusive,encoded
from hashlib import sha256
from failure_handoff import publish,ROLES
class HandoffTest(unittest.TestCase):
    def test_completed_and_unstarted_separate_and_no_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);c,m=str(uuid4()),str(uuid4())
            tasks={r:str(uuid4()) for r in ROLES}
            exclusive(p/"minister-plan.json",{"company":c,"parent":m,"order":list(ROLES),"tasks":tasks})
            for r in ("intelligence","research"):
                row={"company":c,"role":r,"issue":tasks[r]}
                exclusive(p/(r+".attempt-1"),{**row,"attempt":1})
                if r=="intelligence":
                    value={"public":True}
                    exclusive(p/(r+".json"),{**row,"result":value,"sha256":sha256(encoded(value)).hexdigest()})
            proof=publish(p,c,m,"a"*64,[])
            self.assertEqual(set(proof["completed_receipts"]),{"intelligence"})
            self.assertEqual(proof["reserved_unfinished"],["research"])
            self.assertEqual(proof["no_local_reservation_observed"],["engineering","commercial","verification"])
            self.assertFalse(proof["mission_accepted"])
            self.assertFalse(proof["automatic_replay_authorized"])
            with self.assertRaises(FileExistsError):publish(p,c,m,"a"*64,[])
    def test_native_recovery_retains_only_typed_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);c,m=str(uuid4()),str(uuid4())
            diagnostic={"division":"verification","diagnostic":{
                "id":str(uuid4()),"status":"failed","errorCode":"setup_failed",
                "exitCode":None,"native_recovery":{"kind":"bootstrap",
                "provider_work_started":False,"identity_matches":True,
                "observed_run_matches":"false","finished":True,"detail_error":False,
                "raw_context":"must-not-be-retained"}}}
            proof=publish(p,c,m,"a"*64,[diagnostic])
            self.assertEqual(proof["diagnostics"][0]["native_recovery"],{
                "kind":"bootstrap","provider_work_started":False,
                "identity_matches":True,"observed_run_matches":None,
                "finished":True,"detail_error":False})
            self.assertFalse(proof["automatic_replay_authorized"])
            self.assertFalse(proof["mission_accepted"])
    def test_rejects_corrupt_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);c,m=str(uuid4()),str(uuid4());tasks={r:str(uuid4()) for r in ROLES}
            exclusive(p/"minister-plan.json",{"company":c,"parent":m,"order":list(ROLES),"tasks":tasks})
            exclusive(p/"intelligence.json",{"company":c,"role":"intelligence","issue":tasks["intelligence"],"result":{},"sha256":"bad"})
            with self.assertRaises(ValueError):publish(p,c,m,"a"*64,[])
            self.assertFalse((p/"failure-handoff.json").exists())
if __name__=="__main__":unittest.main()
