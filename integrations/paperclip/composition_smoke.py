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
        dimensions={"orders":{"order":1},"cartons_per_order":{"carton":1,"order":-1},"cartons_per_pallet":{"carton":1,"pallet":-1},"total_cartons":{"carton":1},"pallet_count":{"pallet":1}}
        integer_outputs=outputs
        expected={"results":{"total_cartons":quantity(102),"pallet_count":quantity(6)},
                  "holdout":{"total_cartons":quantity(92),"pallet_count":quantity(7)}}
    elif case=="composition-energy":
        objective="Find the nominal battery energy in watt hours and how long the battery could ideally power the specified load in hours."
        values={"voltage":48,"amp_hours":75,"load_watts":800}
        holdout={"voltage":24,"amp_hours":120,"load_watts":480}
        outputs=["battery_energy","runtime_hours"]
        dimensions={"voltage":{"energy":1,"charge":-1},"amp_hours":{"charge":1},"load_watts":{"energy":1,"time":-1},"battery_energy":{"energy":1},"runtime_hours":{"time":1}}
        integer_outputs=[]
        expected={"results":{"battery_energy":quantity(3600),"runtime_hours":quantity(9,2)},
                  "holdout":{"battery_energy":quantity(2880),"runtime_hours":quantity(6)}}
    else:raise ValueError("Unknown independent fixture")
    return {"kind":"public_objective","objective":objective,"dois":["10.1145/3442188.3445922"],
            "inputs":{"composition":{"values":values,"holdout":holdout,"outputs":outputs,"dimensions":dimensions,"integer_outputs":integer_outputs}},
            "result_commitment":hash_value(expected)}

def smoke():
    from mission_scope import validate_scope
    for case,expr in [
      ("composition-logistics",{"total_cartons":"orders*cartons_per_order","pallet_count":"ceil(total_cartons/cartons_per_pallet)"}),
      ("composition-energy",{"battery_energy":"voltage*amp_hours","runtime_hours":"battery_energy/load_watts"})]:
        s=validate_scope(scope(case));data=accept_choice(s,expr)
        assert analyze(data)==independent(data)
        for invalid in ["__import__('os')","orders**99","unknown","1","1/0","[1]","ceil(orders,2)","ceil(x=orders)","round(orders)"]:
            bad=dict(expr);bad[next(iter(bad))]=invalid
            try:accept_choice(s,bad)
            except (ValueError,TypeError,SyntaxError,ZeroDivisionError):pass
            else:raise AssertionError("Invalid expression accepted")
    from composition_contract import normalize,request_for,convert
    assert normalize({"x":" math.ceil( a / b ) "})=={"x":"ceil( a / b )"}
    for invalid in ["os.system(x)", "a=2", "a; b"]:
        try:normalize({"x":invalid})
        except ValueError:pass
        else:raise AssertionError("Unsafe normalization")
    request=request_for(scope("composition-energy"),1,None)
    feedback={"category":"Independent actual and held-out answer commitment mismatch","previous_expressions":{"battery_energy":"voltage+amp_hours","runtime_hours":"battery_energy/load_watts"}}
    second=request_for(scope("composition-energy"),2,feedback)
    third=request_for(scope("composition-energy"),3,feedback)
    assert len({hash_value(x) for x in (request,second,third)})==3
    assert all("holdout" not in json.loads(x["messages"][1]["content"]) for x in (request,second,third))
    from composition_units import candidate_expressions,verify_expressions
    for case,choice in [
        ("composition-logistics",{"total_cartons":"cartons_per_order*orders","pallet_count":"ceil(total_cartons/cartons_per_pallet)"}),
        ("composition-energy",{"battery_energy":"amp_hours*voltage","runtime_hours":"battery_energy/load_watts"})]:
        fixture=scope(case);c=fixture["inputs"]["composition"]
        assert analyze(accept_choice(fixture,convert(fixture,choice,1)))==independent(accept_choice(fixture,convert(fixture,choice,1)))
        opts=candidate_expressions(c)
        if case=="composition-energy":
            assert opts=={"battery_energy":["amp_hours*voltage"],"runtime_hours":["battery_energy/load_watts"]}
            bad={"battery_energy":"load_watts*amp_hours","runtime_hours":"battery_energy/load_watts"}
            try:verify_expressions(c,bad)
            except ValueError:pass
            else:raise AssertionError("Wrong physical dimensions accepted")
        # Original untyped scopes retain both symbolic and structured planning.
        untyped=dict(fixture,inputs={"composition":{k:v for k,v in c.items() if k not in ("dimensions","integer_outputs")}})
        assert accept_choice(untyped,choice)
        assert analyze(accept_choice(untyped,choice))==independent(accept_choice(untyped,choice))
        req=request_for(fixture,1,None)
        assert "holdout" not in json.loads(req["messages"][1]["content"])
    print("Independent compositional grammar, two domains, correction request binding and held-out results passed")
if __name__=="__main__":
    if len(sys.argv)==2:print(json.dumps(scope(sys.argv[1]),separators=(",",":")))
    else:smoke()
