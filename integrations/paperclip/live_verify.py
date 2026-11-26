"""Owner-only live proof, using the real native readback and signed remote GETs.

No activation, remote mutation, model call, host restart, credential printing or
public CI access. A restart marker is reported separately; it is not proof of
a Docker restart by itself.
"""
import json,os
from datetime import datetime,timezone
from uuid import uuid4
from checkpoint_store import checked
from lifecycle import canonical,mission_dir,owner_company,persistent
from model_plan import digest
from production_wiring import load_prepared,grant,company_lock
from runtime_checkpoint import RuntimeCheckpoint,CheckpointRejected

ROLES=("intelligence","research","engineering","commercial","verification")
REQUIRED={"minister_model_executed":True,"verified_divisions":5,"verified_profile_work_products":11,"paid_inference":False}

def local_receipt(root,company,mission,readback):
    directory=mission_dir(root,company,mission)
    q=checked(directory/"qualification.json",{"company":company,"parent":mission,**REQUIRED})
    if q["minister_model_executed"] is not True or q["paid_inference"] is not False or type(q["verified_divisions"]) is not int or type(q["verified_profile_work_products"]) is not int:
        raise ValueError("Invalid model qualification types")
    prepared=load_prepared(directory,company,mission)
    if prepared["model_mode"]!="local" or prepared["scope_sha256"]!=q["scope_sha256"]:raise ValueError("Prepared local model scope mismatch")
    activation=checked(directory/"activation.json",{"company":company,"mission":mission,"minister":q["minister"],"scope_sha256":q["scope_sha256"],"model_mode":"local","remote_checkpoint_preflight":prepared["checkpoint_mode"]=="remote"})
    plan=checked(directory/"minister-plan.json",{"company":company,"parent":mission,"minister":q["minister"]})
    if set(plan["tasks"])!=set(ROLES) or len(set(plan["tasks"].values()))!=5:raise ValueError("Invalid native task identities")
    if readback(company,plan)!=q:raise ValueError("Independent native readback mismatch")
    timing=checked(directory/"event-timing.json",{"parent":mission,"qualification_sha256":digest(q),"paid_inference":False,"model_executed":True,"verified_divisions":5})
    evidence={}
    if set(q["evidence"])!=set(ROLES) or len(q["profile_receipt_sha256"])!=11:raise ValueError("Missing qualification evidence")
    for role in ROLES:
        issue=canonical(plan["tasks"][role])
        record=checked(directory/(role+".json"),{"company":company,"role":role,"issue":issue})
        h=digest(record["result"])
        if record["sha256"]!=h or q["evidence"][role]!={"issue":issue,"sha256":h}:raise ValueError("Local evidence digest mismatch")
        evidence[role]={"issue":issue,"sha256":h}
    restart=directory/"restart-timing.json"
    restart_digest=None
    if restart.exists() or restart.is_symlink():
        row=checked(restart,{"qualification_sha256":digest(q),"container_restart_readback":True,"provider_calls_replayed":0})
        restart_digest=digest(row)
    return directory,q,prepared,evidence,restart_digest

def remote_receipt(root,company,mission,readback):
    if not persistent() or os.getenv("GITHUB_ACTIONS")=="true":raise PermissionError("Live verifier is owner-only")
    directory,q,prepared,evidence,restart_digest=local_receipt(root,company,mission,readback)
    if prepared["checkpoint_mode"]!="remote":raise PermissionError("Explicit remote activation required")
    secret=grant(company,mission)
    remote={}
    for role,expected in evidence.items():
        record=RuntimeCheckpoint(company,mission,role,expected["issue"],secret=secret,scope=company+"/"+mission).request("GET")
        if record is None or record.get("state")!="completed" or record.get("issue")!=expected["issue"] or record.get("sha256")!=expected["sha256"] or record.get("revision")!=record.get("attempt")+1:
            raise ValueError("Remote checkpoint does not match accepted local task: "+role)
        remote[role]={**expected,"attempt":record["attempt"],"revision":record["revision"]}
    wrong=str(uuid4())
    if wrong==mission:raise ValueError("Wrong-scope test collision")
    try:
        RuntimeCheckpoint(company,wrong,"intelligence",evidence["intelligence"]["issue"],secret=secret,scope=company+"/"+wrong).request("GET")
    except CheckpointRejected as exc:
        if exc.status!=403 or exc.code!="checkpoint_scope_unavailable":raise ValueError("Wrong-scope response not verified") from None
    else:raise ValueError("Wrong scope was not rejected")
    receipt={"schema":"plenum-live-verification-v1","company":company,"mission":mission,
             "scope_sha256":q["scope_sha256"],"qualification_sha256":digest(q),"model_receipt_sha256":q["model_receipt_sha256"],
             **REQUIRED,"remote_checkpoint_count":len(remote),"remote_checkpoints":remote,
             "wrong_scope_http_status":403,"wrong_scope_error":"checkpoint_scope_unavailable",
             "independent_native_readback":True,"restart_readback_receipt_sha256":restart_digest,
             "container_restart_performed_by_verifier":False,"provider_calls_replayed":0,
             "recovery_receipt_sha256":q.get("recovery_receipt_sha256",{}),"replan_receipt_sha256":q.get("replan_receipt_sha256",{}),
             "verified_at":datetime.now(timezone.utc).isoformat(),"wake_verified":False}
    return receipt

def verify_live(api,root,readback):
    if not persistent() or os.getenv("GITHUB_ACTIONS")=="true":raise PermissionError("Live verifier is owner-only")
    cid=owner_company(api);mid=canonical(os.environ["PLENUM_PAPERCLIP_MISSION_UUID"])
    with company_lock(root,cid):
        receipt=remote_receipt(root,cid,mid,readback)
    print(json.dumps(receipt,sort_keys=True),flush=True)
    return receipt
