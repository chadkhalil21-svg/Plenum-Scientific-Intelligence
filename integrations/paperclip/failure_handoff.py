"""Read-only session handoff for a timed-out native mission.

Adapted from Anthropic's long-running agent guidance: leave structured progress
for the next session. Original immutable receipts remain authoritative; this
summary does not grant permission, authorize replay or certify mission success.
"""
import hashlib
from pathlib import Path
from checkpoint_store import checked,encoded,exclusive
from lifecycle import canonical

ROLES=("intelligence","research","engineering","commercial","verification")
def publish(directory,company,mission,scope_sha256,diagnostics):
    root=Path(directory)
    if root.is_symlink() or not root.is_dir():raise ValueError("Unsafe handoff directory")
    company,mission=canonical(company),canonical(mission)
    plan_path=root/"minister-plan.json"
    completed={};reserved=[];unstarted=[];plan_sha=None
    if plan_path.exists() or plan_path.is_symlink():
        plan=checked(plan_path,{"company":company,"parent":mission,"order":list(ROLES)})
        if set(plan["tasks"])!=set(ROLES) or len({canonical(v) for v in plan["tasks"].values()})!=5:
            raise ValueError("Unexpected original native tasks")
        plan_sha=hashlib.sha256(encoded(plan)).hexdigest()
        for role in ROLES:
            issue=canonical(plan["tasks"][role])
            identity={"company":company,"role":role,"issue":issue}
            receipt=root/(role+".json")
            attempts=[]
            for i in (1,2):
                marker=root/(role+".attempt-"+str(i))
                if marker.exists() or marker.is_symlink():
                    checked(marker,{**identity,"attempt":i})
                    attempts.append(i)
            if receipt.exists() or receipt.is_symlink():
                row=checked(receipt,identity)
                if row["sha256"]!=hashlib.sha256(encoded(row["result"])).hexdigest():
                    raise ValueError("Handoff receipt digest mismatch")
                completed[role]={"issue":issue,"receipt_sha256":hashlib.sha256(encoded(row)).hexdigest()}
            elif attempts:reserved.append(role)
            else:unstarted.append(role)
    # Only small, fixed-category diagnostics already emitted by supervisor.
    safe=[]
    for row in diagnostics:
        role=row["division"];d=row["diagnostic"]
        if role not in ("minister",*ROLES):raise ValueError("Unknown diagnostic division")
        item={"division":role,"run":canonical(d["id"]),"status":str(d.get("status"))[:32],
              "error_code":str(d.get("errorCode"))[:64],"exit_code":d.get("exitCode")}
        recovery=d.get("native_recovery")
        if isinstance(recovery,dict):
            kind=recovery.get("kind")
            item["native_recovery"]={"kind":kind if kind in ("bootstrap","other") else None}
            for field in ("provider_work_started","identity_matches","observed_run_matches","finished","detail_error"):
                value=recovery.get(field)
                item["native_recovery"][field]=value if type(value) is bool else None
        safe.append(item)
    if len(safe)>18:raise ValueError("Diagnostic bound")
    result={"schema":"plenum-native-failure-handoff-v1","company":company,"mission":mission,
            "scope_sha256":scope_sha256,"plan_sha256":plan_sha,"completed_receipts":completed,
            "reserved_unfinished":reserved,"no_local_reservation_observed":unstarted,
            "diagnostics":safe,"mission_accepted":False,"automatic_replay_authorized":False,
            "paid_inference":False}
    # Publish once, preserve previous handoff on any subsequent session.
    exclusive(root/"failure-handoff.json",result)
    return result
