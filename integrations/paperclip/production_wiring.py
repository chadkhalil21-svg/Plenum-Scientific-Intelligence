"""Owner-private two-phase activation and exact native checkpoint grant.
No secrets in mission evidence or agent adapter configuration.
"""
import json
import os
import stat
from pathlib import Path
from contextlib import contextmanager
from urllib.error import HTTPError
from lifecycle import canonical
from checkpoint_store import checked, exclusive

GRANT_DIR=Path("/run/plenum-checkpoint")
MODES=("local","remote")

@contextmanager
def company_lock(root,company):
    import fcntl
    directory=Path(root)/canonical(company)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    if directory.is_symlink():raise ValueError("Unsafe company directory")
    fd=os.open(directory/".submission.lock",os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:os.close(fd)

def prepared(directory,company,mission,scope_sha,mode,model_mode="off"):
    if mode not in MODES or model_mode not in ("off","local"):raise ValueError("Unknown execution mode")
    row={"schema":"plenum-prepared-mission-v1","company":canonical(company),
         "mission":canonical(mission),"scope_sha256":scope_sha,"checkpoint_mode":mode,"model_mode":model_mode}
    exclusive(Path(directory)/"prepared.json",row)
    return row

def load_prepared(directory,company,mission):
    row=checked(Path(directory)/"prepared.json",{"schema":"plenum-prepared-mission-v1",
        "company":canonical(company),"mission":canonical(mission)})
    row={**row,"model_mode":row.get("model_mode","off")}
    if set(row)!={"schema","company","mission","scope_sha256","checkpoint_mode","model_mode"} or row["checkpoint_mode"] not in MODES or row["model_mode"] not in ("off","local"):
        raise ValueError("Invalid prepared mission")
    return row

def grant(company,mission,*,root=None):
    if os.getenv("GITHUB_ACTIONS")=="true":raise PermissionError("Public CI cannot use owner checkpoint grant")
    runtime_mount=root is None
    root=GRANT_DIR if runtime_mount else Path(root)
    scope=canonical(company)+"/"+canonical(mission)
    directory_fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        info=os.fstat(directory_fd)
        if info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o700:
            raise PermissionError("Private grant directory must be runtime-owned mode 0700")
        if runtime_mount and not os.fstatvfs(directory_fd).f_flag & os.ST_RDONLY:
            raise PermissionError("Private grant directory must be mounted read-only")
        fd=os.open(mission+".json",os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory_fd)
    finally:os.close(directory_fd)
    with os.fdopen(fd,"rb") as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o600 or info.st_size>4096:
            raise PermissionError("Private checkpoint grant must be owned by runtime user, mode 0600")
        data=json.loads(stream.read(4097))
    if (not isinstance(data,dict) or set(data)!={"scope","secret"} or data["scope"]!=scope
        or not isinstance(data["secret"],str) or not 32<=len(data["secret"])<=512):
        raise PermissionError("Incorrect private checkpoint grant")
    return data["secret"]

def checkpoint_for(directory,company,mission,role,issue):
    from runtime_checkpoint import RuntimeCheckpoint
    row=load_prepared(directory,company,mission)
    if row["checkpoint_mode"]=="local":return None
    return RuntimeCheckpoint(company,mission,role,issue,secret=grant(company,mission),scope=company+"/"+mission)

def preflight(directory,company,mission):
    from runtime_checkpoint import RuntimeCheckpoint,CheckpointRejected
    from uuid import uuid4
    row=load_prepared(directory,company,mission)
    if row["checkpoint_mode"]=="local":return False
    secret=grant(company,mission)
    for role in ("intelligence","research","engineering","commercial","verification"):
        remote=RuntimeCheckpoint(company,mission,role,mission,secret=secret,scope=company+"/"+mission)
        if remote.request("GET") is not None:
            raise ValueError("Remote checkpoint already exists; no fresh execution")
    wrong=str(uuid4())
    try:
        RuntimeCheckpoint(company,wrong,"intelligence",mission,secret=secret,scope=company+"/"+wrong).request("GET")
    except CheckpointRejected as exc:
        if exc.status!=403 or exc.code!="checkpoint_scope_unavailable":raise ValueError("Wrong-scope rejection not verified") from None
    else:raise ValueError("Wrong scope was not rejected")
    return True

def authorize_activation(api,directory,company,mission,leader,binding):
    row=load_prepared(directory,company,mission)
    if row["scope_sha256"]!=binding["scope_sha256"]:raise ValueError("Prepared scope changed")
    task=api("/api/issues/"+mission)
    if (task.get("id")!=mission or task.get("companyId")!=company or task.get("parentId") is not None
        or task.get("assigneeAgentId") is not None or task.get("status")!="todo"
        or task.get("title")!=binding["parent_title"] or task.get("description")!=binding["parent_description"]):
        raise ValueError("Prepared parent no longer eligible")
    # Before any worker is assigned: verify the exact scope, private file and
    # signed remote GET. Never fall back to local when remote was requested.
    remote=preflight(directory,company,mission)
    if row["model_mode"]=="local":
        from model_plan import check_local_model
        check_local_model()
    exclusive(Path(directory)/"activation.json",{"company":company,"mission":mission,
        "minister":leader,"scope_sha256":row["scope_sha256"],"remote_checkpoint_preflight":remote,"model_mode":row["model_mode"]})
    api("/api/issues/"+mission,"PATCH",{"assigneeAgentId":leader})
    return remote
