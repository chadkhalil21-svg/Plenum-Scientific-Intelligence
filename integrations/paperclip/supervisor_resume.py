"""Resume only an acknowledged native assignment. Never reassign or replay providers."""
import os,time,signal
from datetime import datetime,timezone
from checkpoint_store import checked,exclusive
from lifecycle import canonical
from production_wiring import load_prepared
from model_plan import digest

def validate_resume(api,directory,cid,mid,leader,binding):
    prepared=load_prepared(directory,cid,mid)
    checked(directory/"activation.json",{"company":cid,"mission":mid,"minister":leader,
        "scope_sha256":binding["scope_sha256"],"model_mode":prepared["model_mode"],
        "remote_checkpoint_preflight":prepared["checkpoint_mode"]=="remote"})
    task=api("/api/issues/"+canonical(mid))
    if (task.get("id")!=mid or task.get("companyId")!=cid or task.get("parentId") is not None
        or task.get("assigneeAgentId")!=leader or task.get("status") not in ("todo","in_progress","done")
        or task.get("title")!=binding["parent_title"] or task.get("description")!=binding["parent_description"]):
        raise ValueError("Unacknowledged or changed native assignment; no replay")
    return task

def interrupt_ci(flag,durable,action,directory,code,*,api=None):
    if os.getenv(flag)!="confirmed":return
    if os.getenv("GITHUB_ACTIONS")!="true" or not durable or action!=("activate" if code==73 else "resume"):
        raise PermissionError("Supervisor interruption restricted to isolated CI")
    cid=canonical(os.environ["PLENUM_PAPERCLIP_COMPANY_UUID"])
    mid=canonical(os.environ["PLENUM_PAPERCLIP_MISSION_UUID"])
    prepared=load_prepared(directory,cid,mid)
    if prepared["checkpoint_mode"]!="local" or prepared["model_mode"]!="local":
        raise PermissionError("Supervisor interruption requires isolated local objective")
    row={"company":cid,"mission":mid,"stage":"after_assignment" if code==73 else "after_timing",
         "signal":signal.SIGKILL.value,"paid_inference":False}
    if api is not None:
        task=api("/api/issues/"+mid)
        row["native_parent_status"]=task["status"]
        if task["status"] not in ("todo","in_progress"):raise ValueError("Expected unfinished native assignment")
    else:
        row["timing_sha256"]=digest(checked(directory/"event-timing.json",{"parent":mid}))
        if (directory/"qualification.json").exists():raise ValueError("Expected unfinished finalization")
    exclusive(directory/("ci-supervisor-interrupt-"+str(code)+".json"),row)
    os.kill(os.getpid(),signal.SIGKILL)

def finalize(root,summary,started,queued,*,resuming=False,directory=None):
    """Timing first, qualification last: either can be reconciled by readback.
    When the original monotonic interval was lost, don't invent it."""
    target=root/"qualification.json";tp=root/"event-timing.json"
    expected={"parent":summary["parent"],"qualification_sha256":digest(summary),"paid_inference":False,
              "model_executed":summary["minister_model_executed"],"verified_divisions":summary["verified_divisions"]}
    if target.exists() or target.is_symlink():
        if checked(target,summary)!=summary:raise ValueError("Qualification changed")
    if tp.exists() or tp.is_symlink():
        timing=checked(tp,expected)
        if timing.get("schema")!="plenum-paperclip-event-timing-v1":raise ValueError("Unknown timing receipt")
        stamp=datetime.fromisoformat(timing["verified_at"])
        if stamp.tzinfo is None:raise ValueError("Invalid timing timestamp")
    else:
        terminal=datetime.now(timezone.utc)
        issue_created=os.getenv("PLENUM_ISSUE_CREATED_AT","")
        timing={"schema":"plenum-paperclip-event-timing-v1",**expected,
                "native_assignment_to_verified_seconds":None if resuming else round(time.monotonic()-queued,3),
                "native_qualification_seconds":None if resuming else round(time.monotonic()-started,3),
                "verified_at":terminal.isoformat(),"issue_created_at":issue_created or None,"issue_to_verified_seconds":None}
        if resuming:timing["supervisor_resume_wait_seconds"]=round(time.monotonic()-started,3)
        if issue_created:
            created=datetime.fromisoformat(issue_created)
            if created.tzinfo is None or created>terminal:raise ValueError("Invalid event timestamp")
            timing["issue_to_verified_seconds"]=round((terminal-created).total_seconds(),3)
        exclusive(tp,timing)
    if directory is not None:
        interrupt_ci("PLENUM_CI_INTERRUPT_FINALIZATION",True,"resume" if resuming else "activate",directory,74)
    if not target.exists():exclusive(target,summary)
    return timing
