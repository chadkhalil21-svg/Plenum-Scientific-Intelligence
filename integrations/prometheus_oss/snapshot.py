"""Attestable public synthetic graph backup and fresh-runner disaster restore.

Use the upstream SQLite database, not a serialized replacement state. Never
run this exporter on owner-private data. GitHub provenance is verified by the
workflow before restore. The manifest binds all bytes and logical DB contents.
"""
import hashlib,json,os,re,shutil,sqlite3,sys
from pathlib import Path
from contextlib import closing
import stat

SAFE=re.compile(r"(manifest|pause|read_evidence|estimate_review|record_decision|estimate-rejected|decision-rejected|model-[0-9]{2}\.(reserved|result))\.json")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe_path(p):
    # Reject traversal and symlinks in every component, including ancestors.
    if ".." in p.parts:raise ValueError("Traversal in checkpoint path")
    p=p.absolute()
    for entry in (*reversed(p.parents),p):
        if entry.is_symlink():raise ValueError("Symlink in checkpoint path")
    return p

def graph_name(name):
    return isinstance(name,str) and (name=="graph.sqlite" or SAFE.fullmatch(name) is not None)

def logical(p,*,sealed=False):
    exact(p)
    # SQLite's context manager does not close the connection. A live source
    # may have WAL pages; the sealed backup must be standalone.
    uri=p.resolve().as_uri()+"?mode=ro"+("&immutable=1" if sealed else "")
    with closing(sqlite3.connect(uri,uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchall()!=[("ok",)]:raise ValueError("SQLite integrity failure")
        rows=list(db.iterdump())
        if not rows or len(rows)>100000:raise ValueError("Unexpected database size")
        return hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()

def copy_closed_database(src,dest,*,sealed_source=False):
    safe_path(src);safe_path(dest)
    if dest.exists():raise FileExistsError("Database destination must be absent")
    before=logical(src,sealed=sealed_source)
    uri=src.resolve().as_uri()+"?mode=ro"+("&immutable=1" if sealed_source else "")
    with closing(sqlite3.connect(uri,uri=True)) as a,closing(sqlite3.connect(dest)) as b:
        a.backup(b)
        b.commit()
        if b.execute("PRAGMA journal_mode=DELETE").fetchone()!=("delete",):
            raise ValueError("Cannot seal standalone database")
        b.commit()
    for suffix in ("-wal","-shm","-journal"):
        sidecar=dest.with_name(dest.name+suffix)
        if sidecar.exists() or sidecar.is_symlink():raise ValueError("Unclosed backup sidecar")
    if logical(dest,sealed=True)!=before:raise ValueError("Backup logical content changed")
    return before
def exact(p):
    safe_path(p)
    if not p.is_file() or p.is_symlink() or not stat.S_ISREG(p.lstat().st_mode) or p.stat().st_size>10_000_000:raise ValueError("Unsafe checkpoint file")
    return {"size":p.stat().st_size,"sha256":sha(p)}
def ci():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise PermissionError("Only synthetic public CI backup")
    return {"run_id":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"run_attempt":os.environ["GITHUB_RUN_ATTEMPT"]}
def manifest(root):
    safe_path(root)
    if not root.is_dir() or root.is_symlink():raise ValueError("Unsafe backup root")
    entries=list(sorted(root.iterdir()))
    if len(entries)>64 or any(not graph_name(p.name) for p in entries):raise ValueError("Unsafe backup tree")
    result={p.name:exact(p) for p in entries}
    if "graph.sqlite" not in result:raise ValueError("Missing database")
    return result
def seal(source,target,dependencies):
    ident=ci()
    if ident["run_attempt"]!="1":raise PermissionError("No replayed qualification")
    source=safe_path(source);target=safe_path(target);dependencies=safe_path(dependencies)
    if not source.is_dir() or not (source/"pause.json").is_file():raise ValueError("Missing acknowledged source")
    if target==source or source in target.parents or target in source.parents:raise ValueError("Overlapping checkpoint roots")
    target.mkdir(parents=True,exist_ok=False,mode=0o700);graph=target/"graph";graph.mkdir(mode=0o700)
    for p in source.iterdir():
        if p.name in ("graph.sqlite","graph.sqlite-wal","graph.sqlite-shm"):
            exact(p);continue
        if not SAFE.fullmatch(p.name):raise ValueError("Unreviewed checkpoint path")
        exact(p);shutil.copyfile(p,graph/p.name)
    src=source/"graph.sqlite";exact(src)
    before=copy_closed_database(src,graph/"graph.sqlite")
    exact(dependencies);shutil.copyfile(dependencies,target/"dependencies.txt")
    row={**ident,"schema":"plenum-ci-sqlite-backup-v1","source_job":os.environ["GITHUB_JOB"],
        "source_runner":os.environ["RUNNER_NAME"],"source_logical_sha256":before,"files":manifest(graph),
        "dependency_lock":exact(target/"dependencies.txt"),"paid_inference":False,"synthetic_public_only":True}
    (target/"backup.json").write_text(json.dumps(row,sort_keys=True),encoding="utf-8")
def restore(source,target,proof):
    ident=ci();source=safe_path(source);target=safe_path(target);proof=safe_path(proof)
    if not source.is_dir() or source.is_symlink() or set(p.name for p in source.iterdir())!={"graph","backup.json","dependencies.txt"}:raise ValueError("Unexpected backup files")
    exact(source/"backup.json");exact(source/"dependencies.txt")
    row=json.loads((source/"backup.json").read_text())
    if target==source or source in target.parents or target in source.parents or proof==source or source in proof.parents or proof==target or target in proof.parents:raise ValueError("Overlapping restore paths")
    if proof.exists() or proof.is_symlink():raise FileExistsError("Restore proof destination must be absent")
    if row["schema"]!="plenum-ci-sqlite-backup-v1" or any(row.get(k)!=v for k,v in ident.items()) or row["source_job"]!="prepare" or row["source_runner"]==os.environ["RUNNER_NAME"] or row["paid_inference"] is not False or row["synthetic_public_only"] is not True:
        raise PermissionError("Wrong runner or original backup identity")
    graph=safe_path(source/"graph")
    if not isinstance(row["files"],dict) or any(not graph_name(name) for name in row["files"]):raise ValueError("Unsafe manifest path")
    if manifest(graph)!=row["files"] or exact(source/"dependencies.txt")!=row["dependency_lock"] or logical(graph/"graph.sqlite",sealed=True)!=row["source_logical_sha256"]:raise ValueError("Backup integrity mismatch")
    if target.exists() or target.is_symlink():raise FileExistsError("Restore requires absent destination")
    target.mkdir(parents=True,mode=0o700)
    # Rebuild a new SQLite file using the database backup API.
    for p in graph.iterdir():
        if p.name!="graph.sqlite":shutil.copyfile(p,target/p.name)
    if copy_closed_database(graph/"graph.sqlite",target/"graph.sqlite",sealed_source=True)!=row["source_logical_sha256"]:raise ValueError("Restored database differs")
    if {k:v for k,v in manifest(target).items() if k!="graph.sqlite"}!={k:v for k,v in row["files"].items() if k!="graph.sqlite"}:raise ValueError("Restored receipt bytes differ")
    value={**ident,"schema":"plenum-ci-sqlite-restore-v1","backup_manifest_sha256":sha(source/"backup.json"),
        "source_runner":row["source_runner"],"restore_runner":os.environ["RUNNER_NAME"],"logical_sha256":row["source_logical_sha256"],
        "restored_database_sha256":sha(target/"graph.sqlite"),"immutable_prefix":{k:v for k,v in row["files"].items() if k!="graph.sqlite"},
        "separate_runner":True,"database_integrity_verified":True,"paid_inference":False,"model_calls_replayed":0,"provider_calls_replayed":0}
    proof.write_text(json.dumps(value,sort_keys=True),encoding="utf-8")
def check_prefix(root,proof):
    root=safe_path(root);proof=safe_path(proof);exact(proof)
    row=json.loads(proof.read_text())
    if row["schema"]!="plenum-ci-sqlite-restore-v1" or row["separate_runner"] is not True or row["paid_inference"] is not False or row["model_calls_replayed"]!=0 or row["provider_calls_replayed"]!=0:raise ValueError("Invalid restore proof")
    for name,expected in row["immutable_prefix"].items():
        if not SAFE.fullmatch(name) or exact(root/name)!=expected:raise ValueError("Predecessor receipt changed")
    logical(root/"graph.sqlite")
    return row
if __name__=="__main__":
    action,*args=sys.argv[1:]
    if action=="seal":seal(*map(Path,args))
    elif action=="restore":restore(*map(Path,args))
    elif action=="verify":check_prefix(*map(Path,args))
    else:raise SystemExit("Unknown snapshot action")
