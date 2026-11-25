"""Owner-private cold native database recovery candidate.

No production credentials are read; no remote calls, source restart, new
persistent server, volume creation, deletion or public CI. The operator must
independently attest actual production provenance and quiescence, and prepare
a separate existing empty, network-isolated recovery container and volume.
This candidate is not production qualification until executed and accepted.
"""
import argparse, gzip, hashlib, json, os, re, stat, subprocess, tarfile, tempfile, time
from pathlib import Path, PurePosixPath
from uuid import UUID

SOURCE="plenum-paperclip-production"
TARGET="plenum-paperclip-recovery"
IMAGE="ghcr.io/paperclipai/paperclip:2026.1106.0"
REVISION="d69631b01b9c658f80bf8bed389863dce82643e1"
LIMIT=256*1024*1024
EXPANDED=1024*1024*1024
COUNT=100000

def need(ok, message="Owner recovery rejected"):
    if not ok: raise ValueError(message)
def canonical(x):
    need(isinstance(x,str) and str(UUID(x))==x,"Invalid UUID")
    return x
def encoded(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def digest(b): return hashlib.sha256(b).hexdigest()
def filehash(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def secure_dir(p):
    p=Path(p);s=p.lstat()
    need(stat.S_ISDIR(s.st_mode) and s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o700,"Owner-only directory required")
    return p
def private_file(p,limit):
    p=Path(p);secure_dir(p.parent);s=p.lstat()
    need(stat.S_ISREG(s.st_mode) and s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o600 and 0<s.st_size<=limit,"Owner-only regular file required")
    return p
def absent(p):
    need(not p.exists() and not p.is_symlink(),"Destination already exists")
def publish(p,row):
    secure_dir(p.parent);absent(p)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"wb") as f:
        f.write(encoded(row));f.flush();os.fsync(f.fileno())
def docker(*args):
    return subprocess.run(["docker",*args],check=True,capture_output=True,timeout=180).stdout
def inspect(name):
    # Deliberately exclude Config.Env and all credential-bearing fields.
    fmt='{"id":{{json .Id}},"image":{{json .Image}},"started":{{json .State.StartedAt}},"running":{{json .State.Running}},"mounts":{{json .Mounts}},"ports":{{json .NetworkSettings.Ports}},"network":{{json .HostConfig.NetworkMode}},"restart":{{json .HostConfig.RestartPolicy.Name}}}'
    x=json.loads(docker("inspect","--format",fmt,name))
    m=[a for a in x["mounts"] if a["Destination"]=="/paperclip"]
    need(len(m)==1 and m[0]["Type"]=="volume" and m[0]["RW"] is True,"Native writable volume required")
    need(not any(v for v in (x["ports"] or {}).values()) and x["network"]!="host","Unexposed private container required")
    x["volume"]=m[0]["Name"]
    need(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]+",x["volume"]) is not None)
    need(docker("image","inspect",x["image"],"--format",'{{index .Config.Labels "org.opencontainers.image.revision"}}').decode().strip()==REVISION,"Pinned image revision required")
    return x
def no_writer(volume):
    need(not docker("ps","--quiet","--filter","volume="+volume).strip(),"Volume has running container")
def tar_manifest(path,company,mission):
    files={}; seen=set(); total=0; q=None
    expected="plenum-mission-evidence/"+company+"/"+mission+"/qualification.json"
    with tarfile.open(path,"r:*") as t:
        for m in t:
            name=m.name
            if name in (".","./"):
                need(m.isdir(),"Invalid archive root");continue
            if name.startswith("./"):name=name[2:]
            parts=PurePosixPath(name).parts
            need(parts and not name.startswith("/") and not any(x in ("",".","..") for x in name.split("/")) and "\\" not in name and name not in seen and len(seen)<COUNT,"Unsafe archive member")
            seen.add(name)
            need(m.isdir() or m.isfile(),"Archive links and special files rejected")
            if m.isdir():continue
            total+=m.size;need(total<=EXPANDED,"Expanded archive exceeds bound")
            h=hashlib.sha256()
            f=t.extractfile(m);need(f is not None)
            if name==expected:
                need(m.size<=2*1024*1024,"Qualification exceeds bound")
                q=f.read();h.update(q)
            else:
                for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
            files[name]=h.hexdigest()
    pg=[n for n in files if "/base/" in "/"+n]
    need(pg and any(n.endswith("/PG_VERSION") for n in files) and any(n.endswith("/global/pg_control") for n in files),"Native PostgreSQL files missing")
    need(q is not None,"Original qualification missing")
    row=json.loads(q)
    need(row["company"]==company and row["parent"]==mission and row["verified_divisions"]==5 and row["verified_profile_work_products"]==11 and row["paid_inference"] is False,"Native qualification mismatch")
    return {"file_manifest_sha256":digest(encoded(files)),"file_count":len(files),"postgres_file_count":len(pg),"qualification_sha256":digest(encoded(row))}
def volume_tar(volume,image,path,compressed):
    # Explicit source mount; helper has no network and no credentials.
    flags="-czf" if compressed else "-cf"
    with path.open("xb") as out:
        subprocess.run(["docker","run","--rm","--network","none","--user","root","--entrypoint","tar","--mount","type=volume,src="+volume+",dst=/source,readonly",image,"-C","/source",flags,"-","."],stdout=out,stderr=subprocess.DEVNULL,check=True,timeout=600)
        out.flush();os.fsync(out.fileno())
def source_state():
    s=inspect(SOURCE)
    need(s["running"] is False and s["volume"]==SOURCE,"Expected stopped named production volume")
    no_writer(s["volume"]);return s
def baseline(path,company,mission):
    row=json.loads(private_file(path,2*1024*1024).read_bytes())
    # Accept independently recorded native qualification, not just a file hash.
    need(row["company"]==company and row["parent"]==mission and row["verified_divisions"]==5 and row["verified_profile_work_products"]==11 and row["paid_inference"] is False,"Baseline qualification rejected")
    return digest(encoded(row))
def capture(args):
    s=source_state(); out=Path(args.archive);proof=Path(args.proof)
    secure_dir(out.parent);secure_dir(proof.parent);absent(out);absent(proof)
    expected=baseline(Path(args.baseline),args.company,args.mission)
    volume_tar(s["volume"],s["image"],out,True)
    private_file(out,LIMIT)
    m=tar_manifest(out,args.company,args.mission)
    need(m["qualification_sha256"]==expected,"Source qualification differs from independent baseline")
    after=source_state();need(after["id"]==s["id"] and after["started"]==s["started"],"Source changed during capture")
    row={"schema":"plenum-owner-native-cold-capture-v1","company":args.company,"mission":args.mission,"source_commit":args.source_commit,"source_container_sha256":digest(s["id"].encode()),"source_volume":s["volume"],"archive_sha256":filehash(out),**m,"operator_attested_production_provenance":True,"paid_inference":False,"model_calls_replayed":0,"provider_calls_replayed":0}
    publish(proof,row)
    print(json.dumps({"capture_receipt_sha256":digest(encoded(row)),"paid_inference":False}))
def restore(args):
    s=source_state(); t=inspect(TARGET)
    need(t["running"] is False and t["network"]=="none" and t["restart"] in ("","no") and t["id"]!=s["id"] and t["image"]==s["image"] and t["volume"]==TARGET and t["volume"]!=s["volume"],"Expected separate stopped network-isolated recovery target")
    no_writer(t["volume"])
    backup=private_file(Path(args.archive),LIMIT); cap=json.loads(private_file(Path(args.capture_proof),65536).read_bytes())
    proof=Path(args.proof);secure_dir(proof.parent);absent(proof)
    expected=baseline(Path(args.baseline),args.company,args.mission)
    need(cap["schema"]=="plenum-owner-native-cold-capture-v1" and cap["company"]==args.company and cap["mission"]==args.mission and cap["source_commit"]==args.source_commit and cap["source_container_sha256"]==digest(s["id"].encode()) and cap["source_volume"]==s["volume"] and cap["archive_sha256"]==filehash(backup) and cap["qualification_sha256"]==expected,"Capture binding rejected")
    m=tar_manifest(backup,args.company,args.mission)
    need(all(cap[k]==v for k,v in m.items()),"Archive manifest differs")
    # Existing target only; do not silently create a volume or delete any data.
    docker("volume","inspect",t["volume"],"--format","{{.Name}}")
    contents=docker("run","--rm","--network","none","--user","root","--entrypoint","ls","--mount","type=volume,src="+t["volume"]+",dst=/restore,readonly",t["image"],"-A","/restore")
    need(not contents.strip(),"Recovery volume must be empty")
    with backup.open("rb") as f:
        subprocess.run(["docker","run","--rm","-i","--network","none","--user","root","--entrypoint","tar","--mount","type=volume,src="+t["volume"]+",dst=/restore",t["image"],"-C","/restore","-xzpf","-"],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=600)
    with tempfile.TemporaryDirectory(dir=proof.parent) as tmp:
        p=Path(tmp)/"restored.tar.gz";volume_tar(t["volume"],t["image"],p,True)
        need(tar_manifest(p,args.company,args.mission)==m,"Restored native file manifest differs")
    started=False
    try:
        docker("start",TARGET);started=True
        now=inspect(TARGET)
        need(now["id"]==t["id"] and now["network"]=="none" and now["volume"]==t["volume"] and now["started"]!=t["started"],"Recovery target identity changed")
        for _ in range(90):
            try:
                docker("exec",TARGET,"curl","--fail","--silent","http://127.0.0.1:3100/api/health");break
            except subprocess.CalledProcessError:time.sleep(2)
        else:raise ValueError("Recovered board unavailable")
        docker("exec","--user","node",TARGET,"python3","-c","import socket; s=socket.socket(); s.settimeout(2); assert s.connect_ex(('127.0.0.1',11434))!=0; s.close()")
        raw=docker("exec","--user","node","-e","PYTHONPATH=/plenum/src","-e","PLENUM_PERSISTENT_BOARD=confirmed","-e","PLENUM_PAPERCLIP_COMPANY_UUID="+args.company,"-e","PLENUM_PAPERCLIP_MISSION_UUID="+args.mission,TARGET,"python3","/plenum/integrations/paperclip/sequential_mission.py","restart-readback")
        rows=[]
        for line in raw.splitlines():
            try:x=json.loads(line)
            except ValueError:continue
            if isinstance(x,dict) and x.get("container_restart_readback") is True:rows.append(x)
        need(len(rows)==1 and rows[0]["qualification_sha256"]==expected and rows[0]["provider_calls_replayed"]==0,"Independent native board readback failed")
        row={"schema":"plenum-owner-native-cold-restore-v1","company":args.company,"mission":args.mission,"source_commit":args.source_commit,"capture_receipt_sha256":digest(encoded(cap)),"archive_sha256":cap["archive_sha256"],**m,"source_container_sha256":cap["source_container_sha256"],"restored_container_sha256":digest(t["id"].encode()),"separate_volume":True,"network_isolated":True,"native_readback":True,"verified_divisions":5,"verified_profile_work_products":11,"model_calls_replayed":0,"provider_calls_replayed":0,"paid_inference":False,"raw_database_uploaded":False,"operator_attested_production_provenance":True}
    finally:
        if started:docker("stop","--time","60",TARGET)
    source_state();publish(proof,row)
    print(json.dumps({"restore_receipt_sha256":digest(encoded(row)),"paid_inference":False}))
def main():
    need(os.getenv("GITHUB_ACTIONS")!="true" and os.getenv("PLENUM_PERSISTENT_BOARD")=="confirmed","Owner private runtime only")
    os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument("action",choices=("capture","restore"));p.add_argument("--confirm-owner-quiesced",action="store_true");p.add_argument("--confirm-production-provenance",action="store_true")
    for name in ("company","mission","source-commit","archive","baseline","proof"):p.add_argument("--"+name,required=True)
    p.add_argument("--capture-proof");a=p.parse_args()
    need(a.confirm_owner_quiesced and a.confirm_production_provenance,"Owner confirmations required")
    canonical(a.company);canonical(a.mission);need(re.fullmatch("[0-9a-f]{40}",a.source_commit) is not None)
    need(docker("image","inspect",IMAGE,"--format","{{.Id}}").strip(),"Existing pinned image required")
    # Source commit and mounted checkout are separately owner-attested; no automatic deployment.
    need(a.action=="capture" or a.capture_proof is not None,"Capture proof required")
    {"capture":capture,"restore":restore}[a.action](a)
if __name__=="__main__":
    try:main()
    except Exception:raise SystemExit("Owner native recovery failed closed; inspect private state; do not replay ambiguous operations.") from None
