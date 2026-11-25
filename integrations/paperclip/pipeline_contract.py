"""Independent scope and outcome contract for the multidisciplinary DAG."""
import re
from fractions import Fraction
from hashlib import sha256
from math import gcd
from checkpoint_store import encoded

OPS={
    "science":("paired_removed_mass","removal_efficiency","worst_pair_efficiency","mean_influent"),
    "engineering":("effective_capacity","module_count","energy_requirement","reserve_capacity"),
    "commercial":("daily_operating_cost","daily_margin","payback_days","annual_margin")
}
DEPS={"paired_removed_mass":(),"removal_efficiency":("paired_removed_mass",),"worst_pair_efficiency":(),"mean_influent":(),
      "effective_capacity":(),"module_count":("effective_capacity",),"energy_requirement":("module_count",),"reserve_capacity":("effective_capacity","module_count"),
      "daily_operating_cost":(),"daily_margin":("daily_operating_cost",),"payback_days":("daily_margin",),"annual_margin":("daily_margin",)}
EXPORTS={"science":{"worst_pair_efficiency","removal_efficiency","paired_removed_mass"},
         "engineering":{"module_count","energy_requirement","effective_capacity"},
         "commercial":{"daily_operating_cost","daily_margin","payback_days"}}
PREVIOUS={"science":None,"engineering":"science","commercial":"engineering"}
DIGEST=re.compile(r"[0-9a-f]{64}")
COMMIT=re.compile(r"[0-9a-f]{40}")
DEFINITIONS={
    "paired_removed_mass":"sum of paired control minus treated masses in milligrams",
    "removal_efficiency":"total removed mass divided by total control mass",
    "worst_pair_efficiency":"minimum fractional removal across individual pairs",
    "mean_influent":"mean of the original control masses",
    "effective_capacity":"nominal removal capacity times verified conservative efficiency",
    "module_count":"minimum integer modules to reach the target with effective capacity",
    "energy_requirement":"total daily electricity in Wh for required modules",
    "reserve_capacity":"installed effective capacity above the target",
    "daily_operating_cost":"daily electricity and labor expense in cents",
    "daily_margin":"daily revenue minus daily operating expense in cents",
    "payback_days":"whole days required to recover installed module capital at positive daily margin",
    "annual_margin":"365 times daily margin, without discounting"
}
CUES={
    "paired_removed_mass":(r"\b(?:paired|total) removed mass\b",),
    "removal_efficiency":(r"\b(?:overall|aggregate) removal efficiency\b",),
    "worst_pair_efficiency":(r"\b(?:worst.pair|minimum.pair|conservative) efficiency\b",),
    "mean_influent":(r"\b(?:mean|average) influent\b",),
    "effective_capacity":(r"\beffective capacity\b",),
    "module_count":(r"\b(?:module count|required modules|number of modules)\b",),
    "energy_requirement":(r"\b(?:daily energy requirement|daily electricity demand|energy demand)\b",),
    "reserve_capacity":(r"\b(?:reserve|excess|spare) capacity\b",),
    "daily_operating_cost":(r"\bdaily operating cost\b",),
    "daily_margin":(r"\bdaily margin\b",),
    "payback_days":(r"\b(?:whole.day payback|payback days|capital payback)\b",),
    "annual_margin":(r"\bannual margin\b",)
}

def digest(x):return sha256(encoded(x)).hexdigest()

def bounded_int(v,low=1,high=10**9):
    return type(v) is int and low<=v<=high

def fraction(v):
    if (not isinstance(v,dict) or set(v)!={"numerator","denominator"} or
        not bounded_int(v["numerator"],-10**18,10**18) or not bounded_int(v["denominator"],1,10**18) or
        gcd(v["numerator"],v["denominator"])!=1):raise ValueError("Noncanonical pipeline quantity")
    return Fraction(v["numerator"],v["denominator"])

def rational(v):
    v=Fraction(v);return {"numerator":v.numerator,"denominator":v.denominator}

def validate_memory(row,stage):
    fields={"schema","stage","run_id","commit","scope_sha256","qualification_sha256","previous_sha256","outcomes","fresh_runner_independent_acceptance","verified_divisions","verified_profile_work_products","provider_calls_replayed","model_calls_replayed","paid_inference"}
    if (not isinstance(row,dict) or set(row)!=fields or row["schema"]!="plenum-public-pipeline-memory-v1" or
        row["stage"]!=stage or not isinstance(row["run_id"],str) or not re.fullmatch(r"[1-9][0-9]{0,12}",row["run_id"]) or
        not isinstance(row["commit"],str) or not COMMIT.fullmatch(row["commit"]) or
        any(not isinstance(row[k],str) or not DIGEST.fullmatch(row[k]) for k in ("scope_sha256","qualification_sha256")) or
        row["fresh_runner_independent_acceptance"] is not True or type(row["verified_divisions"]) is not int or row["verified_divisions"]!=5 or
        type(row["verified_profile_work_products"]) is not int or row["verified_profile_work_products"]!=11 or
        any(type(row[k]) is not int or row[k]!=0 for k in ("provider_calls_replayed","model_calls_replayed")) or row["paid_inference"] is not False):
        raise ValueError("Invalid public memory receipt")
    if stage=="science":
        if row["previous_sha256"] is not None:raise ValueError("Unexpected first-stage predecessor")
    elif not isinstance(row["previous_sha256"],str) or not DIGEST.fullmatch(row["previous_sha256"]):raise ValueError("Missing predecessor digest")
    outcomes=row["outcomes"]
    if not isinstance(outcomes,dict) or not EXPORTS[stage]<=set(outcomes)<=set(OPS[stage]):raise ValueError("Invalid memory exports")
    for v in outcomes.values():fraction(v)
    if stage=="science":
        if not 0<fraction(outcomes["worst_pair_efficiency"])<=fraction(outcomes["removal_efficiency"])<=1:raise ValueError("Invalid removal efficiency")
    elif stage=="engineering":
        units=fraction(outcomes["module_count"])
        if units.denominator!=1 or units<=0 or fraction(outcomes["energy_requirement"])<=0:raise ValueError("Invalid engineering exports")
    return row

def validate(pipeline):
    if not isinstance(pipeline,dict) or set(pipeline)!={"stage","parameters","prior"} or pipeline["stage"] not in OPS:raise ValueError("Exact pipeline envelope required")
    stage=pipeline["stage"];p=pipeline["parameters"];prior=pipeline["prior"]
    if not isinstance(p,dict):raise ValueError("Exact pipeline parameters required")
    if stage=="science":
        if prior is not None or set(p)!={"control_mg","treated_mg"}:raise ValueError("Science inputs")
        c,t=p["control_mg"],p["treated_mg"]
        if (not isinstance(c,list) or not isinstance(t,list) or not 2<=len(c)<=32 or len(t)!=len(c) or
            any(not bounded_int(x) for x in c) or any(not bounded_int(y,0,x-1) for x,y in zip(c,t))):raise ValueError("Paired synthetic observations")
    else:
        validate_memory(prior,PREVIOUS[stage])
        fields={"target_mg_day","nominal_mg_day","energy_wh_module_day"} if stage=="engineering" else {"tariff_cents_kwh","labor_cents_module_day","revenue_cents_day","capital_cents_module"}
        if set(p)!=fields or any(not bounded_int(v) for v in p.values()):raise ValueError("Pipeline parameter bounds")
        if stage=="engineering":
            if Fraction(p["target_mg_day"])/(p["nominal_mg_day"]*fraction(prior["outcomes"]["worst_pair_efficiency"]))>10**6:raise ValueError("Module bound")
    return pipeline

def policy(pipeline,commitment):
    stage=validate(pipeline)["stage"];allowed=OPS[stage]
    return {"allowed":allowed,"required_groups":(allowed,),"commitment":commitment,
            "required_dependencies":{op:DEPS[op] for op in allowed}}

def independent(data):
    pipeline=validate(data["pipeline"]);stage=pipeline["stage"];p=pipeline["parameters"];prior=pipeline["prior"]
    ops=data["operations"]
    if not isinstance(ops,list) or not ops or len(set(ops))!=len(ops) or not set(ops)<=set(OPS[stage]) or any(not set(DEPS[op])<=set(ops) for op in ops):raise ValueError("Independent graph scope")
    if stage=="science":
        c,t=p["control_mg"],p["treated_mg"]
        vals={"paired_removed_mass":sum(c)-sum(t),"removal_efficiency":1-Fraction(sum(t),sum(c)),
              "worst_pair_efficiency":1-max(Fraction(y,x) for x,y in zip(c,t)),"mean_influent":Fraction(sum(c),len(c))}
    elif stage=="engineering":
        cap=Fraction(p["nominal_mg_day"])*fraction(prior["outcomes"]["worst_pair_efficiency"])
        q=Fraction(p["target_mg_day"])/cap;units=-(-q.numerator//q.denominator)
        if not ((units-1)*cap<p["target_mg_day"]<=units*cap):raise ValueError("Minimum sizing verification")
        vals={"effective_capacity":cap,"module_count":units,"energy_requirement":units*p["energy_wh_module_day"],"reserve_capacity":units*cap-p["target_mg_day"]}
    else:
        units=fraction(prior["outcomes"]["module_count"]);energy=fraction(prior["outcomes"]["energy_requirement"])
        cost=(energy*p["tariff_cents_kwh"]+1000*units*p["labor_cents_module_day"])/1000
        margin=p["revenue_cents_day"]-cost
        vals={"daily_operating_cost":cost,"daily_margin":margin,"annual_margin":margin*365}
        if "payback_days" in ops:
            if margin<=0:raise ValueError("Nonpositive margin")
            capital=units*p["capital_cents_module"];q=capital/margin;days=-(-q.numerator//q.denominator)
            if not ((days-1)*margin<capital<=days*margin):raise ValueError("Payback verification")
            vals["payback_days"]=days
    result={k:rational(vals[k]) for k in ops};steps=[];completed=set()
    while len(completed)<len(ops):
        ready=sorted(set(ops)-completed,key=str)
        op=next((k for k in ready if set(DEPS[k])<=completed),None)
        if op is None:raise ValueError("Invalid dependency graph")
        deps=DEPS[op]
        steps.append({"operation":op,"depends_on":list(deps),"input_sha256":digest({"pipeline":pipeline,"predecessors":{k:result[k] for k in deps}}),"output_sha256":digest(result[op])})
        completed.add(op)
    return {"results":result,"steps":steps}

def perturb(data):
    p=dict(data["pipeline"]["parameters"]);stage=data["pipeline"]["stage"]
    if stage=="science":
        p["treated_mg"]=[max(0,v-1) for v in p["treated_mg"]]
    elif stage=="engineering":
        p["target_mg_day"]=p["target_mg_day"]+1
    else:
        p["tariff_cents_kwh"]=p["tariff_cents_kwh"]+1
    return dict(data,pipeline=dict(data["pipeline"],parameters=p))
