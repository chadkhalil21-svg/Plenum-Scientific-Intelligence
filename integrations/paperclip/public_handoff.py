"""Public completed evidence continuity. GitHub/Sigstore signs exact accepted bytes."""
import os,sys,hashlib,re
from pathlib import Path
from fractions import Fraction
from checkpoint_store import checked,encoded,exclusive
from fresh_runner_acceptance import safe_tree,accept
from pipeline_fixtures import KINDS,scope
from objective_mission import independent
from mission_scope import digest as scope_digest
from lifecycle import canonical

def digest(x):return hashlib.sha256(encoded(x)).hexdigest()

def make(base,acceptance,output,run,commit):
    row=checked(acceptance,{"run_id":run,"commit":commit,"fresh_runner_independent_acceptance":True,
        "native_board_restored":False,"provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False})
    if set(row["accepted"])!={"local-"+kind for kind in KINDS}:raise ValueError("Wrong accepted mission set")
    missions={}
    for kind in KINDS:
        key="local-"+kind;root=base/("paperclip-native-public-evidence-"+key)
        safe_tree(root);proof=accept(root,run,commit,scope(kind))
        if proof!=row["accepted"][key]:raise ValueError("Fresh acceptance proof changed")
        cid,mid=canonical(proof["company"]),canonical(proof["mission"])
        directory=root/cid/mid
        eng=checked(directory/"engineering.json",{"company":cid,"role":"engineering"})
        if digest(eng["result"])!=eng["sha256"]:raise ValueError("Engineering receipt changed")
        result=eng["result"]["result"]
        missions[kind]={"scope":scope(kind),"acceptance":proof,"engineering_sha256":eng["sha256"],
                        "input":result["input"],"validation":result["validation"]}
    exclusive(output,{"schema":"plenum-public-mission-memory-v1","run_id":run,"commit":commit,
             "acceptance_sha256":digest(row),"missions":missions,"paid_inference":False})

def consume(path,output,run,commit,expected_sha):
    if not re.fullmatch(r"[0-9]+",run) or not re.fullmatch(r"[0-9a-f]{40}",commit) or not re.fullmatch(r"[0-9a-f]{64}",expected_sha):
        raise ValueError("Invalid source identity")
    memory=checked(path,{"schema":"plenum-public-mission-memory-v1","run_id":run,"commit":commit,"paid_inference":False})
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected_sha:raise ValueError("Memory digest changed")
    if set(memory)!={"schema","run_id","commit","acceptance_sha256","missions","paid_inference"} or set(memory["missions"])!=set(KINDS):
        raise ValueError("Wrong memory envelope")
    if not isinstance(memory["acceptance_sha256"],str) or not re.fullmatch(r"[0-9a-f]{64}",memory["acceptance_sha256"]):raise ValueError("Missing acceptance digest")
    records=memory["missions"];proofs={}
    def step(kind,name):
        matches=[x["value"] for x in records[kind]["validation"]["pipeline"]["steps"] if x["operation"]==name]
        if len(matches)!=1:raise ValueError("Missing required prior result")
        return Fraction(matches[0]["numerator"],matches[0]["denominator"])
    for kind,record in records.items():
        if set(record)!={"scope","acceptance","engineering_sha256","input","validation"}:raise ValueError("Wrong memory record")
        approved=scope(kind)
        if record["scope"]!=approved or {k:v for k,v in record["input"].items() if k!="operations"}!=approved["inputs"]:
            raise ValueError("Prior scope changed")
        if digest(sorted(record["input"]["operations"]))!=approved["operation_commitment"]:raise ValueError("Prior terminal set changed")
        if record["validation"]!=independent(record["input"]):raise ValueError("Prior pipeline disagrees")
        p=record["acceptance"]
        if p["scope_sha256"]!=scope_digest(approved) or p["verified_divisions"]!=5 or p["verified_profile_work_products"]!=11 or p["model_receipt_verified"] is not True or p["independent_actual_input_test"] is not True or p["provider_calls_replayed"]!=0 or p["model_calls_replayed"]!=0 or p["paid_inference"] is not False:
            raise ValueError("Unqualified prior mission")
        canonical(p["company"]);canonical(p["mission"]);proofs[kind]=p["qualification_sha256"]
        if not all(isinstance(x,str) and re.fullmatch(r"[0-9a-f]{64}",x) for x in (p["qualification_sha256"],record["engineering_sha256"])):
            raise ValueError("Invalid prior digest")
    if len(set(proofs.values()))!=3:raise ValueError("Duplicate mission evidence")
    original=step("engineering","total_load");extra=step("engineering","reserve_capacity")
    unit_reduction=step("scientific","absolute_reduction")
    margin=step("commercial","unit_contribution");profit=step("commercial","operating_profit")
    if original!=records["commercial"]["input"]["business"]["units"] or extra<0 or unit_reduction<0:
        raise ValueError("Incompatible prior scenario")
    expanded=original+extra
    result={"expanded_units":expanded,"additional_units":extra,"annual_avoided_methane_kg":expanded*unit_reduction*365/1000,
            "annual_operating_profit_usd":profit+extra*margin}
    s=records["scientific"]["input"]["experiment"];e=records["engineering"]["input"]["design"];b=records["commercial"]["input"]["business"]
    cap=e["capacity"];expected={"expanded_units":Fraction(cap),"additional_units":Fraction(cap-sum(e["loads"])),
        "annual_avoided_methane_kg":Fraction((sum(s["control"])-sum(s["treatment"]))*cap*365,1000*len(s["control"])),
        "annual_operating_profit_usd":Fraction(cap*(b["price"]-b["variable_cost"])-b["fixed_cost"])}
    if result!=expected:raise ValueError("Continuation independent check disagrees")
    exclusive(output,{"schema":"plenum-public-mission-continuation-v1","source_run_id":run,"source_commit":commit,
        "consumer_run_id":os.environ.get("GITHUB_RUN_ID"),"consumer_commit":os.environ.get("GITHUB_SHA"),
        "prior_memory_sha256":expected_sha,"prior_qualifications":proofs,
        "result":{k:{"numerator":v.numerator,"denominator":v.denominator} for k,v in result.items()},
        "new_offline_analysis_executed":True,"independent_check_passed":True,
        "provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False,
        "synthetic_only":True,"native_board_restored":False})

if __name__=="__main__":
    if sys.argv[1]=="make":make(Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]),os.environ["GITHUB_RUN_ID"],os.environ["GITHUB_SHA"])
    elif sys.argv[1]=="consume":consume(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6])
    else:raise ValueError("Unknown handoff command")
