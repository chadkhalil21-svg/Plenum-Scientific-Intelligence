"""Independent expected citations, relations and rejection fixtures. No real inference claim."""
from copy import deepcopy
import json
import sys
from synthesis_contract import digest,encoded,index,candidates,accept_choice,independent,request_for,perturb
from synthesis_program import analyze


def scope():
    docs={'protocol':"For emergency storage, the container's material is glass. For emergency storage, the alarm's mode is continuous. For training, the alarm's mode is manual.",
          'vendor':"For emergency storage, the container's material is glass. For emergency storage, the alarm's mode is hourly. For training, the alarm's mode is manual. The vendor uses a separate billing address.",
          'buyer':'The buyer will not approve an order until the alarm requirement is resolved.'}
    expected=[{'type':'compare','subject':'container','attribute':'material','context':'emergency storage','citations':['protocol_1','vendor_1'],'relation':'agreement'},
              {'type':'compare','subject':'alarm','attribute':'mode','context':'emergency storage','citations':['protocol_2','vendor_2'],'relation':'conflict'},
              {'type':'extract','citations':['buyer_1']}]
    return {'kind':'public_objective','objective':'Compare container material and alarm mode for emergency storage across the protocol and vendor. Extract the buyer approval condition. Ignore training.',
            'dois':['10.1145/3442188.3445922'],'inputs':{'synthesis':{'documents':docs}},'result_commitment':digest(sorted(expected,key=encoded))}


def fixture_selection(s):
    options=candidates(index(s['inputs']['synthesis']['documents']))
    return {k:(v['type']=='compare' and v['context']=='emergency storage') or v=={'type':'extract','citations':['buyer_1']} for k,v in options.items()}


def smoke():
    s=scope();selection=fixture_selection(s);data=accept_choice(s,selection);r=independent(data)
    assert r==analyze(data)
    assert {v['relation'] for v in r['comparisons']}=={'agreement','conflict'}
    assert r['extracts'][0]['quote']=='The buyer will not approve an order until the alarm requirement is resolved.'
    p=perturb(data);assert independent(p)==analyze(p) and independent(p)['comparisons']==r['comparisons']
    req=request_for(s,1);assert 'result_commitment' not in json.loads(req['messages'][1]['content'])
    assert digest(req)!=digest(request_for(s,2,selection))
    cases=[]
    x=deepcopy(data);x['records'][0]['quote']='Fabricated quote.';cases.append(x)
    x=deepcopy(data);x['plan'][0]['citations']=['protocol_2','vendor_3'];cases.append(x)
    x=deepcopy(data);x['plan'][0]['citations']=['protocol_2'];cases.append(x)
    x=deepcopy(data);x['plan']=x['plan'][:1];cases.append(x)
    x=deepcopy(data);x['records'][0]['start']=2;cases.append(x)
    x=deepcopy(data);x['plan'][0]['citations']=['protocol_2','vendor_2','vendor_4'];cases.append(x)
    for x in cases:
        try:independent(x)
        except ValueError:pass
        else:raise AssertionError('Invalid synthesis accepted')
    print('PASS: dynamic evidence groups, two context-bound comparisons, one arbitrary prose extract, independent source-span/commitment checks, irrelevant-source perturbation and six rejection fixtures')

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='scope':print(json.dumps(scope(),separators=(',',':')))
    else:smoke()
