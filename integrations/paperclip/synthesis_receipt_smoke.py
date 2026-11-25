"""Mocked transport receipt tests. Actual Qwen and native board are NOT exercised."""
from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from synthesis_contract import plan,receipt,digest,encoded
from synthesis_smoke import scope,fixture_selection


def main():
    s=scope();company='synthetic-company';parent='synthetic-parent';selected=fixture_selection(s)
    rejected=dict(selected);rejected['extract_buyer_1']=False
    calls=[]
    def checked(path,expected):
        row=json.loads(Path(path).read_text())
        if any(k not in row or row[k]!=v for k,v in expected.items()):raise ValueError('Fixture checkpoint binding')
        return row
    def exclusive(path,value):
        with Path(path).open('xb') as stream:stream.write(encoded(value))
    def read_json(path,request,timeout):
        calls.append(request);choice=rejected if len(calls)==1 else selected
        if len(calls)>2:raise AssertionError('Unexpected model replay')
        return {'done':True,'model':'qwen3.5:4b','message':{'content':json.dumps(choice)},'eval_count':70}
    modules={'checkpoint_store':SimpleNamespace(checked=checked,exclusive=exclusive),
             'mission_scope':SimpleNamespace(digest=digest),
             'model_plan':SimpleNamespace(MODEL='qwen3.5:4b',valid_digest=lambda v:v=='a'*64,check_local_model=lambda:'a'*64,read_json=read_json),
             'production_wiring':SimpleNamespace(load_prepared=lambda *a:{'model_mode':'local','scope_sha256':digest(s)})}
    with patch.dict(sys.modules,modules),tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);exclusive(d/'activation.json',{'company':company,'mission':parent,'scope_sha256':digest(s),'model_mode':'local'})
        accepted=plan(d,s,company,parent);assert accepted['attempts']==2 and len(calls)==2 and digest(calls[0])!=digest(calls[1])
        assert receipt(d,s,company,parent)==accepted and plan(d,s,company,parent)==accepted and len(calls)==2
        assert all('result_commitment' not in json.loads(r['messages'][1]['content']) for r in calls)
        p=d/'synthesis-rejection-1.json';old=p.read_bytes();tampered=json.loads(old);tampered['request_sha256']='b'*64;p.write_bytes(encoded(tampered))
        try:receipt(d,s,company,parent)
        except ValueError:pass
        else:raise AssertionError('Tampered attempt accepted')
        p.write_bytes(old);(d/'synthesis-plan.json').unlink()
        try:plan(d,s,company,parent)
        except PermissionError:pass
        else:raise AssertionError('Ambiguous previous inference replayed')
        assert len(calls)==2
    print('PASS: mocked rejected-then-accepted selection, distinct requests, immutable reservation validation, tamper rejection, zero readback replay and ambiguous-call rejection')

if __name__=='__main__':main()
