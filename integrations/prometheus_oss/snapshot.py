"""Attestable public synthetic graph backup and fresh-runner disaster restore.

Use the upstream SQLite database, not a serialized replacement state. Never
run this exporter on owner-private data. GitHub provenance is verified by the
workflow before restore. The manifest binds all bytes and logical DB contents.
"""
import hashlib,json,os,re,shutil,sqlite3,sys
from pathlib import Path

SAFE=re.compile(r"(manifest|pause|read_evidence|estimate_review|record_decision|estimate-rejected|decision-rejected|model-[0-9]{2}\.(reserved|result))\.json")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def logical(p):
    with sqlite3.connect(p.resolve().as_uri()+"?mode=ro",uri=True) as db:
        if db.execute("PRAGMA integrity_check").fetchall()!=[("ok",)]:raise ValueError("SQLite integrity failure")
        rows=list(db.iterdump())
        if not rows or len(rows)>100000:raise ValueError("Unexpected database size")
        return hashlib.sha256("\n".join(sorted(rows)).encode()).hexdigest()
def exact(p):
    if not p.is_file() or p.is_symlink() or p.stat().st_size>10_000_000:raise ValueError("Unsafe checkpoint file")
    return {"size":p.stat().st_size,"sha256":sha(p)}
def ci():
    if os.environ.get("GITHUB_ACTIONS")!="true":raise PermissionError("Only synthetic public CI backup")
    return {"run_id":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"run_attempt":os.environ["GITHUB_RUN_ATTEMPT"]}
def manifest(root):
    return {p.name:exact(p) for p in sorted(root.iterdir()) if p.is_file() and not p.is_symlink()}
def seal(source,target,dependencies):
    ident=ci()
    if ident["run_attempt"]!="1":raise PermissionError("No replayed qualification")
    if not source.is_dir() or source.is_symlink() or not (source/"pause.json").is_file():raise ValueError("Missing acknowledged source")
    target.mkdir(parents=True,exist_ok=False);graph=target/"graph";graph.mkdir()
    for p in source.iterdir():
        if p.name in ("graph.sqlite","graph.sqlite-wal","graph.sqlite-shm"):continue
        if not SAFE.fullmatch(p.name):raise ValueError("Unreviewed checkpoint path")
        exact(p);shutil.copyfile(p,graph/p.name)
    src=source/"graph.sqlite";exact(src)
    before=logical(src)
    with sqlite3.connect(src.resolve().as_uri()+"?mode=ro",uri=True) as a,sqlite3.connect(graph/"graph.sqlite") as b:
        a.backup(b)
    if logical(graph/"graph.sqlite")!=before:raise ValueError("Backup logical content changed")
    exact(dependencies);shutil.copyfile(dependencies,target/"dependencies.txt")
    row={**ident,"schema":"plenum-ci-sqlite-backup-v1","source_job":os.environ["GITHUB_JOB"],
        "source_runner":os.environ["RUNNER_NAME"],"source_logical_sha256":before,"files":manifest(graph),
        "dependency_lock":exact(target/"dependencies.txt"),"paid_inference":False,"synthetic_public_only":True}
    (target/"backup.json").write_text(json.dumps(row,sort_keys=True),encoding="utf-8")
def restore(source,target,proof):
    ident=ci();row=json.loads((source/"backup.json").read_text())
    if set(p.name for p in source.iterdir())!={"graph","backup.json","dependencies.txt"}:raise ValueError("Unexpected backup files")
    if row["schema"]!="plenum-ci-sqlite-backup-v1" or any(row.get(k)!=v for k,v in ident.items()) or row["source_job"]!="prepare" or row["source_runner"]==os.environ["RUNNER_NAME"] or row["paid_inference"] is not False or row["synthetic_public_only"] is not True:
        raise PermissionError("Wrong runner or original backup identity")
    graph=source/"graph"
    if any(not p.is_file() or p.is_symlink() or (p.name!="graph.sqlite" and not SAFE.fullmatch(p.name)) for p in graph.iterdir()):raise ValueError("Unsafe backup tree")
    if manifest(graph)!=row["files"] or exact(source/"dependencies.txt")!=row["dependency_lock"] or logical(graph/"graph.sqlite")!=row["source_logical_sha256"]:raise ValueError("Backup integrity mismatch")
    if target.exists() or target.is_symlink():raise FileExistsError("Restore requires absent destination")
    target.mkdir(parents=True,mode=0o700)
    # Rebuild a new SQLite file using the database backup API.
    for p in graph.iterdir():
        if p.name!="graph.sqlite":shutil.copyfile(p,target/p.name)
    with sqlite3.connect((graph/"graph.sqlite").resolve().as_uri()+"?mode=ro",uri=True) as a,sqlite3.connect(target/"graph.sqlite") as b:a.backup(b)
    if logical(target/"graph.sqlite")!=row["source_logical_sha256"]:raise ValueError("Restored database differs")
    if {k:v for k,v in manifest(target).items() if k!="graph.sqlite"}!={k:v for k,v in row["files"].items() if k!="graph.sqlite"}:raise ValueError("Restored receipt bytes differ")
    value={**ident,"schema":"plenum-ci-sqlite-restore-v1","backup_manifest_sha256":sha(source/"backup.json"),
        "source_runner":row["source_runner"],"restore_runner":os.environ["RUNNER_NAME"],"logical_sha256":row["source_logical_sha256"],
        "restored_database_sha256":sha(target/"graph.sqlite"),"immutable_prefix":{k:v for k,v in row["files"].items() if k!="graph.sqlite"},
        "separate_runner":True,"database_integrity_verified":True,"paid_inference":False,"model_calls_replayed":0,"provider_calls_replayed":0}
    proof.write_text(json.dumps(value,sort_keys=True),encoding="utf-8")
def check_prefix(root,proof):
    row=json.loads(proof.read_text())
    if row["schema"]!="plenum-ci-sqlite-restore-v1" or row["separate_runner"] is not True or row["paid_inference"] is not False:raise ValueError("Invalid restore proof")
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
