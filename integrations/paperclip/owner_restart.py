"""Owner-only same-container restart proof; no provisioning, private export or inference."""
import hashlib,json,os,stat,subprocess,sys,time
from pathlib import Path
from uuid import UUID
from checkpoint_store import encoded,exclusive

NAME="plenum-paperclip-production"
SCHEMA="plenum-live-verification-v1"
def digest(x):return hashlib.sha256(encoded(x)).hexdigest()
def canonical(x):
    if str(UUID(x))!=x:raise ValueError("Invalid owner identity")
    return x
def run(args):
    return subprocess.run(args,check=True,capture_output=True,text=True,timeout=120).stdout
def state(runner):
    fmt='{"id":{{json .Id}},"started":{{json .State.StartedAt}},"running":{{json .State.Running}},"mounts":{{json .Mounts}},"ports":{{json .NetworkSettings.Ports}},"network":{{json .HostConfig.NetworkMode}}}'
    x=json.loads(runner(["docker","inspect","--format",fmt,NAME]))
    if x["running"] is not True or x["network"]=="host" or any(v for v in (x["ports"] or {}).values()):raise PermissionError("Private unexposed running board required")
    if len(x["id"])!=64 or not x["started"]:raise ValueError("Invalid container identity")
    m=[v for v in x["mounts"] if v["Destination"]=="/paperclip"]
    grant=[v for v in x["mounts"] if v["Destination"]=="/run/plenum-checkpoint"]
    if len(m)!=1 or m[0]["Type"]!="volume" or not m[0]["RW"] or len(grant)!=1 or grant[0]["RW"]:raise PermissionError("Existing persistent board and readonly grant mount required")
    return {"container_sha256":digest(x["id"]),"started":x["started"],"volume_sha256":digest(m[0]),"grant_mount_sha256":digest(grant[0])}
def command(cid,mid,action):
    return ["docker","exec","--user","node","-e","PYTHONPATH=/plenum/src","-e","PLENUM_PERSISTENT_BOARD=confirmed",
            "-e","PLENUM_PAPERCLIP_COMPANY_UUID="+cid,"-e","PLENUM_PAPERCLIP_MISSION_UUID="+mid,
            NAME,"python3","/plenum/integrations/paperclip/sequential_mission.py",action]
def output(text,schema=None):
    rows=[]
    for line in text.splitlines():
        try:x=json.loads(line)
        except ValueError:continue
        if isinstance(x,dict) and (schema is None or x.get("schema")==schema):rows.append(x)
    if len(rows)!=1:raise ValueError("Expected one native receipt")
    return rows[0]
def live(runner,cid,mid):
    row=output(runner(command(cid,mid,"verify-live")),SCHEMA)
    expected={"company":cid,"mission":mid,"verified_divisions":5,"verified_profile_work_products":11,
        "minister_model_executed":True,"remote_checkpoint_count":5,"wrong_scope_http_status":403,
        "wrong_scope_error":"checkpoint_scope_unavailable","independent_native_readback":True,"provider_calls_replayed":0,"paid_inference":False}
    if any(type(row.get(k)) is not type(v) or row[k]!=v for k,v in expected.items()):raise ValueError("Owner live proof rejected")
    if set(row["remote_checkpoints"])!={"intelligence","research","engineering","commercial","verification"}:raise ValueError("Missing live remote checkpoints")
    return row
def stable(row):
    keys=("company","mission","scope_sha256","qualification_sha256","model_receipt_sha256","remote_checkpoints","recovery_receipt_sha256","replan_receipt_sha256")
    return {k:row[k] for k in keys}
def model_off(runner):
    code="import socket; s=socket.socket(); s.settimeout(2); rc=s.connect_ex(('127.0.0.1',11434)); s.close(); assert rc != 0"
    runner(["docker","exec","--user","node",NAME,"python3","-c",code])
def prove(cid,mid,runner=run,sleep=time.sleep):
    canonical(cid);canonical(mid)
    if os.getenv("GITHUB_ACTIONS")=="true":raise PermissionError("No owner proof in public CI")
    before=state(runner);model_off(runner);pre=live(runner,cid,mid)
    runner(["docker","restart",NAME]);after=state(runner)
    if before["started"]==after["started"] or any(before[k]!=after[k] for k in ("container_sha256","volume_sha256","grant_mount_sha256")):
        raise ValueError("Same-volume restart not demonstrated")
    for _ in range(45):
        try:
            runner(["docker","exec",NAME,"curl","--fail","--silent","http://127.0.0.1:3100/api/health"]);break
        except subprocess.CalledProcessError:sleep(2)
    else:raise RuntimeError("Board unavailable after restart")
    model_off(runner)
    restart=output(runner(command(cid,mid,"restart-readback")))
    if restart.get("container_restart_readback") is not True or restart.get("provider_calls_replayed")!=0 or restart.get("qualification_sha256")!=pre["qualification_sha256"]:raise ValueError("Restart readback mismatch")
    post=live(runner,cid,mid)
    if stable(pre)!=stable(post) or not post["restart_readback_receipt_sha256"]:raise ValueError("Live remote continuity mismatch")
    return {"schema":"plenum-owner-same-volume-live-restart-v1","company":cid,"mission":mid,
        "before":before,"after":after,"before_live_sha256":digest(pre),"after_live_sha256":digest(post),
        "qualification_sha256":post["qualification_sha256"],"remote_checkpoint_manifest_sha256":digest(post["remote_checkpoints"]),
        "verified_divisions":5,"verified_profile_work_products":11,"remote_checkpoint_count":5,"wrong_scope_http_status":403,
        "actual_same_container_restart":True,"same_volume":True,"model_unreachable_before_and_after":True,
        "provider_calls_replayed":0,"model_calls_replayed":0,"paid_inference":False,
        "native_database_restored_from_backup":False,"inflight_recovery_verified":False}
def main():
    if len(sys.argv)!=5 or sys.argv[1]!="--confirm-owner-quiesced":raise SystemExit("Owner confirmation, company UUID, mission UUID and private output directory required")
    _,_,cid,mid,root=sys.argv
    p=Path(root);st=p.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.geteuid() or stat.S_IMODE(st.st_mode)!=0o700:raise PermissionError("Owner-only 0700 output directory required")
    target=p/(canonical(mid)+".live-restart.json")
    if target.exists() or target.is_symlink():raise FileExistsError("Never overwrite an existing proof")
    row=prove(cid,mid);exclusive(target,row)
    print(json.dumps({"owner_proof_sha256":digest(row),"paid_inference":False,"private_receipt_written":True}))
if __name__=="__main__":main()
