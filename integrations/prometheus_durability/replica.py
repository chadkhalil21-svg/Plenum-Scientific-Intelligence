"""Use upstream Litestream for DBOS SQLite replication. Seal all replica bytes.
Only relative canonical file names, public synthetic/accepted evidence, no secrets.
"""
import hashlib,json,os,re,shutil,signal,sqlite3,subprocess,sys,time
from contextlib import closing
from pathlib import Path
from receipts import read_accepted,sha,encoded,digest
SAFE=re.compile(r"[a-zA-Z0-9._-]{1,200}")
def identity():
    if os.environ.get("GITHUB_ACTIONS")!="true" or os.environ.get("GITHUB_RUN_ATTEMPT")!="1":raise PermissionError("Original public CI only")
    return {"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"job":os.environ["GITHUB_JOB"],"boot_sha256":sha(Path("/proc/sys/kernel/random/boot_id"))}
def logical(p):
    if not p.is_file() or p.is_symlink():raise ValueError("Missing SQLite file")
    with closing(sqlite3.connect(p.resolve().as_uri()+"?mode=ro",uri=True)) as db:
        if db.execute("pragma integrity_check").fetchall()!=[("ok",)]:raise ValueError("SQLite corruption")
        return digest(sorted(db.iterdump()))
def tree(root):
    if not root.is_dir() or root.is_symlink():raise ValueError("Unsafe replica root")
    result={};total=0
    for p in sorted(root.rglob("*")):
        rel=p.relative_to(root)
        if p.is_symlink() or any(x in (".","..") or not SAFE.fullmatch(x) for x in rel.parts):raise ValueError("Unsafe replica path")
        if p.is_dir():continue
        if not p.is_file():raise ValueError("Nonregular replica")
        total+=p.stat().st_size
        if total>50_000_000 or len(result)>500:raise ValueError("Replica bound")
        result[rel.as_posix()]={"sha256":sha(p),"bytes":p.stat().st_size}
    if not result:raise ValueError("Empty replica")
    return result
def ls(*args):return subprocess.run(["litestream",*args],check=True,capture_output=True,text=True,timeout=20)
def seal(source,bundle):
    ident=identity();source=source.resolve();bundle=bundle.resolve()
    read_accepted(source/"original.zip")
    if (source/"step-two.json").exists() or not (source/"step-one.json").is_file():raise ValueError("Expected interrupted workflow")
    bundle.mkdir(mode=0o700,parents=True,exist_ok=False)
    expected=logical(source/"workflow.sqlite")
    replica=bundle/"replica"
    url=replica.as_uri()
    probe=source/"probe.sqlite"
    with (source/"litestream.log").open("wb") as log:
        process=subprocess.Popen(["litestream","replicate",str(source/"workflow.sqlite"),url],stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(25):
                if process.poll() is not None:raise RuntimeError("Litestream replication exited")
                for suffix in ("","-wal","-shm"):
                    p=probe.with_name(probe.name+suffix)
                    if p.exists():p.unlink()
                try:
                    ls("restore","-o",str(probe),url)
                    if logical(probe)==expected:break
                except (subprocess.CalledProcessError,ValueError,sqlite3.Error):pass
                time.sleep(2)
            else:raise RuntimeError("Replica has not reached committed database")
        finally:
            if process.poll() is None:process.send_signal(signal.SIGTERM);process.wait(timeout=20)
    # Do not trust the probe made while replication was running. Verify final repo.
    for suffix in ("","-wal","-shm"):
        p=probe.with_name(probe.name+suffix)
        if p.exists():p.unlink()
    ls("restore","-o",str(probe),url)
    if logical(probe)!=expected:raise ValueError("Final replica logical contents")
    for n in ("original.zip","step-one.json","dependencies.txt"):
        if (source/n).is_symlink():raise ValueError("Unsafe source")
        shutil.copyfile(source/n,bundle/n)
    row={"schema":"plenum-litestream-dbos-public-v1","source":ident,"files":tree(bundle),"logical_sha256":expected,
        "litestream_version":ls("version").stdout.strip(),"paid_inference":False}
    (bundle/"backup.json").write_bytes(encoded(row))
def restore(bundle,target,proof):
    ident=identity();bundle=bundle.resolve()
    marker=bundle/"backup.json"
    if marker.is_symlink() or not marker.is_file():raise ValueError("Unsafe manifest")
    row=json.loads(marker.read_text())
    if row["schema"]!="plenum-litestream-dbos-public-v1" or row["paid_inference"] is not False or any(row["source"][k]!=ident[k] for k in ("run","commit")) or row["source"]["job"]==ident["job"] or row["source"]["boot_sha256"]==ident["boot_sha256"]:raise ValueError("Wrong backup source")
    if {k:v for k,v in tree(bundle).items() if k!="backup.json"}!=row["files"]:raise ValueError("Replica manifest mismatch")
    read_accepted(bundle/"original.zip")
    if target.exists() or target.is_symlink():raise FileExistsError("Restore target exists")
    target.mkdir(mode=0o700,parents=True)
    for name in ("original.zip","step-one.json","dependencies.txt"):shutil.copyfile(bundle/name,target/name)
    ls("restore","-o",str(target.resolve()/"workflow.sqlite"),(bundle/"replica").as_uri())
    if logical(target/"workflow.sqlite")!=row["logical_sha256"]:raise ValueError("Restored database differs")
    value={"schema":"plenum-litestream-restore-v1","backup_sha256":sha(marker),"source":row["source"],"target":ident,
        "logical_sha256":row["logical_sha256"],"acknowledged_step_sha256":sha(target/"step-one.json"),"separate_runner":True,"paid_inference":False}
    with proof.open("xb") as f:f.write(encoded(value))
if __name__=="__main__":
    action,*args=sys.argv[1:]
    {"seal":seal,"restore":restore}[action](*map(Path,args))
