"""Bounded process supervisor: reattach after child SIGKILL, never replay activation."""
import os,signal,subprocess,sys
from pathlib import Path
from checkpoint_store import checked,exclusive
from lifecycle import canonical,persistent
from model_plan import digest
import sequential_mission as native
from event_native import MARKER

HERE=Path(__file__).parent

def supervise(mode,*,runner=subprocess.run):
    if mode not in ("event","activate","resume","queue"):raise ValueError("Unknown supervised native mode")
    ci=os.getenv("GITHUB_ACTIONS")=="true"
    injection=os.getenv("PLENUM_CI_SUPERVISOR_PROOF")=="confirmed"
    if injection and (not ci or mode!="event"):raise PermissionError("Fault injection requires isolated event qualification")
    if mode=="event":
        if not ci:raise PermissionError("Event supervisor is public CI only")
        file="event_native.py";action="execute";resume="resume"
    else:
        if not persistent():raise PermissionError("Explicit persistent board required")
        file="sequential_mission.py";action="queue-run" if mode=="queue" else mode
        resume="queue-run" if mode=="queue" else "resume"
    codes=[]
    for i in range(3):
        env=dict(os.environ)
        for flag in ("PLENUM_CI_INTERRUPT_SUPERVISOR","PLENUM_CI_INTERRUPT_FINALIZATION"):
            env.pop(flag,None)
        if injection and i<2:
            env[("PLENUM_CI_INTERRUPT_SUPERVISOR","PLENUM_CI_INTERRUPT_FINALIZATION")[i]]="confirmed"
        child=runner([sys.executable,str(HERE/file),action],env=env)
        codes.append(child.returncode)
        if child.returncode==0:
            if injection:verify_injection(codes)
            return
        # Ordinary exceptions, operator termination, security refusals and
        # non-SIGKILL exits must not be interpreted as transient failures.
        if child.returncode!=-signal.SIGKILL or i==2:
            raise RuntimeError("Native supervisor child did not qualify")
        if mode=="event":
            checked(native.ROOT/MARKER,{"paid_inference":False})
        elif mode!="queue":
            cid=canonical(os.environ["PLENUM_PAPERCLIP_COMPANY_UUID"])
            mid=canonical(os.environ["PLENUM_PAPERCLIP_MISSION_UUID"])
            checked(native.ROOT/cid/mid/"activation.json",{"company":cid,"mission":mid})
        # resume/queue-run independently validate exact original activation;
        # never start a new parent or reassign an interrupted activation.
        action=resume
    raise RuntimeError("Supervisor retry budget exhausted")

def verify_injection(codes):
    if codes!=[-9,-9,0]:raise ValueError("Expected two actual child SIGKILLs and one completion")
    m=checked(native.ROOT/MARKER,{"paid_inference":False})
    cid,mid=canonical(m["company"]),canonical(m["mission"]);d=native.ROOT/cid/mid
    q=checked(d/"qualification.json",{"company":cid,"parent":mid,"verified_divisions":5,"verified_profile_work_products":11,"minister_model_executed":True,"paid_inference":False})
    first=checked(d/"ci-supervisor-interrupt-73.json",{"company":cid,"mission":mid,"signal":9,"stage":"after_assignment","paid_inference":False})
    second=checked(d/"ci-supervisor-interrupt-74.json",{"company":cid,"mission":mid,"signal":9,"stage":"after_timing","paid_inference":False})
    if first["native_parent_status"] not in ("todo","in_progress"):raise ValueError("No unfinished mission at interruption")
    timing=checked(d/"event-timing.json",{"qualification_sha256":digest(q),"parent":mid})
    if second["timing_sha256"]!=digest(timing):raise ValueError("Recovered timing changed")
    plan=checked(d/"minister-plan.json",{"company":cid,"parent":mid,"minister":q["minister"]})
    tasks={mid,*plan["tasks"].values()}
    rows=native.api("/api/companies/"+cid+"/issues")
    if len(rows)!=6 or {r["id"] for r in rows}!=tasks or any(r["status"]!="done" for r in rows):raise ValueError("Duplicate or unfinished native issue")
    for role,issue in plan["tasks"].items():
        checked(d/(role+".attempt-1"),{"company":cid,"role":role,"issue":issue,"attempt":1})
        if (d/(role+".attempt-2")).exists():raise ValueError("Unexpected specialist replay")
    checked(d/"minister-model-attempt.json",{"company":cid,"parent":mid,"maximum":1})
    proof={"schema":"plenum-native-supervisor-recovery-v1","company":cid,"mission":mid,
           "child_return_codes":codes,"unfinished_parent_status":first["native_parent_status"],
           "interrupt_receipt_sha256":[digest(first),digest(second)],"timing_sha256":digest(timing),
           "qualification_sha256":digest(q),"native_issue_count":len(rows),"native_task_ids":sorted(tasks),
           "specialist_reservations":5,"model_reservations":1,"provider_calls_replayed":0,
           "model_calls_replayed":0,"paid_inference":False}
    exclusive(d/"supervisor-recovery.json",proof)
    print(proof,flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Specify exact supervisor mode")
    supervise(sys.argv[1])
