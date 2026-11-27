"""Mocked transport receipt tests. Actual Qwen and native board are NOT exercised."""
from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from synthesis_contract import plan,receipt,digest,encoded,request_for,request_v1
from synthesis_smoke import scope,fixture_selection


def main():
    comparison=scope()
    assert request_for(comparison,1)==request_v1(comparison,1)
    assert request_for(comparison,2,fixture_selection(comparison))==request_v1(comparison,2,fixture_selection(comparison))
    # A different, standalone extraction fixture; no comparison candidates.
    s=scope();s['objective']='Extract the buyer approval condition and the warehouse access restriction.'
    s['inputs']={'synthesis':{'documents':{'buyer':'Buyer approval requires a signed order. The buyer prefers blue stationery.',
        'warehouse':'Warehouse access requires a badge.'}}}
    expected=[{'type':'extract','citations':[x]} for x in ('buyer_1','warehouse_1')]
    s['result_commitment']=digest(sorted(expected,key=encoded))
    company='synthetic-company';parent='synthetic-parent'
    selected={'extract_buyer_1':True,'extract_buyer_2':False,'extract_warehouse_1':True}
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
        for i,r in enumerate(calls,1):
            payload=json.loads(r['messages'][1]['content'])
            assert len(payload['candidate_reviews'])==len(selected)
            assert {v['key'] for v in payload['candidate_reviews']}==set(selected)
            assert all(v['evidence'] for v in payload['candidate_reviews'])
            assert all(('previous_decision' in v)==(i==2) for v in payload['candidate_reviews'])
            assert json.loads((d/f'synthesis-attempt-{i}.json').read_text())['request_version']==2
        # Historic receipts must reconstruct the original requests without inference.
        saved={p:p.read_bytes() for p in d.glob('synthesis-attempt-*.json')}
        rejection=d/'synthesis-rejection-1.json';saved[rejection]=rejection.read_bytes()
        for p,raw in saved.items():
            row=json.loads(raw);i=row['index'];row.pop('request_version')
            row['request_sha256']=digest(request_v1(s,i,None if i==1 else rejected))
            p.write_bytes(encoded(row))
        assert receipt(d,s,company,parent)==accepted and len(calls)==2
        for p,raw in saved.items():p.write_bytes(raw)
        # Unknown or mixed request versions must fail closed.
        p=d/'synthesis-attempt-2.json';old=p.read_bytes()
        bad=json.loads(old);bad['request_version']=1;p.write_bytes(encoded(bad))
        try:receipt(d,s,company,parent)
        except ValueError:pass
        else:raise AssertionError('Mixed request versions accepted')
        p.write_bytes(old)
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
