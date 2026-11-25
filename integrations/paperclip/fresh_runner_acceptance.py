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
from model_plan import validate_receipt,verify_classification_attempts
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
    return accept_mission(directory,timing_root,summary,cid,mid,expected_scope)

def accept_mission(directory,timing_root,summary,cid,mid,expected_scope=None):
    if summary.get("company")!=cid or summary.get("parent")!=mid:raise ValueError("Wrong mission identity")
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
        verify_classification_attempts(directory,receipt,planning_kwargs(scope)["operation_policy"])
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

def accept_queue(root):
    from mission_queue import validate_queue
    from recovery_audit import verify as verify_recovery
    from objective_replan import validate_saved
    lifecycle=read(root/"persistent-lifecycle.json",{"model_mode":"local","queue_no_replay":True,
        "first_mission_preserved":True,"staged_prepare_activate":True,"paid_inference":False})
    cid,qid=canonical(lifecycle["same_company"]),canonical(lifecycle["queue_uuid"])
    queue=root/cid/"queues"/qid
    manifest=read(queue/"queue.json",{"schema":"plenum-queue-v1","company":cid,"queue":qid,
        "checkpoint_mode":"local","model_mode":"local","ci_fault_injection":True})
    scopes=validate_queue(manifest["scopes"])
    if len(scopes)!=2 or manifest["scope_sha256"]!=list(map(scope_digest,scopes)):raise ValueError("Wrong queue scopes")
    if scopes[1]["kind"]!="public_objective" or "operation_commitment" not in scopes[1]:raise ValueError("Missing natural objective")
    roster=lifecycle["same_six_agent_ids"]
    if len(roster)!=6 or len(set(map(canonical,roster.values())))!=6 or roster["minister"]!=lifecycle["same_minister"]:raise ValueError("Wrong queue roster")
    accepted=[];proofs=[];mids=[]
    for index,scope in enumerate(scopes,1):
        expected={"queue":qid,"index":index,"scope_sha256":scope_digest(scope),"manifest_sha256":digest(manifest)}
        if read(queue/(str(index)+".prepare-start.json"),expected)!=expected:raise ValueError("Wrong queue start")
        slot=read(queue/(str(index)+".prepared.json"),expected)
        mid=canonical(slot["mission"]);mids.append(mid)
        if slot!={**expected,"mission":mid}:raise ValueError("Wrong queue slot")
        directory=root/cid/mid
        summary=read(directory/"qualification.json",{"persistent_roster":roster,"minister":roster["minister"]})
        proof=accept_mission(directory,directory,summary,cid,mid,scope)
        if proof["model_receipt_verified"] is not True:raise ValueError("Missing queue model proof")
        row={**expected,"mission":mid,"qualification_sha256":proof["qualification_sha256"],
             "persistent_roster_sha256":digest(roster),"paid_inference":False}
        if read(queue/(str(index)+".accepted.json"),row)!=row:raise ValueError("Wrong accepted queue slot")
        if index==2:
            intelligence=read(directory/"intelligence.json")
            recovery=verify_recovery(directory,cid,"intelligence",intelligence["issue"],intelligence["sha256"])
            engineering=read(directory/"engineering.json")
            replan=validate_saved(directory,cid,mid,engineering["issue"],scope)
            complete=read(directory/"engineering.replan-completed.json",{"replan_sha256":digest(replan),
                "result_sha256":engineering["sha256"],"issue":engineering["issue"],
                "alternative_tool":replan["choice"]["tool"],"paid_inference":False})
            read(directory/"engineering.alternative-attempt.json",{"replan_sha256":digest(replan),"issue":engineering["issue"],"maximum":1})
            expected_recovery={"intelligence":digest(recovery)}
            expected_replan={"engineering":digest({"replan":replan,"completed":complete})}
            if recovery is None or summary["recovery_receipt_sha256"]!=expected_recovery or summary["replan_receipt_sha256"]!=expected_replan or lifecycle["recovery_receipt_sha256"]!=expected_recovery or lifecycle["replan_receipt_sha256"]!=expected_replan:raise ValueError("Queue recovery proof mismatch")
        accepted.append(row);proofs.append(proof)
    if len(set(mids))!=2 or lifecycle["missions"]!=mids or lifecycle["restart_digests"]!=[x["qualification_sha256"] for x in proofs]:raise ValueError("Queue continuity mismatch")
    completion={"schema":"plenum-queue-completion-v1","queue":qid,"company":cid,
        "manifest_sha256":digest(manifest),"checkpoint_mode":"local","state":"completed",
        "accepted":accepted,"persistent_roster_sha256":digest(roster),"paid_inference":False}
    if read(queue/"completed.json",completion)!=completion:raise ValueError("Queue completion changed")
    return {"queue":qid,"company":cid,"completion_sha256":digest(completion),"missions":proofs,
            "same_roster":True,"queue_no_replay":True,"paid_inference":False}

def main():
    base=Path(sys.argv[1]);out=Path(sys.argv[2])
    event=os.environ["EVENT"];run=os.environ["GITHUB_RUN_ID"];commit=os.environ["GITHUB_SHA"]
    novel=event=="pull_request" and os.environ.get("QUALIFICATION_SUITE")=="multidisciplinary"
    if novel:
        from pipeline_fixtures import KINDS,scope as fixture_scope
        expected_names={"local-"+k for k in KINDS}
    else:
        expected_names={"off-legacy","local-legacy","local-budget","local-objective"} if event=="pull_request" else {"local-event"}
    paths={p.name.removeprefix("paperclip-native-public-evidence-"):p for p in base.iterdir()}
    if set(paths)!=expected_names:raise ValueError("Missing or unexpected native evidence archives")
    scope=None if event=="pull_request" else validate_scope(json.loads(os.environ["EXPECTED_SCOPE"]))
    results={k:accept(paths[k],run,commit,fixture_scope(k.removeprefix("local-")) if novel else scope) for k in sorted(paths)}
    if any(v["model_receipt_verified"]!=(k!="off-legacy") for k,v in results.items()):raise ValueError("Unexpected model receipt")
    if event=="pull_request" and not novel and not results["local-objective"].get("supervisor_recovery_sha256"):raise ValueError("Missing native interrupted-supervisor proof")
    row={"schema":"plenum-fresh-runner-acceptance-v1","run_id":run,"commit":commit,"accepted":results,
         "fresh_runner_independent_acceptance":True,"native_board_restored":False,"provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False}
    if event=="pull_request" and not novel:row["consecutive_queue"]=accept_queue(paths["local-budget"])
    exclusive(out,row)
    print(json.dumps(row,sort_keys=True))
if __name__=="__main__":main()
