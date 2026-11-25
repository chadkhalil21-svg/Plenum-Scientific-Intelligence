"""Reject forged or cross-run memory; offline fixtures only."""
import copy,hashlib,tempfile,unittest,json
from pathlib import Path
from uuid import uuid4
from checkpoint_store import encoded
from pipeline_fixtures import KINDS,scope
from pipeline_smoke import EXPECTED
from objective_mission import independent
from mission_scope import digest
from public_handoff import consume
RUN="123";COMMIT="a"*40
def fixture():
    missions={}
    for index,kind in enumerate(KINDS,1):
        s=scope(kind);data={**s["inputs"],"operations":sorted(EXPECTED[kind])}
        missions[kind]={"scope":s,"input":data,"validation":independent(data),"engineering_sha256":"a"*64,
            "acceptance":{"company":str(uuid4()),"mission":str(uuid4()),"scope_sha256":digest(s),
            "qualification_sha256":str(index)*64,"verified_divisions":5,"verified_profile_work_products":11,
            "model_receipt_verified":True,"independent_actual_input_test":True,
            "provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False}}
    return {"schema":"plenum-public-mission-memory-v1","run_id":RUN,"commit":COMMIT,
            "acceptance_sha256":"b"*64,"missions":missions,"paid_inference":False}
class Tests(unittest.TestCase):
    def test_continuation_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/"memory.json";out=root/"result.json"
            good=fixture();p.write_bytes(encoded(good));sha=hashlib.sha256(p.read_bytes()).hexdigest()
            consume(p,out,RUN,COMMIT,sha)
            r=json.loads(out.read_text())
            self.assertEqual(r["result"],{k:{"numerator":v,"denominator":1} for k,v in
                {"expanded_units":125,"additional_units":25,"annual_avoided_methane_kg":4380,"annual_operating_profit_usd":2025}.items()})
            with self.assertRaises(FileExistsError):consume(p,out,RUN,COMMIT,sha)
            with self.assertRaises(ValueError):consume(p,root/"bad.json","124",COMMIT,sha)
            changed=copy.deepcopy(good);changed["missions"]["scientific"]["validation"]["results"]["relative_reduction"]["numerator"]=8
            p.write_bytes(encoded(changed))
            with self.assertRaises(ValueError):consume(p,root/"bad.json",RUN,COMMIT,sha)
            with self.assertRaises(ValueError):consume(p,root/"bad.json",RUN,COMMIT,hashlib.sha256(p.read_bytes()).hexdigest())
            changed=copy.deepcopy(good);changed["missions"]["engineering"]["acceptance"]["provider_calls_replayed"]=1
            p.write_bytes(encoded(changed))
            with self.assertRaises(ValueError):consume(p,root/"bad.json",RUN,COMMIT,hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=="__main__":unittest.main(verbosity=2)
