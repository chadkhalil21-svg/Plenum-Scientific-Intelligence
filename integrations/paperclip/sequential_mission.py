"""One deterministic Minister-routed, native Paperclip public mission.

Uses existing scientific/engineering routines and native dependency locks.
No model calls, arbitrary commands, private data, or external account writes.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlencode
from uuid import UUID, uuid4
import traceback
from urllib.error import HTTPError
from acceptance import api
from checkpoint_store import encoded, exclusive
from division_adapter import SPECS, DESCRIPTION, ROOT, MISSION_ORDER, read_evidence, run_assigned

TITLE = "Delegate bounded coastal monitoring evidence mission"
MISSION = "Public NOAA station, scholarly metadata, reviewed validator and commercial evidence brief; no private operations."
STATIONS = {"station_ids": ["8723214"]}
PAPERS = {"paper_survey": SPECS["research"][1]}


def required(row, key, context):
    if not isinstance(row, dict) or key not in row or row.get(key) is None:
        raise ValueError("Missing required field: " + context + "." + key)
    return row[key]


def env_id(key):
    value = os.getenv(key)
    if not value:
        raise ValueError("Missing required environment: " + key)
    return str(UUID(value))


def minister_task(aid, cid):
    # The pinned Process adapter does not guarantee PAPERCLIP_TASK_ID.
    # Same authenticated assigned-issue fallback already proven in #881.
    task_id = os.getenv("PAPERCLIP_TASK_ID")
    if task_id:
        rows = [api("/api/issues/" + str(UUID(task_id)), worker=True)]
    else:
        rows = api("/api/companies/" + cid + "/issues?" + urlencode({
            "assigneeAgentId": aid, "status": "todo,in_progress"}), worker=True)
    if not isinstance(rows, list):
        raise ValueError("Unexpected Minister issue-list shape")
    candidates = [row for row in rows if isinstance(row, dict)
                  and row.get("assigneeAgentId") == aid and row.get("title") == TITLE
                  and row.get("description") == MISSION
                  and row.get("status") in ("todo", "in_progress")]
    if len(candidates) != 1:
        raise ValueError("Expected exactly one authorized Minister mission")
    return candidates[0], str(UUID(required(candidates[0], "id", "minister_task")))


def failure_receipt(stage, exc):
    # No exception text, raw provider payload, frame locals, or environment
    # values. Retain only known missing-field names and source coordinates.
    known = {"PAPERCLIP_TASK_ID","PAPERCLIP_AGENT_ID","PAPERCLIP_COMPANY_ID",
             "PAPERCLIP_API_KEY","PAPERCLIP_RUN_ID","id","companyId","name",
             "result","input_sha256","sha256","status","tasks","parent","minister",
             "artifact_dir","manifest","main_sha256","validation","readback","discovery",
             "structurally_valid_rows","invalid_rows","8723214","lat","lng",
             "assigneeAgentId","issue","role","company","order","functional_verifier_executed_and_passed"}
    frames = [{"file": Path(frame.filename).name, "line": frame.lineno,
               "function": frame.name} for frame in traceback.extract_tb(exc.__traceback__)
              if "/integrations/paperclip/" in frame.filename.replace("\\", "/")]
    # Deliberately do not serialize arbitrary exception messages.
    missing = exc.args[0] if isinstance(exc, KeyError) and exc.args and isinstance(exc.args[0], str) and exc.args[0] in known else None
    if isinstance(exc, ValueError) and exc.args and isinstance(exc.args[0], str):
        prefix = exc.args[0]
        if prefix.startswith(("Missing required field: ", "Missing required environment: ")):
            field = prefix.rsplit(".",1)[-1].rsplit(" ",1)[-1]
            if field in known: missing = field
    row = {"stage":stage,"error_type":type(exc).__name__,"missing_field":missing,
           "http_status":exc.code if isinstance(exc,HTTPError) else None,
           "frames":frames[-8:],"native_run_id":None}
    try: row["native_run_id"]=str(UUID(os.getenv("PAPERCLIP_RUN_ID","")))
    except ValueError: pass
    ROOT.mkdir(parents=True,exist_ok=True,mode=0o700)
    exclusive(ROOT/("failure-"+stage+"-"+uuid4().hex+".json"),row)
    print(json.dumps(row),flush=True)


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def scope_inputs(prior):
    return {key: digest(value) for key,value in prior.items()}


def commercial_brief(prior):
    from plenum_ai.chief_team_mission import _station_rows
    row = _station_rows(prior["intelligence"]["result"], ("8723214",))[0]
    engineering = prior["engineering"]["result"]
    papers = prior["research"]["result"]["readback"]
    return {
        "objective":"Assess a bounded coastal monitoring evidence opportunity",
        "facts":{"station_id":row["id"],"station_name":required(row,"name","station"),"coordinates":[row["lat"],row["lng"]],
                 "scholarly_dois":sorted(papers),
                 "structurally_valid_rows":engineering["validation"]["structurally_valid_rows"]},
        "recommendation":"Scope a read-only coastal metadata and literature screening pilot",
        "next_owner":"Scientific Research and Engineering",
        "next_action":"Obtain separate evidence for corrosion exposure, instrumentation and customer requirements",
        "limitations":["NOAA station metadata is not corrosion or water-level measurement evidence",
                       "Crossref metadata is not full-paper scientific validation",
                       "No sales, readiness, ROI or financial claims"],
        "new_paid_services":False,"external_actions_executed":False
    }


def verify(prior,directory,*,functional_test=False):
    from plenum_ai.chief_contract_plan import check_contract_result
    from plenum_ai.reviewed_domain_workers import DOMAIN_FILES
    expected=MISSION_ORDER[:-1]
    if set(prior)!=set(expected):
        raise ValueError("Missing original producers")
    for i,role in enumerate(expected):
        value=prior[role]
        if required(value,"input_sha256","producer_receipt")!=scope_inputs({k:prior[k] for k in expected[:i]}):
            raise ValueError("Dependency receipt hash mismatch")
    intel=prior["intelligence"]["result"]
    check_contract_result("noaa_metadata",STATIONS,{},intel)
    research=prior["research"]["result"]
    check_contract_result("paper_discovery",PAPERS,{},research["discovery"])
    check_contract_result("paper_readback",PAPERS,{"paper_discovery":research["discovery"]},research["readback"])
    eng=prior["engineering"]["result"]
    check_contract_result("station_validation",STATIONS,{"noaa_metadata":intel},eng["validation"])
    if eng["validation"]["invalid_rows"]!=0 or eng["validation"]["structurally_valid_rows"]!=1:
        raise ValueError("Unexpected station validation findings")
    name=eng["artifact_dir"]
    if not isinstance(name,str) or not name.startswith("engineering-artifact-") or Path(name).name!=name:
        raise ValueError("Unsafe artifact location")
    artifact=directory/name
    manifest=json.loads((artifact/"manifest.json").read_text())
    source=artifact/"main.py"
    if (artifact.is_symlink() or source.is_symlink() or manifest!=eng["manifest"]
        or required(manifest,"functional_verifier_executed_and_passed","engineering_manifest") is not True
        or hashlib.sha256(source.read_bytes()).hexdigest()!=required(manifest,"main_sha256","engineering_manifest")
        or source.read_bytes()!=DOMAIN_FILES["noaa_water_station_metadata"].read_bytes()):
        raise ValueError("Reviewed engineering artifact disagrees")
    # Separate local reviewer process executes the copied script on actual
    # provider input, never executes unreviewed third-party code.
    if functional_test:
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"station.json"
            path.write_text(intel["8723214"])
            observed=subprocess.run([sys.executable,str(source),str(path)],capture_output=True,text=True,timeout=15,check=True)
            if json.loads(observed.stdout)!=eng["validation"]:
                raise ValueError("Independent actual-input program output disagrees")
    if prior["commercial"]["result"]!=commercial_brief(prior):
        raise ValueError("Commercial brief not bound to public facts")
    return {"verified_public_artifact_scope":True,"verified_producers":4,
            "station_rows":1,"scholarly_metadata_records":len(research["readback"]),
            "independent_actual_input_test":functional_test,"general_autonomy_verified":False,
            "skill_scan_applicable":False,"paid_inference":False}


def mission_worker(role,prior,directory):
    from plenum_ai.chief_contract_plan import run_contract,check_contract_result
    from plenum_ai.reviewed_domain_workers import reuse_original_program
    if role=="intelligence":
        result=run_contract("noaa_metadata",STATIONS,{})
        check_contract_result("noaa_metadata",STATIONS,{},result)
    elif role=="research":
        discovery=run_contract("paper_discovery",PAPERS,{})
        check_contract_result("paper_discovery",PAPERS,{},discovery)
        readback=run_contract("paper_readback",PAPERS,{"paper_discovery":discovery})
        check_contract_result("paper_readback",PAPERS,{"paper_discovery":discovery},readback)
        result={"discovery":discovery,"readback":readback}
    elif role=="engineering":
        intel=prior["intelligence"]["result"]
        validation=run_contract("station_validation",STATIONS,{"noaa_metadata":intel})
        check_contract_result("station_validation",STATIONS,{"noaa_metadata":intel},validation)
        artifact=Path(tempfile.mkdtemp(prefix="engineering-artifact-",dir=directory))
        manifest=reuse_original_program("noaa_water_station_metadata",SPECS[role][1],artifact)
        result={"artifact_dir":artifact.name,"manifest":manifest,"validation":validation}
    elif role=="commercial":
        result=commercial_brief(prior)
    elif role=="verification":
        result=verify(prior,directory,functional_test=True)
    else:
        raise ValueError("Unknown mission division")
    return {"input_sha256":scope_inputs(prior),"result":result}


def minister():
    aid=env_id("PAPERCLIP_AGENT_ID")
    cid=env_id("PAPERCLIP_COMPANY_ID")
    identity=api("/api/agents/me",worker=True)
    task,pid=minister_task(aid,cid)
    if (required(identity,"id","identity")!=aid or required(identity,"companyId","identity")!=cid or required(identity,"name","identity")!="Minister of Operations"
            or task.get("assigneeAgentId")!=aid or task.get("title")!=TITLE
            or task.get("description")!=MISSION or task.get("status") not in ("todo","in_progress")):
        raise PermissionError("Unauthorized Minister mission")
    api("/api/issues/"+pid+"/checkout","POST",{"agentId":aid,"expectedStatuses":["todo","in_progress"]},worker=True)
    roster=api("/api/companies/"+cid+"/agents",worker=True)
    if not isinstance(roster,list) or any(not isinstance(x,dict) for x in roster):
        raise ValueError("Unexpected native roster shape")
    reports=[x for x in roster if x.get("reportsTo")==aid]
    direct={required(x,"name","roster"):str(UUID(required(x,"id","roster"))) for x in reports}
    if len(reports)!=len(SPECS) or set(direct)!={v[0] for v in SPECS.values()}:
        raise ValueError("Unexpected original workforce roster")
    # Only the Minister creates the tasks, through the native company API.
    # Idempotency keys ensure interrupted delegation cannot duplicate children.
    directory=ROOT/cid
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    roles=list(MISSION_ORDER)
    model_receipt=None
    if os.getenv("PLENUM_PAPERCLIP_MODEL")=="local":
        from model_plan import model_plan
        roles,model_receipt=model_plan(directory,cid,pid)
    tasks={}
    for role in roles:
        fields={"title":SPECS[role][1],"description":DESCRIPTION,"status":"todo","priority":"high",
                "parentId":pid,"assigneeAgentId":direct[SPECS[role][0]],
                "idempotencyKey":"plenum-bounded-"+pid+"-"+role}
        if tasks:
            fields["blockedByIssueIds"]=[list(tasks.values())[-1]]
        child=api("/api/companies/"+cid+"/issues","POST",fields,worker=True)
        tasks[role]=str(UUID(required(child,"id","created_child")))
    plan={"company":cid,"minister":aid,"parent":pid,"tasks":tasks,"order":roles}
    if model_receipt is not None:
        plan["model_receipt_sha256"]=digest(model_receipt)
    path=directory/"minister-plan.json"
    if path.exists():
        if json.loads(path.read_text())!=plan:
            raise ValueError("Existing Minister plan differs")
    else:
        exclusive(path,plan)
    api("/api/issues/"+pid,"PATCH",{"status":"done","comment":"Minister dispatched five bounded dependent tasks; final mission acceptance is separate. Plan SHA256: "+digest(plan)},worker=True)
    print(json.dumps({"minister_dispatch":True,"plan_sha256":digest(plan),"tasks":tasks}),flush=True)


def qualify():
    from datetime import datetime, timezone
    started = time.monotonic()
    if api("/api/companies"):
        raise RuntimeError("Expected fresh isolated board")
    cid=str(UUID(required(api("/api/companies","POST",{"name":"Plenum sequential public mission","description":MISSION}),"id","created_company")))
    route="/api/companies/"+cid
    def hire(name,role,arg,parent=None):
        fields={"name":name,"role":role,"runner":"legacy","adapterType":"process",
                "adapterConfig":{"command":"python3","args":["/plenum/integrations/paperclip/sequential_mission.py",arg],
                                 "cwd":"/plenum","timeoutSec":150 if arg=="minister" else 120,"env":{"PYTHONPATH":"/plenum/src","GITHUB_ACTIONS":"true",
                                 "PLENUM_PAPERCLIP_MODEL":os.getenv("PLENUM_PAPERCLIP_MODEL","off"),
                                 "PLENUM_EPHEMERAL_RUNNER":"confirmed"}},
                "budgetMonthlyCents":0,"runtimeConfig":{"heartbeat":{"enabled":False,"wakeOnAssignment":True,"maxConcurrentRuns":1}},
                "permissions":{"canCreateAgents":False,"canCreateSkills":False}}
        if parent: fields["reportsTo"]=parent
        return str(UUID(required(api(route+"/agents","POST",fields),"id","created_agent")))
    leader=hire("Minister of Operations","ceo","minister")
    agents={key:hire(name,"engineer" if key=="engineering" else "general",key,leader) for key,(name,_) in SPECS.items()}
    queued = time.monotonic()
    task=api(route+"/issues","POST",{"title":TITLE,"description":MISSION,"status":"todo","priority":"high","assigneeAgentId":leader})
    parent_id=str(UUID(required(task,"id","created_parent")))
    # No board-side child assignment: wait for the actual Minister's plan and native wakes.
    directory=ROOT/cid
    deadline=time.monotonic()+360
    plan_path=directory/"minister-plan.json"
    while time.monotonic()<deadline:
        # The adapter writes a safe failure receipt before a nonzero exit.
        # Stop early on a definitive failure instead of waiting six minutes.
        if list(ROOT.glob("failure-minister-*.json")) or any(
                list(ROOT.glob("failure-"+role+"-*.json")) for role in MISSION_ORDER):
            raise RuntimeError("Native adapter failure receipt recorded")
        if plan_path.is_file() and required(api("/api/issues/"+parent_id),"status","parent_readback")=="done":
            plan=json.loads(plan_path.read_text())
            if (plan["minister"]!=leader or plan["parent"]!=parent_id or plan["order"]!=list(MISSION_ORDER)
                    or set(plan["tasks"])!=set(MISSION_ORDER)):
                raise ValueError("Minister plan not bound to mission")
            if all(required(api("/api/issues/"+iid),"status","child_readback")=="done" for iid in plan["tasks"].values()):
                break
        time.sleep(3)
    else:
        for key,aid in {"minister":leader,**agents}.items():
            rows=api(route+"/heartbeat-runs?"+urlencode({"agentId":aid,"limit":10}))
            for row in rows[:3]:
                d={k:row.get(k) for k in ("id","status","errorCode","exitCode")}
                try:
                    raw=api("/api/heartbeat-runs/"+row["id"]+"/log?offset=0&limitBytes=16000").get("content","")
                    d["categories"]=[x for x in ("HTTPError","PermissionError","ValueError","RuntimeError","ModuleNotFoundError",
                        "KeyError","FileNotFoundError","Terminal specialist failure","Task assignment") if x in raw]
                except Exception as exc: d["log_error"]=type(exc).__name__
                print(json.dumps({"division":key,"diagnostic":d}),flush=True)
        raise RuntimeError("Native Minister sequential mission did not finish within deadline")
    summary=readback(cid,plan,expected_agents=agents)
    if os.getenv("PLENUM_PAPERCLIP_MODEL")=="local" and summary["minister_model_executed"] is not True:
        raise ValueError("Missing required actual local model receipt")
    exclusive(ROOT/"qualification.json",summary)
    terminal=datetime.now(timezone.utc)
    issue_created=os.environ.get("PLENUM_ISSUE_CREATED_AT","")
    timing={"schema":"plenum-paperclip-event-timing-v1","parent":parent_id,
            "native_assignment_to_verified_seconds":round(time.monotonic()-queued,3),
            "native_qualification_seconds":round(time.monotonic()-started,3),
            "verified_at":terminal.isoformat(),"issue_to_verified_seconds":None,
            "paid_inference":False,"model_executed":summary["minister_model_executed"],
            "verified_divisions":summary["verified_divisions"]}
    if issue_created:
        created=datetime.fromisoformat(issue_created)
        if created.tzinfo is None or created>terminal:raise ValueError("Invalid event timestamp")
        timing["issue_to_verified_seconds"]=round((terminal-created).total_seconds(),3)
    exclusive(ROOT/"event-timing.json",timing)
    print(json.dumps(timing),flush=True)
    print(json.dumps(summary),flush=True)


def readback(cid,plan,expected_agents=None):
    directory=ROOT/cid
    original=api("/api/issues/"+plan["parent"])
    if original.get("status")!="done" or original.get("assigneeAgentId")!=plan["minister"]:
        raise ValueError("Minister dispatch not accepted")
    parent_comments=api("/api/issues/"+plan["parent"]+"/comments")
    if not any("Plan SHA256: "+digest(plan) in c.get("body","") for c in parent_comments):
        raise ValueError("Missing native Minister plan receipt")
    records={}
    previous=None
    for role in MISSION_ORDER:
        iid=plan["tasks"][role]
        task=api("/api/issues/"+iid)
        if (task.get("status")!="done" or task.get("parentId")!=plan["parent"]
                or (expected_agents and task.get("assigneeAgentId")!=expected_agents[role])):
            raise ValueError("Wrong native child scope")
        # Native dependency relations plus actual producer hashes bind order.
        if previous and previous not in (task.get("blockedByIssueIds") or [x.get("id") for x in task.get("blockedBy",[])]):
            # Some detail responses omit relations; check the original native
            # relation endpoint separately when present. Never fake a relation.
            raise ValueError("Native dependency edge not visible")
        previous=iid
        record=read_evidence(cid,role)
        if record["issue"]!=iid or record["result"]["input_sha256"]!=scope_inputs({k:v["result"] for k,v in records.items()}):
            raise ValueError("Invalid task-bound dependency evidence")
        comments=api("/api/issues/"+iid+"/comments")
        if not any("Original public worker evidence SHA256: "+record["sha256"] in c.get("body","") for c in comments):
            raise ValueError("Missing task completion receipt")
        records[role]=record
    result=verify({k:v["result"] for k,v in records.items() if k!="verification"},directory,functional_test=True)
    if result!=records["verification"]["result"]["result"]:
        raise ValueError("Independent verifier disagrees")
    model_executed=False
    model_info={}
    if "model_receipt_sha256" in plan:
        from model_plan import validate_receipt
        receipt=json.loads((directory/"minister-model-plan.json").read_text())
        if digest(receipt)!=plan["model_receipt_sha256"] or validate_receipt(receipt,cid,plan["parent"])!=plan["order"]:
            raise ValueError("Local model delegation receipt mismatch")
        model_executed=True
        model_info={"model":receipt["model"],"model_digest":receipt["model_digest"],
                    "model_receipt_sha256":digest(receipt),"model_eval_count":receipt["eval_count"]}
    return {"company":cid,"minister":plan["minister"],"parent":plan["parent"],"order":list(MISSION_ORDER),
            "verified_divisions":5,"minister_dispatch":True,"minister_model_executed":model_executed,**model_info,"independent_verification":result,
            "paid_inference":False,"persistent_production":False,
            "evidence":{k:{"issue":v["issue"],"sha256":v["sha256"]} for k,v in records.items()}}


def restart_readback():
    old=json.loads((ROOT/"qualification.json").read_text())
    plan=json.loads((ROOT/old["company"]/"minister-plan.json").read_text())
    now=readback(old["company"],plan)
    if now!=old:
        raise ValueError("Restart changed accepted mission receipts")
    print(json.dumps({"container_restart_readback":True,"qualification_sha256":digest(now),"provider_calls_replayed":0}),flush=True)


if __name__=="__main__":
    arg=sys.argv[1] if len(sys.argv)==2 else "invalid"
    if arg not in ("minister","qualify","restart-readback",*MISSION_ORDER):
        raise SystemExit("Unknown bounded entrypoint")
    try:
        if arg=="minister":minister()
        elif arg=="qualify":qualify()
        elif arg=="restart-readback":restart_readback()
        else:run_assigned(arg,mission_worker=mission_worker)
    except Exception as exc:
        failure_receipt(arg,exc)
        raise SystemExit(1) from None
