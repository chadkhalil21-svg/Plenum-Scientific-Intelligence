"""New synthetic Terra pilot qualifications; source metadata is context only."""
import json,sys
from hashlib import sha256
from checkpoint_store import encoded
from mission_scope import validate_scope

def scope(kind):
    rows={
        "scientific":("Estimate relative reduction in synthetic paired cattle methane observations.",
            "10.1371/journal.pone.0247820",{"experiment":{"control":[320,300,340,320],"treatment":[224,210,238,224]}},["relative_reduction"]),
        "engineering":("Determine the reserve fraction of synthetic service capacity for three pilot cohorts.",
            "10.3390/methane4020009",{"design":{"loads":[30,45,25],"capacity":125}},["reserve_fraction"]),
        "commercial":("Calculate break-even units and operating profit for the synthetic annual pilot.",
            "10.3390/methane4020009",{"business":{"units":100,"price":120,"variable_cost":75,"fixed_cost":3600}},["break_even_units","operating_profit"])}
    objective,doi,inputs,terminal=rows[kind]
    return validate_scope({"kind":"public_objective","objective":objective,"dois":[doi],
        "inputs":inputs,"operation_commitment":sha256(encoded(sorted(terminal))).hexdigest()})

KINDS=("scientific","engineering","commercial")
if __name__=="__main__":print(json.dumps(scope(sys.argv[1]),sort_keys=True))
