"""Reviewed offline scientific/engineering/commercial operation DAG.

No model-generated code, URLs, paths or side effects. Exact rational arithmetic.
"""
import hashlib,json,sys
from fractions import Fraction
from math import ceil

DEPENDENCIES={
    "paired_removed_mass":(), "removal_efficiency":("paired_removed_mass",),
    "worst_pair_efficiency":(), "mean_influent":(),
    "effective_capacity":(), "module_count":("effective_capacity",),
    "energy_requirement":("module_count",), "reserve_capacity":("effective_capacity","module_count"),
    "daily_operating_cost":(), "daily_margin":("daily_operating_cost",),
    "payback_days":("daily_margin",), "annual_margin":("daily_margin",)
}
STAGES={
    "science":("paired_removed_mass","removal_efficiency","worst_pair_efficiency","mean_influent"),
    "engineering":("effective_capacity","module_count","energy_requirement","reserve_capacity"),
    "commercial":("daily_operating_cost","daily_margin","payback_days","annual_margin")
}

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def rational(value):
    x=Fraction(value)
    return {"numerator":x.numerator,"denominator":x.denominator}

def fraction(row):
    return Fraction(row["numerator"],row["denominator"])

def analyze(data,tool):
    if tool!="collections":raise ValueError("Only reviewed exact rational engine")
    pipeline=data["pipeline"];stage=pipeline["stage"];p=pipeline["parameters"]
    prior=pipeline["prior"];ops=data["operations"]
    if not isinstance(ops,list) or len(set(ops))!=len(ops) or not ops or not set(ops)<=set(STAGES[stage]):raise ValueError("Pipeline operation scope")
    if any(not set(DEPENDENCIES[op])<=set(ops) for op in ops):raise ValueError("Missing operation dependency")
    values={};steps=[]
    while len(values)<len(ops):
        ready=sorted(op for op in ops if op not in values and set(DEPENDENCIES[op])<=set(values))
        if not ready:raise ValueError("Cyclic operation graph")
        op=ready[0];deps=DEPENDENCIES[op]
        if stage=="science":
            controls=p["control_mg"];treated=p["treated_mg"]
            if op=="paired_removed_mass":v=sum(c-t for c,t in zip(controls,treated))
            elif op=="removal_efficiency":v=values["paired_removed_mass"]/sum(controls)
            elif op=="worst_pair_efficiency":v=min(Fraction(c-t,c) for c,t in zip(controls,treated))
            elif op=="mean_influent":v=Fraction(sum(controls),len(controls))
            else:raise ValueError("Wrong science operation")
        elif stage=="engineering":
            if op=="effective_capacity":v=p["nominal_mg_day"]*fraction(prior["outcomes"]["worst_pair_efficiency"])
            elif op=="module_count":v=ceil(Fraction(p["target_mg_day"])/values["effective_capacity"])
            elif op=="energy_requirement":v=values["module_count"]*p["energy_wh_module_day"]
            elif op=="reserve_capacity":v=values["effective_capacity"]*values["module_count"]-p["target_mg_day"]
            else:raise ValueError("Wrong engineering operation")
        else:
            units=fraction(prior["outcomes"]["module_count"]);energy=fraction(prior["outcomes"]["energy_requirement"])
            if op=="daily_operating_cost":v=energy*p["tariff_cents_kwh"]/1000+units*p["labor_cents_module_day"]
            elif op=="daily_margin":v=p["revenue_cents_day"]-values["daily_operating_cost"]
            elif op=="payback_days":
                if values["daily_margin"]<=0:raise ValueError("Nonpositive margin has no finite payback")
                v=ceil(units*p["capital_cents_module"]/values["daily_margin"])
            elif op=="annual_margin":v=365*values["daily_margin"]
            else:raise ValueError("Wrong commercial operation")
        values[op]=Fraction(v)
        steps.append({"operation":op,"depends_on":list(deps),
                      "input_sha256":digest({"pipeline":pipeline,"predecessors":{k:rational(values[k]) for k in deps}}),
                      "output_sha256":digest(rational(v))})
    return {"results":{k:rational(v) for k,v in values.items()},"steps":steps}

if __name__=="__main__":
    print(json.dumps(analyze(json.load(sys.stdin),sys.argv[1]),sort_keys=True,allow_nan=False))
