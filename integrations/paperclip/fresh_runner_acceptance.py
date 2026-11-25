"""Final acceptance on a separate GitHub runner using only original public evidence.

No Paperclip database, tokens, agent identities re-created, model or provider
request. Reviewed local functional verification is repeated deliberately.
This is a durable acceptance boundary, not native in-flight board recovery.
"""
import hashlib,json,os,sys
from pathlib import Path
from checkpoint_store import checked,encoded,exclusive
from lifecycle import canonical
from mission_scope import validate_scope,digest as scope_digest,profile_routes
from model_plan import validate_receipt
from objective_mission import planning_kwargs
from sequential_mission import MISSION_ORDER,scope_binding,scope_inputs,goal_texts,verify
from profile_execution import chief_receipt,division_receipts

def digest(row):return hashlib.sha256(encoded(row)).hexdigest()

def read(path,expected=None):
    return checked(path,expected or {})

def safe_tree(root):
    if root.is_symlink() or not root.is_dir():raise ValueError("Unsafe evidence root")
    count=0;size=0
    for p in root.rglob("*"):
        count+=1
        if count>500 or p.is_symlink() or not (p.is_file() or p.is_dir()):raise ValueError("Unsafe evidence tree")
        if p.is_file():
            size+=p.stat().st_size
            if size>20_000_000:raise ValueError("Evidence tree too large")

def accept(root,run,commit,expected_scope=None):
    safe_tree(root)
    read(root/"ci-diagnostic.json",{"run_id":run,"commit":commit,"startup":"success","checkpoint":"success","mission":"success","restart":"success","evidence_copy":"success","failure_receipts":0})
    marker=root/"event-native-mission.json"
    if marker.exists():
        m=read(marker,{"paid_inference":False})
        cid,mid=canonical(m["company"]),canonical(m["mission"])
        directory=root/cid/mid;summary=read(directory/"qualification.json",{"company":cid,"parent":mid,"scope_sha256":m["scope_sha256"]})
        timing_root=directory
    else:
        summary=read(root/"qualification.json");cid,mid=canonical(summary["company"]),canonical(summary["parent"])
        directory=root/cid;timing_root=root
    if summary.get("paid_inference") is not False or summary.get("verified_divisions")!=5 or summary.get("verified_profile_work_products")!=11:raise ValueError("Incomplete original qualification")
    h=digest(summary)
    read(timing_root/"event-timing.json",{"parent":mid,"qualification_sha256":h,"paid_inference":False})
    read(timing_root/"restart-timing.json",{"qualification_sha256":h,"container_restart_readback":True,"provider_calls_replayed":0})
    binding=read(directory/"mission-scope.json")
    scope=validate_scope(binding["scope"])
    if binding!=scope_binding(scope) or summary["scope_sha256"]!=scope_digest(scope) or (expected_scope is not None and scope!=validate_scope(expected_scope)):raise ValueError("Wrong original public scope")
    if read(directory/"profile-routing.json")!=profile_routes(scope):raise ValueError("Wrong original profiles")
    plan=read(directory/"minister-plan.json",{"company":cid,"parent":mid,"minister":summary["minister"],"order":list(MISSION_ORDER)})
    if set(plan["tasks"])!=set(MISSION_ORDER) or len(set(plan["tasks"].values()))!=5:raise ValueError("Wrong task identities")
    chief=read(directory/"chief-profile.json")
    if chief!=chief_receipt(scope,plan):raise ValueError("Chief receipt mismatch")
    profiles={"chief":digest(chief)};prior={};evidence={}
    for role in MISSION_ORDER:
        issue=canonical(plan["tasks"][role])
        row=read(directory/(role+".json"),{"company":cid,"role":role,"issue":issue})
        value=row["result"];sha=digest(value)
        if row["sha256"]!=sha or value["input_sha256"]!=scope_inputs(prior):raise ValueError("Producer or dependency digest mismatch")
        expected=division_receipts(role,scope,prior,value["result"],directory)
        if value["profile_receipts"]!=expected or set(expected)&set(profiles):raise ValueError("Profile receipt mismatch")
        profiles.update({k:digest(v) for k,v in expected.items()})
        prior[role]=value;evidence[role]={"issue":issue,"sha256":sha}
    if len(profiles)!=11 or profiles!=summary["profile_receipt_sha256"] or evidence!=summary["evidence"]:raise ValueError("Qualification evidence mismatch")
    actual=verify({k:v for k,v in prior.items() if k!="verification"},directory,functional_test=True,scope=scope)
    if actual!=prior["verification"]["result"] or actual!=summary["independent_verification"]:raise ValueError("Fresh functional verification mismatch")
    if summary.get("minister_model_executed") is True:
        receipt=read(directory/"minister-model-plan.json")
        if digest(receipt)!=summary["model_receipt_sha256"] or digest(receipt)!=plan["model_receipt_sha256"] or validate_receipt(receipt,cid,mid,goals=goal_texts(scope),**planning_kwargs(scope))!=list(MISSION_ORDER):raise ValueError("Original model proof mismatch")
    elif summary.get("minister_model_executed") is not False or "model_receipt_sha256" in plan:raise ValueError("Model state mismatch")
    extra={}
    recovery=directory/"supervisor-recovery.json"
    if recovery.exists():
        proof=read(recovery,{"schema":"plenum-native-supervisor-recovery-v1","company":cid,"mission":mid,
            "child_return_codes":[-9,-9,0],"qualification_sha256":h,"native_issue_count":6,
            "native_task_ids":sorted({mid,*plan["tasks"].values()}),"specialist_reservations":5,"model_reservations":1,
            "provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False})
        first=read(directory/"ci-supervisor-interrupt-73.json",{"company":cid,"mission":mid,"stage":"after_assignment","signal":9,"paid_inference":False})
        second=read(directory/"ci-supervisor-interrupt-74.json",{"company":cid,"mission":mid,"stage":"after_timing","signal":9,"paid_inference":False})
        timing=read(timing_root/"event-timing.json")
        if first["native_parent_status"] not in ("todo","in_progress") or first["native_parent_status"]!=proof["unfinished_parent_status"] or proof["interrupt_receipt_sha256"]!=[digest(first),digest(second)] or second["timing_sha256"]!=proof["timing_sha256"] or digest(timing)!=proof["timing_sha256"]:raise ValueError("Supervisor recovery proof mismatch")
        for role,issue in plan["tasks"].items():
            read(directory/(role+".attempt-1"),{"company":cid,"role":role,"issue":issue,"attempt":1})
            if (directory/(role+".attempt-2")).exists():raise ValueError("Unexpected specialist replay")
        read(directory/"minister-model-attempt.json",{"company":cid,"parent":mid,"maximum":1})
        extra={"supervisor_recovery_sha256":digest(proof)}
    return {**extra,"company":cid,"mission":mid,"scope_sha256":scope_digest(scope),"qualification_sha256":h,
            "verified_divisions":5,"verified_profile_work_products":11,"model_receipt_verified":summary["minister_model_executed"],
            "independent_actual_input_test":True,"provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False}

def main():
    base=Path(sys.argv[1]);out=Path(sys.argv[2])
    event=os.environ["EVENT"];run=os.environ["GITHUB_RUN_ID"];commit=os.environ["GITHUB_SHA"]
    expected_names={"off-legacy","local-legacy","local-budget","local-objective"} if event=="pull_request" else {"local-event"}
    paths={p.name.removeprefix("paperclip-native-public-evidence-"):p for p in base.iterdir()}
    if set(paths)!=expected_names:raise ValueError("Missing or unexpected native evidence archives")
    scope=None if event=="pull_request" else validate_scope(json.loads(os.environ["EXPECTED_SCOPE"]))
    results={k:accept(paths[k],run,commit,scope) for k in sorted(paths)}
    if any(v["model_receipt_verified"]!=(k!="off-legacy") for k,v in results.items()):raise ValueError("Unexpected model receipt")
    if event=="pull_request" and not results["local-objective"].get("supervisor_recovery_sha256"):raise ValueError("Missing native interrupted-supervisor proof")
    row={"schema":"plenum-fresh-runner-acceptance-v1","run_id":run,"commit":commit,"accepted":results,
         "fresh_runner_independent_acceptance":True,"native_board_restored":False,"provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False}
    exclusive(out,row)
    print(json.dumps(row,sort_keys=True))
if __name__=="__main__":main()
