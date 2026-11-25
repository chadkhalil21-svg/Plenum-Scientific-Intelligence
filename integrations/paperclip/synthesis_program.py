"""Pure reviewed synthesis interpreter: source-bound extracts and comparisons.
No network, eval, arbitrary actions or claims of truth from source disagreement.
"""
import hashlib
import json
import sys

LIMITATIONS=['Exact excerpts are source-grounded, not independently established as true.',
             'Conflict is classified only for explicit single-valued claims in the same context.',
             'Unstructured evidence is extracted without inferring semantic contradiction.']


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def hash_value(value):return hashlib.sha256(canonical(value)).hexdigest()


def cite(record):
    return {'citation':record['id'],'document':record['document'],'start':record['start'],'end':record['end'],
            'quote':record['quote'],'source_sha256':hash_value(record)}


def analyze(data):
    records={record['id']:record for record in data['records']}
    comparisons=[];extracts=[];used=set()
    for item in data['plan']:
        ids=item['citations'];used.update(ids)
        if item['type']=='extract':
            extracts.append(cite(records[ids[0]]));continue
        claims=[]
        for key in ids:
            record=records[key];claims.append(dict(cite(record),value=record['claim']['value']))
        relation='agreement' if len({claim['value'] for claim in claims})==1 else 'conflict'
        comparisons.append({'subject':item['subject'],'attribute':item['attribute'],
                            'context':item['context'],'relation':relation,'claims':claims})
    return {'comparisons':comparisons,'extracts':extracts,'unused_citations':sorted(set(records)-used),
            'limitations':LIMITATIONS,'external_actions_executed':False,'paid_inference':False}


if __name__=='__main__':
    if sys.argv[1:]!=['collections']:raise ValueError('Only reviewed synthesis interpreter')
    print(json.dumps(analyze(json.load(sys.stdin)),sort_keys=True))
