"""Independent expected outputs, not plan templates; no model or provider calls."""
import json
import sys
from composition_contract import accept_choice,hash_value,independent
from composition_program import analyze

def quantity(n,d=1):return {"numerator":n,"denominator":d}

def scope(case):
    if case=="composition-logistics":
        objective="How many cartons are required for the orders and what is the minimum number of whole pallets needed to carry them?"
        values={"orders":17,"cartons_per_order":6,"cartons_per_pallet":20}
        holdout={"orders":23,"cartons_per_order":4,"cartons_per_pallet":15}
        outputs=["total_cartons","pallet_count"]
        expected={"results":{"total_cartons":quantity(102),"pallet_count":quantity(6)},
                  "holdout":{"total_cartons":quantity(92),"pallet_count":quantity(7)}}
    elif case=="composition-energy":
        objective="Find the nominal battery energy in watt hours and how long the battery could ideally power the specified load in hours."
        values={"voltage":48,"amp_hours":75,"load_watts":800}
        holdout={"voltage":24,"amp_hours":120,"load_watts":480}
        outputs=["battery_energy","runtime_hours"]
        expected={"results":{"battery_energy":quantity(3600),"runtime_hours":quantity(9,2)},
                  "holdout":{"battery_energy":quantity(2880),"runtime_hours":quantity(6)}}
    else:raise ValueError("Unknown independent fixture")
    return {"kind":"public_objective","objective":objective,"dois":["10.1145/3442188.3445922"],
            "inputs":{"composition":{"values":values,"holdout":holdout,"outputs":outputs}},
            "result_commitment":hash_value(expected)}

def smoke():
    from mission_scope import validate_scope
    for case,expr in [
      ("composition-logistics",{"total_cartons":"orders*cartons_per_order","pallet_count":"(total_cartons+cartons_per_pallet-1)//cartons_per_pallet"}),
      ("composition-energy",{"battery_energy":"voltage*amp_hours","runtime_hours":"battery_energy/load_watts"})]:
        s=validate_scope(scope(case));data=accept_choice(s,expr)
        assert analyze(data)==independent(data)
        for invalid in ["__import__('os')","orders**99","unknown","1","1/0","[1]"]:
            bad=dict(expr);bad[next(iter(bad))]=invalid
            try:accept_choice(s,bad)
            except (ValueError,TypeError,SyntaxError,ZeroDivisionError):pass
            else:raise AssertionError("Invalid expression accepted")
    print("Independent compositional grammar, two domains and held-out results passed")
if __name__=="__main__":
    if len(sys.argv)==2:print(json.dumps(scope(sys.argv[1]),separators=(",",":")))
    else:smoke()
