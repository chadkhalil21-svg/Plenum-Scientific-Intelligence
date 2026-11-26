"""Owner-only read-only preflight. Reachability is not deployment or billing proof."""
import json,os,stat
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,build_opener,ProxyHandler
from acceptance import NoRedirect
from lifecycle import persistent,canonical,owner_company,mission_dir
from production_wiring import GRANT_DIR,load_prepared,preflight
from model_plan import check_local_model
from runtime_checkpoint import ENDPOINT

def grant_directory(path):
    path=Path(path)
    # Exact directory ownership and mode, no symlink, read-only mount.
    info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o700:
        raise PermissionError("Grant directory must be runtime-owned mode 0700")
    if not os.statvfs(path).f_flag & os.ST_RDONLY:
        raise PermissionError("Grant directory must be mounted read-only")
    return True

def health_json(url):
    # Do not send private credentials or trust redirects/proxy substitution.
    with build_opener(ProxyHandler({}),NoRedirect).open(Request(url,headers={"Accept":"application/json"}),timeout=10) as response:
        if response.status!=200:raise ValueError("Health status not 200")
        raw=response.read(8193)
    if len(raw)>8192:raise ValueError("Health response too large")
    row=json.loads(raw)
    if not isinstance(row,dict):raise ValueError("Health response not an object")
    return row

def local_checks(api,root):
    expected={"HOST":"127.0.0.1","PAPERCLIP_BIND":"loopback","PAPERCLIP_DEPLOYMENT_MODE":"local_trusted","PAPERCLIP_DEPLOYMENT_EXPOSURE":"private"}
    if any(os.getenv(k)!=v for k,v in expected.items()):raise PermissionError("Expected private loopback runtime configuration")
    if os.getenv("PAPERCLIP_API_URL","http://127.0.0.1:3100").rstrip("/")!="http://127.0.0.1:3100":
        raise PermissionError("Expected exact loopback board URL")
    board=health_json("http://127.0.0.1:3100/api/health")
    companies=api("/api/companies")
    if not isinstance(companies,list):raise ValueError("Board API unavailable")
    model=check_local_model()
    return {"loopback_health_http_status":200,"private_loopback_configuration":True,
            "native_company_count":len(companies),"model":"qwen3.5:4b","model_digest":model}

def preflight_live(api,root):
    if not persistent() or os.getenv("GITHUB_ACTIONS")=="true" or os.getenv("PLENUM_PAPERCLIP_MODEL")!="local":
        raise PermissionError("Live preflight requires owner persistent local mode")
    local=local_checks(api,root)
    grant_directory(GRANT_DIR)
    worker=health_json(ENDPOINT+"/health")
    if worker.get("state")!="REACHABLE_NOT_A_RUNNING_AGENT" or worker.get("no_model") is not True:
        raise ValueError("Wrong Cloudflare Worker health response")
    mid=os.getenv("PLENUM_PAPERCLIP_MISSION_UUID")
    scoped=None
    if mid:
        cid=owner_company(api);mid=canonical(mid)
        directory=mission_dir(root,cid,mid)
        if load_prepared(directory,cid,mid)["model_mode"]!="local":raise ValueError("Expected staged local model")
        if (directory/"activation.json").exists():raise ValueError("Preflight is for unactivated missions")
        if not preflight(directory,cid,mid):raise ValueError("Expected remote staged mission")
        scoped={"company":cid,"mission":mid,"empty_remote_slots":5,"wrong_scope_http_status":403}
    receipt={"schema":"plenum-live-preflight-v1",**local,"grant_directory_mode":"0700",
             "grant_directory_runtime_owned":True,"grant_directory_read_only":True,
             "worker_health_http_status":200,"worker_health_state":worker["state"],
             "scoped_remote_preflight":scoped,"paid_inference":False,
             "host_port_publication_verified":False,"billing_plan_verified":False,
             "verified_at":datetime.now(timezone.utc).isoformat()}
    print(json.dumps(receipt,sort_keys=True),flush=True)
    return receipt
