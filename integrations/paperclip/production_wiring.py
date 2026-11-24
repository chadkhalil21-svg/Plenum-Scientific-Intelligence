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
    root=GRANT_DIR if root is None else Path(root)
    scope=canonical(company)+"/"+canonical(mission)
    if root.is_symlink():raise PermissionError("Unsafe private grant directory")
    fd=os.open(root/(mission+".json"),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_mode&0o077 or info.st_size>4096:
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
    remote=checkpoint_for(directory,company,mission,"intelligence",mission)
    if remote is not None and remote.request("GET") is not None:
        raise ValueError("Remote checkpoint already exists; no fresh execution")
    return remote is not None

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
