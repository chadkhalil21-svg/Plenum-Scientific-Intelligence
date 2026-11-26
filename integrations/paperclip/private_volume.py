"""Owner-local, HMAC authenticated completed-mission evidence recovery.

No external calls, no GitHub/private Cloudflare credential, no board DB export.
The owner is responsible for an independent durable private disk, grant custody,
and quiescing the native board. No recovery of ambiguous/in-flight effects.
"""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from uuid import UUID
from checkpoint_store import checked,encoded,exclusive

MAX_TOTAL=800000
SAFE=re.compile(r"[A-Za-z0-9_.-]{1,100}")
def canonical(value):
    if str(UUID(value))!=value:raise ValueError("Invalid identity")
    return value

def secure_dir(path):
    path=Path(path)
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o700:
        raise PermissionError("Expected owner-only directory")
    return path

def grant(root,company,mission):
    scope=canonical(company)+"/"+canonical(mission)
    fd=os.open(root/"grant.json",os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o600 or info.st_size>1024:
            raise PermissionError("Expected owner-only local grant")
        row=json.loads(stream.read(1025))
    if set(row)!={"scope","key_hex"} or row["scope"]!=scope or not re.fullmatch(r"[0-9a-f]{64}",row["key_hex"]):
        raise PermissionError("Local checkpoint grant scope mismatch")
    return bytes.fromhex(row["key_hex"])

def file_bytes(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,"rb") as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>MAX_TOTAL:raise ValueError("Unsafe evidence file")
        raw=stream.read(MAX_TOTAL+1)
    if len(raw)>MAX_TOTAL:raise ValueError("Evidence size")
    return raw

def path_parts(name):
    parts=name.split("/")
    if len(parts)>6 or any(not SAFE.fullmatch(p) or p in (".","..") for p in parts):
        raise ValueError("Unsafe evidence path")
    return parts

def collect(directory):
    entries={};size=0
    if not directory.is_dir() or directory.is_symlink():raise ValueError("Unsafe evidence directory")
    for p in sorted(directory.rglob("*")):
        if p.is_symlink():raise ValueError("Evidence symlink")
        name=p.relative_to(directory).as_posix();path_parts(name)
        if p.is_dir():continue
        raw=file_bytes(p);size+=len(raw)
        if size>MAX_TOTAL or len(entries)>=200:raise ValueError("Evidence bound")
        entries[name]=base64.b64encode(raw).decode("ascii")
    return entries

def accepted(entries,company,mission):
    def read(name):return json.loads(base64.b64decode(entries[name],validate=True))
    q=read("qualification.json");p=read("prepared.json");r=read("restart-timing.json")
    digest=hashlib.sha256(encoded(q)).hexdigest()
    if (q["company"]!=company or q["parent"]!=mission or q["paid_inference"] is not False or
        q["verified_divisions"]!=5 or q["verified_profile_work_products"]!=11 or
        p["company"]!=company or p["mission"]!=mission or p["scope_sha256"]!=q["scope_sha256"] or
        r["qualification_sha256"]!=digest or r["container_restart_readback"] is not True or r["provider_calls_replayed"]!=0):
        raise ValueError("Only completed accepted evidence can be sealed")
    return digest

def sign(key,body):return hmac.new(key,b"plenum-local-private-volume-v1\n"+encoded(body),hashlib.sha256).hexdigest()

def seal(directory,root,company,mission):
    root=secure_dir(root)
    if root.resolve()==directory.resolve() or root.resolve().is_relative_to(directory.resolve()) or directory.resolve().is_relative_to(root.resolve()):
        raise ValueError("Private store must be separate from evidence tree")
    key=grant(root,company,mission)
    entries=collect(directory)
    body={"schema":"plenum-local-private-volume-v1","company":company,"mission":mission,
          "qualification_sha256":accepted(entries,company,mission),"entries":entries}
    exclusive(root/"snapshot.json",{"body":body,"signature":sign(key,body)})
    os.chmod(root/"snapshot.json",0o600)
    return body["qualification_sha256"]

def restore(directory,root,company,mission):
    root=secure_dir(root)
    if root.resolve()==directory.resolve() or root.resolve().is_relative_to(directory.resolve()) or directory.resolve().is_relative_to(root.resolve()):
        raise ValueError("Private store must be separate from evidence tree")
    key=grant(root,company,mission)
    row=checked(root/"snapshot.json",{})
    if set(row)!={"body","signature"} or not hmac.compare_digest(sign(key,row["body"]),row["signature"]):
        raise PermissionError("Snapshot authentication failed")
    body=row["body"]
    if set(body)!={"schema","company","mission","qualification_sha256","entries"} or body["schema"]!="plenum-local-private-volume-v1" or body["company"]!=company or body["mission"]!=mission:
        raise PermissionError("Snapshot scope mismatch")
    if accepted(body["entries"],company,mission)!=body["qualification_sha256"]:raise ValueError("Qualification digest mismatch")
    if directory.exists() or directory.is_symlink():raise FileExistsError("Never overwrite live evidence")
    directory.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temporary=Path(tempfile.mkdtemp(prefix=".restore-",dir=directory.parent))
    try:
        for name,value in body["entries"].items():
            path=temporary.joinpath(*path_parts(name));path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            data=base64.b64decode(value,validate=True)
            with open(path,"xb") as stream:
                os.chmod(path,0o600);stream.write(data);stream.flush();os.fsync(stream.fileno())
        if collect(temporary)!=body["entries"]:raise ValueError("Restore bytes differ")
        # Owner must hold the existing company submission lock and quiesce board.
        # Rename only into absent destination; no automatic mission execution.
        if directory.exists() or directory.is_symlink():raise FileExistsError("Destination changed")
        os.rename(temporary,directory)
        dfd=os.open(directory.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(dfd)
        finally:os.close(dfd)
    finally:
        if temporary.exists():
            import shutil
            shutil.rmtree(temporary)
    return body["qualification_sha256"]

if __name__=="__main__":
    if len(sys.argv)!=6 or sys.argv[1] not in ("seal","restore"):raise SystemExit("Explicit local evidence action required")
    action,source,store,company,mission=sys.argv[1:]
    digest={"seal":seal,"restore":restore}[action](Path(source),Path(store),company,mission)
    print(json.dumps({"action":action,"qualification_sha256":digest,"model_calls":0,"provider_calls":0,"paid_inference":False}))
