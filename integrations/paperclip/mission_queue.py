"""Single-flight, immutable owner-approved queue of up to five typed objectives.

Local mode runs all entries consecutively. Remote mode stops after prepare,
requires a fresh exact owner grant, independently verifies remote completion,
then prepares the next. No credential rotation or ambiguous replay.
"""
import json,os
from pathlib import Path
from contextlib import contextmanager
from checkpoint_store import checked,exclusive,encoded
from lifecycle import canonical,mission_dir,owner_company,persistent
from mission_scope import validate_scope,digest as scope_digest
from model_plan import digest
from production_wiring import company_lock,load_prepared
from live_verify import local_receipt,remote_receipt

def validate_queue(value):
    if not isinstance(value,list) or not 2<=len(value)<=5 or len(encoded(value))>9000:raise ValueError("Queue requires two to five bounded typed objectives")
    scopes=[validate_scope(x) for x in value]
    if len(set(map(scope_digest,scopes)))!=len(scopes):raise ValueError("Duplicate queue scopes")
    return scopes

@contextmanager
def environment(**fields):
    old={k:os.environ.get(k) for k in fields}
    try:
        for k,v in fields.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
        yield
    finally:
        for k,v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v

def same(path,row):
    if path.exists() or path.is_symlink():
        if checked(path,row)!=row:raise ValueError("Queue evidence changed")
    else:exclusive(path,row)
    return row

def queue_run(api,root,qualify_locked,readback):
    if not persistent() or os.getenv("PLENUM_PAPERCLIP_MODEL")!="local":raise PermissionError("Queue requires explicit persistent local model mode")
    cid=owner_company(api);qid=canonical(os.environ["PLENUM_PAPERCLIP_QUEUE_UUID"])
    mode=os.getenv("PLENUM_PERSISTENT_CHECKPOINT_MODE","")
    if mode not in ("local","remote"):raise ValueError("Explicit queue checkpoint mode required")
    scopes=validate_queue(json.loads(os.environ["PLENUM_MISSION_QUEUE"]))
    inject=os.getenv("PLENUM_CI_QUEUE_REPLAN")=="confirmed"
    if inject and (os.getenv("GITHUB_ACTIONS")!="true" or mode!="local" or scopes[-1]["kind"]!="public_objective"):raise PermissionError("CI-only queue injection")
    if os.getenv("GITHUB_ACTIONS")=="true" and mode=="remote":raise PermissionError("No remote queue in public CI")
    with company_lock(root,cid):
        directory=Path(root)/cid/"queues"/qid
        if any(p.is_symlink() for p in (directory.parent,directory)):raise ValueError("Unsafe queue directory")
        directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        manifest=same(directory/"queue.json",{"schema":"plenum-queue-v1","company":cid,"queue":qid,"checkpoint_mode":mode,"model_mode":"local","scopes":scopes,"scope_sha256":list(map(scope_digest,scopes)),"ci_fault_injection":inject})
        accepted=[];roster=None
        for index,scope in enumerate(scopes,1):
            expected={"queue":qid,"index":index,"scope_sha256":scope_digest(scope),"manifest_sha256":digest(manifest)}
            start=directory/(str(index)+".prepare-start.json")
            target=directory/(str(index)+".prepared.json")
            done=directory/(str(index)+".accepted.json")
            if not target.exists():
                if start.exists() or start.is_symlink():raise RuntimeError("Ambiguous queue preparation; inspect native board, never replay")
                exclusive(start,expected)
                with environment(PLENUM_MISSION_SCOPE=encoded(scope).decode(),PLENUM_PAPERCLIP_MISSION_UUID=None,
                     PLENUM_CI_TRANSIENT_INTELLIGENCE="confirmed" if inject and index==len(scopes) else None,
                     PLENUM_CI_REPLAN_ENGINEERING="confirmed" if inject and index==len(scopes) else None):
                    prepared=qualify_locked("prepare")
                mid=canonical(prepared["mission"])
                if prepared["company"]!=cid or prepared["scope_sha256"]!=expected["scope_sha256"] or prepared["model_mode"]!="local" or prepared["checkpoint_mode"]!=mode:raise ValueError("Wrong prepared queue scope")
                exclusive(target,{**expected,"mission":mid})
                if mode=="remote":
                    result={"schema":"plenum-queue-progress-v1","queue":qid,"company":cid,"state":"awaiting_exact_grant","index":index,"mission":mid,"checkpoint_scope":cid+"/"+mid,"accepted":accepted,"paid_inference":False}
                    print(json.dumps(result),flush=True)
                    return result
            checked(start,expected)
            slot=checked(target,expected);mid=canonical(slot["mission"])
            mission=mission_dir(root,cid,mid)
            prepared=load_prepared(mission,cid,mid)
            if prepared["scope_sha256"]!=expected["scope_sha256"] or prepared["model_mode"]!="local" or prepared["checkpoint_mode"]!=mode:raise ValueError("Queue mission binding mismatch")
            if mid in [x["mission"] for x in accepted]:raise ValueError("Duplicate queue mission")
            if not (mission/"qualification.json").exists():
                if done.exists() or done.is_symlink():raise RuntimeError("Accepted queue evidence missing")
                activation=mission/"activation.json"
                with environment(PLENUM_PAPERCLIP_MISSION_UUID=mid,PLENUM_MISSION_SCOPE=None):
                    qualify_locked("resume" if activation.exists() or activation.is_symlink() else "activate")
            _,q,_,_,_=local_receipt(root,cid,mid,readback)
            if roster is None:roster=q["persistent_roster"]
            if roster!=q["persistent_roster"] or len(set(roster.values()))!=6:raise ValueError("Queue roster changed")
            row={**expected,"mission":mid,"qualification_sha256":digest(q),"persistent_roster_sha256":digest(roster),"paid_inference":False}
            if done.exists() or done.is_symlink():
                old=checked(done,row)
                if mode=="remote":
                    proof=checked(directory/(str(index)+".live.json"),{"company":cid,"mission":mid,"qualification_sha256":digest(q),"remote_checkpoint_count":5,"wrong_scope_http_status":403,"paid_inference":False})
                    row["live_verification_sha256"]=digest(proof)
                if old!=row:raise ValueError("Queue acceptance changed")
            else:
                if mode=="remote":
                    # Always verify the currently scoped grant before moving on.
                    # An interrupted verification can be repeated; never reactivate.
                    proof=remote_receipt(root,cid,mid,readback)
                    livepath=directory/(str(index)+".live.json")
                    if livepath.exists():
                        prior=checked(livepath,{"company":cid,"mission":mid,"qualification_sha256":digest(q),"remote_checkpoint_count":5,"wrong_scope_http_status":403,"paid_inference":False})
                        if {k:v for k,v in prior.items() if k!="verified_at"}!={k:v for k,v in proof.items() if k!="verified_at"}:raise ValueError("Remote queue proof changed")
                        proof=prior
                    else:exclusive(livepath,proof)
                    row["live_verification_sha256"]=digest(proof)
                exclusive(done,row)
            accepted.append(row)
        result={"schema":"plenum-queue-completion-v1","queue":qid,"company":cid,"manifest_sha256":digest(manifest),"checkpoint_mode":mode,
                "state":"completed","accepted":accepted,"persistent_roster_sha256":digest(roster),"paid_inference":False}
        same(directory/"completed.json",result)
        print(json.dumps(result),flush=True)
        return result
