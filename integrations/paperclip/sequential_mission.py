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

from mission_scope import LEGACY, validate_scope, digest as scope_digest, profile_routes
from profile_execution import chief_receipt, division_receipts
from lifecycle import persistent, mission_dir, owner_company, assigned_scope, canonical, persistent_adapter, validate_roster, bind_roster


def active_scope():
    return validate_scope(json.loads(os.getenv("PLENUM_MISSION_SCOPE") or '{"kind":"coastal"}'))


def scope_binding(scope):
    scope=validate_scope(scope)
    tag=scope_digest(scope)
    return {"scope":scope,"scope_sha256":tag,
            "parent_title":TITLE if scope==LEGACY else "Delegate typed public evidence mission",
            "parent_description":MISSION if scope==LEGACY else "Approved typed public evidence scope SHA256: "+tag,
            "child_description":DESCRIPTION if scope==LEGACY else DESCRIPTION+" Scope SHA256: "+tag}


def task_specs(scope):
    if scope==LEGACY:return SPECS
    if scope["kind"]=="station":
        titles={"intelligence":"Retrieve approved public station metadata","research":"Survey approved public scholarly topic",
                "engineering":"Validate public station metadata","commercial":"Prepare evidence-bound coastal screening brief",
                "verification":"Independently verify station evidence"}
    elif scope["kind"] in ("public_dataset","public_objective"):
        titles={"intelligence":"Retrieve approved public DOI metadata","research":"Independently reread public bibliography",
                "engineering":"Execute reviewed generic numerical data analysis","commercial":"Prepare bounded data evidence brief",
                "verification":"Independently verify numerical analysis and bibliography"}
    elif scope["kind"]=="variable_graph":
        titles={"intelligence":"Execute selected public source contracts","research":"Review selected scholarly contracts","engineering":"Execute selected reviewed engineering contracts","commercial":"Assemble selected public evidence contracts","verification":"Independently verify selected native contract graph"}
    else:
        titles={"intelligence":"Retrieve approved public DOI metadata","research":"Read back approved bibliography independently",
                "engineering":"Execute reviewed offline AI budget validator","commercial":"Prepare evidence-bound budget review brief",
                "verification":"Independently verify bibliography and budget evidence"}
    return {role:(SPECS[role][0],titles[role]) for role in SPECS}


def goal_texts(scope):
    from model_plan import GOALS
    if scope==LEGACY:return GOALS
    if scope["kind"]=="station":
        return {**GOALS,"A":"Retrieve public NOAA station metadata for "+", ".join(scope["station_ids"]),
                "D":scope["paper_survey"],"B":"Functionally test reviewed station validator on the requested records"}
    if scope["kind"]=="public_objective":
        from objective_mission import goals
        return goals(scope)
    if scope["kind"]=="public_dataset":
        from dataset_mission import goals
        return goals(scope)
    return {"C":"Draft a commercial decision brief from reviewed budget and bibliography results",
            "E":"Independently verify dependency receipts and test original budget program",
            "A":"Retrieve public metadata for approved DOI identifiers "+", ".join(scope["dois"]),
            "D":"Independently read back scholarly DOI metadata",
            "B":"Execute and functionally test the reviewed offline AI budget validator using approved synthetic counts"}


def station_inputs(scope):
    return (STATIONS,PAPERS) if scope==LEGACY else ({"station_ids":scope["station_ids"]},{"paper_survey":scope["paper_survey"]})



def required(row, key, context):
    if not isinstance(row, dict) or key not in row or row.get(key) is None:
        raise ValueError("Missing required field: " + context + "." + key)
    return row[key]


def env_id(key):
    value = os.getenv(key)
    if not value:
        raise ValueError("Missing required environment: " + key)
    return str(UUID(value))


def minister_task(aid, cid, scope=LEGACY):
    binding=scope_binding(scope)
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
                  and row.get("assigneeAgentId") == aid and row.get("title") == binding["parent_title"]
                  and row.get("description") == binding["parent_description"]
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


def commercial_brief(prior, scope=LEGACY):
    stations,_=station_inputs(scope)
    from plenum_ai.chief_team_mission import _station_rows
    rows = _station_rows(prior["intelligence"]["result"], tuple(stations["station_ids"]))
    engineering = prior["engineering"]["result"]
    papers = prior["research"]["result"]["readback"]
    return {
        "objective":"Assess a bounded coastal monitoring evidence opportunity",
        "facts":{"stations":[{"station_id":row["id"],"station_name":required(row,"name","station"),"coordinates":[row["lat"],row["lng"]]} for row in rows],
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


def verify(prior,directory,*,functional_test=False,scope=LEGACY):
    from plenum_ai.chief_contract_plan import check_contract_result
    from plenum_ai.reviewed_domain_workers import DOMAIN_FILES
    expected=MISSION_ORDER[:-1]
    if set(prior)!=set(expected):
        raise ValueError("Missing original producers")
    for i,role in enumerate(expected):
        value=prior[role]
        if required(value,"input_sha256","producer_receipt")!=scope_inputs({k:prior[k] for k in expected[:i]}):
            raise ValueError("Dependency receipt hash mismatch")
    if scope["kind"]=="variable_graph":
        from native_variable import verify as verify_variable
        return verify_variable(scope,prior,directory,functional_test=functional_test)
    if scope["kind"]=="public_objective":
        from objective_mission import verify as verify_objective
        return verify_objective(scope,prior,directory,functional_test=functional_test)
    if scope["kind"]=="public_dataset":
        from dataset_mission import verify as verify_dataset
        return verify_dataset(scope,prior,directory,functional_test=functional_test)
    if scope["kind"]=="bibliography_budget":
        from budget_mission import verify as verify_budget
        return verify_budget(scope,prior,directory,functional_test=functional_test)
    stations,papers=station_inputs(scope)
    intel=prior["intelligence"]["result"]
    check_contract_result("noaa_metadata",stations,{},intel)
    research=prior["research"]["result"]
    check_contract_result("paper_discovery",papers,{},research["discovery"])
    check_contract_result("paper_readback",papers,{"paper_discovery":research["discovery"]},research["readback"])
    eng=prior["engineering"]["result"]
    check_contract_result("station_validation",stations,{"noaa_metadata":intel},eng["validation"])
    if eng["validation"]["invalid_rows"]!=0 or eng["validation"]["structurally_valid_rows"]!=len(stations["station_ids"]):
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
            from plenum_ai.chief_team_mission import _station_rows
            path.write_text(json.dumps({"stations":_station_rows(intel,tuple(stations["station_ids"]))}))
            observed=subprocess.run([sys.executable,str(source),str(path)],capture_output=True,text=True,timeout=15,check=True)
            if json.loads(observed.stdout)!=eng["validation"]:
                raise ValueError("Independent actual-input program output disagrees")
    if prior["commercial"]["result"]!=commercial_brief(prior,scope):
        raise ValueError("Commercial brief not bound to public facts")
    return {"verified_public_artifact_scope":True,"verified_producers":4,
            "station_rows":len(stations["station_ids"]),"scholarly_metadata_records":len(research["readback"]),
            "independent_actual_input_test":functional_test,"general_autonomy_verified":False,
            "skill_scan_applicable":False,"paid_inference":False}


def original_mission_worker(role,prior,directory,scope=LEGACY):
    if scope["kind"]=="variable_graph":
        from native_variable import run
        result=verify(prior,directory,functional_test=True,scope=scope) if role=="verification" else run(role,scope,prior,directory)
        return {"input_sha256":scope_inputs(prior),"result":result}
    if scope["kind"]=="public_objective":
        from objective_mission import run
        result=verify(prior,directory,functional_test=True,scope=scope) if role=="verification" else run(role,scope,prior,directory)
        return {"input_sha256":scope_inputs(prior),"result":result}
    if scope["kind"]=="public_dataset":
        from dataset_mission import run
        result=verify(prior,directory,functional_test=True,scope=scope) if role=="verification" else run(role,scope,prior,directory)
        return {"input_sha256":scope_inputs(prior),"result":result}
    if scope["kind"]=="bibliography_budget":
        from budget_mission import run
        result=verify(prior,directory,functional_test=True,scope=scope) if role=="verification" else run(role,scope,prior,directory)
        return {"input_sha256":scope_inputs(prior),"result":result}
    stations,papers=station_inputs(scope)
    from plenum_ai.chief_contract_plan import run_contract,check_contract_result
    from plenum_ai.reviewed_domain_workers import reuse_original_program
    if role=="intelligence":
        result=run_contract("noaa_metadata",stations,{})
        check_contract_result("noaa_metadata",stations,{},result)
    elif role=="research":
        discovery=run_contract("paper_discovery",papers,{})
        check_contract_result("paper_discovery",papers,{},discovery)
        readback=run_contract("paper_readback",papers,{"paper_discovery":discovery})
        check_contract_result("paper_readback",papers,{"paper_discovery":discovery},readback)
        result={"discovery":discovery,"readback":readback}
    elif role=="engineering":
        intel=prior["intelligence"]["result"]
        validation=run_contract("station_validation",stations,{"noaa_metadata":intel})
        check_contract_result("station_validation",stations,{"noaa_metadata":intel},validation)
        artifact=Path(tempfile.mkdtemp(prefix="engineering-artifact-",dir=directory))
        manifest=reuse_original_program("noaa_water_station_metadata",SPECS[role][1],artifact)
        result={"artifact_dir":artifact.name,"manifest":manifest,"validation":validation}
    elif role=="commercial":
        result=commercial_brief(prior,scope)
    elif role=="verification":
        result=verify(prior,directory,functional_test=True,scope=scope)
    else:
        raise ValueError("Unknown mission division")
    return {"input_sha256":scope_inputs(prior),"result":result}


def mission_worker(role,prior,directory,scope=LEGACY):
    value=original_mission_worker(role,prior,directory,scope)
    value["profile_receipts"]=division_receipts(role,scope,prior,value["result"],directory)
    return value


def minister():
    if persistent():
        from objective_replan import maybe_minister_replan
        if maybe_minister_replan(api,ROOT):return
    scope=assigned_scope(api,ROOT,"minister") if persistent() else active_scope()
    binding=scope_binding(scope)
    specs=task_specs(scope)
    aid=env_id("PAPERCLIP_AGENT_ID")
    cid=env_id("PAPERCLIP_COMPANY_ID")
    identity=api("/api/agents/me",worker=True)
    task,pid=minister_task(aid,cid,scope)
    if (required(identity,"id","identity")!=aid or required(identity,"companyId","identity")!=cid or required(identity,"name","identity")!="Minister of Operations"
            or task.get("assigneeAgentId")!=aid or task.get("title")!=binding["parent_title"]
            or task.get("description")!=binding["parent_description"] or task.get("status") not in ("todo","in_progress")):
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
    directory=mission_dir(ROOT,cid,pid)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    if (persistent() or scope!=LEGACY) and json.loads((directory/"mission-scope.json").read_text())!=binding:
        raise ValueError("Minister typed scope mismatch")
    roles=list(MISSION_ORDER)
    model_receipt=None
    if persistent():
        from production_wiring import load_prepared
        model_mode=load_prepared(directory,cid,pid)["model_mode"]
    else:model_mode=os.getenv("PLENUM_PAPERCLIP_MODEL","off")
    variable_plan=None
    if scope["kind"]=="variable_graph":
        if not persistent() or model_mode!="local":raise PermissionError("Variable graph requires persistent local model")
        from native_variable import prepare
        variable_plan=prepare(directory,scope,cid,pid)
    elif model_mode=="local":
        from model_plan import model_plan
        from objective_mission import planning_kwargs
        roles,model_receipt=model_plan(directory,cid,pid,goals=goal_texts(scope),**planning_kwargs(scope))
    synthesis_receipt=None
    from synthesis_contract import is_synthesis
    if is_synthesis(scope):
        from synthesis_contract import plan as synthesis_plan
        synthesis_receipt=synthesis_plan(directory,scope,cid,pid)
    composition_receipt=None
    from composition_contract import is_composition
    if is_composition(scope):
        from composition_contract import plan as composition_plan
        composition_receipt=composition_plan(directory,scope,cid,pid)
    tasks={}
    for role in roles:
        fields={"title":specs[role][1],"description":binding["child_description"],"status":"todo","priority":"high",
                "parentId":pid,"assigneeAgentId":direct[SPECS[role][0]],
                "idempotencyKey":"plenum-bounded-"+pid+"-"+role}
        if tasks:
            fields["blockedByIssueIds"]=[list(tasks.values())[-1]]
        child=api("/api/companies/"+cid+"/issues","POST",fields,worker=True)
        tasks[role]=str(UUID(required(child,"id","created_child")))
    plan={"company":cid,"minister":aid,"parent":pid,"tasks":tasks,"order":roles}
    if scope!=LEGACY:plan["scope_sha256"]=binding["scope_sha256"]
    if model_receipt is not None:
        plan["model_receipt_sha256"]=digest(model_receipt)
    if variable_plan is not None:
        plan["variable_graph_sha256"]=digest(variable_plan)
    if composition_receipt is not None:
        plan["composition_plan_sha256"]=digest(composition_receipt)
    if synthesis_receipt is not None:
        plan["synthesis_plan_sha256"]=digest(synthesis_receipt)
    path=directory/"minister-plan.json"
    if path.exists():
        if json.loads(path.read_text())!=plan:
            raise ValueError("Existing Minister plan differs")
    else:
        exclusive(path,plan)
    chief=chief_receipt(scope,plan)
    chief_path=directory/"chief-profile.json"
    if chief_path.exists():
        if json.loads(chief_path.read_text())!=chief:raise ValueError("Chief receipt changed")
    else:exclusive(chief_path,chief)
    api("/api/issues/"+pid,"PATCH",{"status":"done","comment":"Minister dispatched five bounded dependent tasks; final mission acceptance is separate. Plan SHA256: "+digest(plan)},worker=True)
    print(json.dumps({"minister_dispatch":True,"plan_sha256":digest(plan),"tasks":tasks}),flush=True)


def retry_unstarted_verifier(api,directory,cid,mid,plan,agents,scope,*,target="verification"):
    """Reuse pinned Paperclip's native idempotent task retry, never a new task.
    Disposable CI only; absence of a local receipt alone is not proof of no work.
    """
    if target not in MISSION_ORDER or (target!="verification" and scope.get("kind")!="variable_graph"):
        return False
    if os.getenv("GITHUB_ACTIONS")!="true" or os.getenv("PLENUM_EPHEMERAL_RUNNER")!="confirmed":
        return False
    from checkpoint_store import checked
    from production_wiring import load_prepared
    if load_prepared(directory,cid,mid)["checkpoint_mode"]!="local":return False
    marker=directory/(target+"-setup-retry.json")
    if marker.exists() or marker.is_symlink():return False
    if any((directory/n).exists() or (directory/n).is_symlink() for n in
           (target+".json",target+".attempt-1",target+".attempt-2","qualification.json")):
        return False
    if plan!=checked(directory/"minister-plan.json",{"company":cid,"parent":mid,
                    "scope_sha256":scope_digest(scope),"order":list(MISSION_ORDER)}):
        raise ValueError("Changed specialist recovery plan")
    prior={}
    for role in MISSION_ORDER[:MISSION_ORDER.index(target)]:
        iid=canonical(plan["tasks"][role])
        task=api("/api/issues/"+iid)
        if (task.get("id")!=iid or task.get("companyId")!=cid or task.get("parentId")!=mid
                or task.get("assigneeAgentId")!=agents[role] or task.get("status")!="done"):
            return False
        row=checked(directory/(role+".json"),{"company":cid,"issue":iid,"role":role})
        if row["sha256"]!=digest(row["result"]) or row["result"]["input_sha256"]!=scope_inputs(prior):
            raise ValueError("Changed prerequisite evidence")
        prior[role]=row["result"]
    if scope.get("kind")=="variable_graph" and target!="verification":
        import native_variable as nv
        graph=nv.load(directory,scope,cid,mid)
        root=nv.evidence_root(directory)
        for contract in nv.partition(graph)[target]:
            for suffix in (".reserved.json",".result.json"):
                evidence=root/(contract+suffix)
                if evidence.exists() or evidence.is_symlink():return False
    iid=canonical(plan["tasks"][target])
    aid=canonical(agents[target])
    task=api("/api/issues/"+iid)
    if (task.get("id")!=iid or task.get("companyId")!=cid or task.get("parentId")!=mid
            or task.get("assigneeAgentId")!=aid or task.get("status") not in ("todo","in_progress")):
        return False
    observed=(task.get("interruption") or {}).get("observedRunId")
    if not observed:return False
    runid=canonical(observed)
    run=api("/api/heartbeat-runs/"+runid)
    context=run.get("contextSnapshot") or {}
    execution=(run.get("resultJson") or {}).get("executionRecovery") or {}
    if (run.get("id")!=runid or run.get("companyId")!=cid or run.get("agentId")!=aid
            or context.get("issueId")!=iid or run.get("status")!="failed"
            or run.get("errorCode")!="setup_failed" or run.get("exitCode") is not None
            or not run.get("finishedAt") or execution.get("kind")!="bootstrap"
            or execution.get("providerWorkStarted") is not False):
        return False
    # Upstream checks that observedRunId is still latest under its issue lock.
    # One reserved request only. Lost response remains unresolved; never replay.
    key=str(uuid4())
    exclusive(marker,{"schema":("plenum-verifier-setup-retry-v1" if target=="verification" else "plenum-specialist-setup-retry-v1"),"company":cid,"mission":mid,
        "issue":iid,"run":runid,"idempotency_key":key,"prior_sha256":digest(prior),
        "provider_work_started":False,"paid_inference":False})
    reply=api("/api/issues/"+iid+"/retry","POST",{"observedRunId":runid,"idempotencyKey":key})
    if reply.get("accepted") is not True or reply.get("stale") is not False:
        raise RuntimeError("Native setup retry not accepted; no further dispatch")
    exclusive(directory/(target+"-setup-retry-accepted.json"),{"company":cid,"mission":mid,
        "issue":iid,"request":canonical(reply["requestId"]),"run":runid,"paid_inference":False})
    return True


def qualify(action="qualify"):
    from production_wiring import company_lock
    if persistent():
        with company_lock(ROOT,owner_company(api)):
            return qualify_locked(action)
    if action!="qualify":raise ValueError("Staged mission requires persistent board")
    return qualify_locked(action)


def qualify_locked(action):
    from datetime import datetime, timezone
    started = time.monotonic()
    durable=persistent()
    if action in ("activate","resume"):
        from production_wiring import load_prepared
        cid=owner_company(api)
        mid=canonical(os.environ["PLENUM_PAPERCLIP_MISSION_UUID"])
        directory=mission_dir(ROOT,cid,mid)
        scope=validate_scope(json.loads((directory/"mission-scope.json").read_text())["scope"])
        if load_prepared(directory,cid,mid)["scope_sha256"]!=scope_digest(scope):raise ValueError("Prepared scope mismatch")
    else:scope=active_scope()
    binding=scope_binding(scope)
    specs=task_specs(scope)
    if scope["kind"] in ("public_objective","variable_graph"):
        from production_wiring import load_prepared
        if not durable or (load_prepared(directory,cid,mid)["model_mode"] if action in ("activate","resume") else os.getenv("PLENUM_PAPERCLIP_MODEL","off"))!="local":
            raise PermissionError("Objective scope requires persistent local model approval")
    if durable:
        cid=owner_company(api)
        if os.getenv("PLENUM_PAPERCLIP_MODEL","off") not in ("off","local"):
            raise ValueError("Unsupported persistent model mode")
    else:
        if api("/api/companies"):raise RuntimeError("Expected fresh isolated board")
        cid=str(UUID(required(api("/api/companies","POST",{"name":"Plenum sequential public mission","description":MISSION}),"id","created_company")))
        directory=mission_dir(ROOT,cid)
        directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        exclusive(directory/"mission-scope.json",binding)
        exclusive(directory/"profile-routing.json",profile_routes(scope))
    route="/api/companies/"+cid
    before_failures=set(ROOT.glob("failure-*.json"))
    def hire(name,role,arg,parent=None):
        fields={"name":name,"role":role,"runner":"legacy","adapterType":"process",
                "adapterConfig":{"command":"python3","args":["/plenum/integrations/paperclip/sequential_mission.py",arg],
                                 "cwd":"/plenum","timeoutSec":150 if arg=="minister" else 480 if arg=="commercial" else 120,"env":{"PYTHONPATH":"/plenum/src","GITHUB_ACTIONS":"true",
                                 "PLENUM_PAPERCLIP_MODEL":os.getenv("PLENUM_PAPERCLIP_MODEL","off"),
                                 "PLENUM_EPHEMERAL_RUNNER":"confirmed","PLENUM_MISSION_SCOPE":encoded(scope).decode()}},
                "budgetMonthlyCents":0,"runtimeConfig":{"heartbeat":{"enabled":False,"wakeOnAssignment":True,"maxConcurrentRuns":1}},
                "permissions":{"canCreateAgents":False,"canCreateSkills":False}}
        if durable:
            fields["adapterConfig"]=persistent_adapter(arg)
        if parent: fields["reportsTo"]=parent
        return str(UUID(required(api(route+"/agents","POST",fields),"id","created_agent")))
    roster=api(route+"/agents") if durable else []
    if roster:
        ids=validate_roster(roster,cid,specs)
        # Existing boards must already have the immutable original roster proof.
        if not (ROOT/cid/"persistent-roster.json").is_file():
            raise ValueError("Existing persistent roster has no original continuity receipt")
        bind_roster(ROOT,cid,ids)
        leader=ids["minister"]
        agents={k:ids[k] for k in specs}
    else:
        if action in ("activate","resume"):raise ValueError("Prepared roster absent")
        leader=hire("Minister of Operations","ceo","minister")
        agents={key:hire(name,"engineer" if key=="engineering" else "general",key,leader) for key,(name,_) in specs.items()}
        if durable:
            ids=validate_roster(api(route+"/agents"),cid,specs)
            if ids!={"minister":leader,**agents}:raise ValueError("Created roster identity mismatch")
            bind_roster(ROOT,cid,ids)
    from production_wiring import prepared, authorize_activation
    queued = time.monotonic()
    if action in ("activate","resume"):
        parent_id=mid
        if action=="activate":
            authorize_activation(api,directory,cid,parent_id,leader,binding)
        else:
            from supervisor_resume import validate_resume
            validate_resume(api,directory,cid,parent_id,leader,binding)
            old=directory/"qualification.json"
            if old.exists() or old.is_symlink():
                from checkpoint_store import checked
                accepted=checked(old,{"company":cid,"parent":parent_id,"scope_sha256":binding["scope_sha256"],"paid_inference":False})
                plan=checked(directory/"minister-plan.json",{"company":cid,"parent":parent_id,"minister":leader})
                if readback(cid,plan,expected_agents=agents)!=accepted:raise ValueError("Accepted native mission changed")
                from supervisor_resume import finalize
                finalize(directory,accepted,started,queued,resuming=True)
                print(json.dumps(accepted),flush=True)
                return accepted
    else:
        fields={"title":binding["parent_title"],"description":binding["parent_description"],"status":"todo","priority":"high"}
        if not durable:fields["assigneeAgentId"]=leader
        if durable:
            existing=api(route+"/issues")
            if any(r.get("status") in ("todo","in_progress","blocked","backlog","in_review") for r in existing):
                raise ValueError("Previous mission must be terminal before another submission")
            mode=os.getenv("PLENUM_PERSISTENT_CHECKPOINT_MODE","local")
            if mode not in ("local","remote") or (action=="qualify" and mode!="local"):
                raise ValueError("Remote checkpoint requires staged prepare and activate")
        task=api(route+"/issues","POST",fields)
        parent_id=str(UUID(required(task,"id","created_parent")))
        directory=mission_dir(ROOT,cid,parent_id)
        if durable:
            directory.mkdir(parents=True,exist_ok=False,mode=0o700)
            exclusive(directory/"mission-scope.json",binding)
            exclusive(directory/"profile-routing.json",profile_routes(scope))
            row=prepared(directory,cid,parent_id,binding["scope_sha256"],mode,os.getenv("PLENUM_PAPERCLIP_MODEL","off"))
            if os.getenv("PLENUM_CI_TRANSIENT_INTELLIGENCE")=="confirmed":
                if os.getenv("GITHUB_ACTIONS")!="true" or action!="prepare" or mode!="local":raise PermissionError("CI fault injection requires isolated staged local checkpoints")
                exclusive(directory/"ci-transient-intelligence.json",{"company":cid,"mission":parent_id,"role":"intelligence"})
            if os.getenv("PLENUM_CI_REPLAN_ENGINEERING")=="confirmed":
                if os.getenv("GITHUB_ACTIONS")!="true" or action!="prepare" or mode!="local" or scope["kind"]!="public_objective":raise PermissionError("CI-only objective replan fault")
                exclusive(directory/"ci-replan-engineering.json",{"company":cid,"mission":parent_id,"role":"engineering"})
            if action=="prepare":
                print(json.dumps(row),flush=True)
                return row
            authorize_activation(api,directory,cid,parent_id,leader,binding)
    from supervisor_resume import interrupt_ci
    interrupt_ci("PLENUM_CI_INTERRUPT_SUPERVISOR",durable,action,directory,73,api=api)
    # No board-side child assignment: wait for actual Minister and native wakes.
    # Native graph work shares CPU inference with the prior verified adaptive
    # turns; keep a bounded mission deadline long enough for the worker cap.
    graph_scope=scope.get("inputs",{}).get("synthesis",{}).get("followup",{}).get("engine")=="deepagents"
    deadline=time.monotonic()+(720 if graph_scope else 360)
    plan_path=directory/"minister-plan.json"
    while time.monotonic()<deadline:
        # The adapter writes a safe failure receipt before a nonzero exit.
        # Stop early on a definitive failure instead of waiting six minutes.
        if set(ROOT.glob("failure-*.json"))-before_failures:
            raise RuntimeError("Native adapter failure receipt recorded")
        if plan_path.is_file() and required(api("/api/issues/"+parent_id),"status","parent_readback")=="done":
            plan=json.loads(plan_path.read_text())
            if (plan["minister"]!=leader or plan["parent"]!=parent_id or plan["order"]!=list(MISSION_ORDER)
                    or set(plan["tasks"])!=set(MISSION_ORDER)):
                raise ValueError("Minister plan not bound to mission")
            if all(required(api("/api/issues/"+iid),"status","child_readback")=="done" for iid in plan["tasks"].values()):
                break
            if durable and scope.get("kind")!="coastal":
                # Only the first unfinished dependency can be eligible.
                target="verification"
                if scope.get("kind")=="variable_graph":
                    target=next((role for role in MISSION_ORDER
                        if required(api("/api/issues/"+plan["tasks"][role]),"status","child_readback")!="done"),"verification")
                if retry_unstarted_verifier(api,directory,cid,parent_id,plan,agents,scope,target=target):
                    deadline=max(deadline,time.monotonic()+150)
        time.sleep(3)
    else:
        diagnostics=[]
        for key,aid in {"minister":leader,**agents}.items():
            rows=api(route+"/heartbeat-runs?"+urlencode({"agentId":aid,"limit":10}))
            for row in rows[:3]:
                d={k:row.get(k) for k in ("id","status","errorCode","exitCode")}
                try:
                    raw=api("/api/heartbeat-runs/"+row["id"]+"/log?offset=0&limitBytes=16000").get("content","")
                    d["categories"]=[x for x in ("HTTPError","PermissionError","ValueError","RuntimeError","ModuleNotFoundError",
                        "KeyError","FileNotFoundError","Terminal specialist failure","Task assignment") if x in raw]
                except Exception as exc: d["log_error"]=type(exc).__name__
                diagnostic={"division":key,"diagnostic":d}
                diagnostics.append(diagnostic)
                print(json.dumps(diagnostic),flush=True)
        # Keep an evidence-bound handoff for the next supervisor/operator.
        # This is diagnostic only: never wake, reassign, or replay a task here.
        from failure_handoff import publish
        publish(directory,cid,parent_id,scope_digest(scope),diagnostics)
        raise RuntimeError("Native Minister sequential mission did not finish within deadline")
    summary=readback(cid,plan,expected_agents=agents)
    required_model=__import__("production_wiring").load_prepared(directory,cid,parent_id)["model_mode"] if durable else os.getenv("PLENUM_PAPERCLIP_MODEL","off")
    if required_model=="local" and summary["minister_model_executed"] is not True:
        raise ValueError("Missing required actual local model receipt")
    evidence_root=directory if durable else ROOT
    from supervisor_resume import finalize
    timing=finalize(evidence_root,summary,started,queued,resuming=action=="resume",directory=directory if durable else None)
    print(json.dumps(timing),flush=True)
    print(json.dumps(summary),flush=True)
    return summary


def readback(cid,plan,expected_agents=None):
    directory=mission_dir(ROOT,cid,plan["parent"])
    binding=json.loads((directory/"mission-scope.json").read_text())
    scope=validate_scope(binding["scope"])
    if binding!=scope_binding(scope) or (scope!=LEGACY and plan.get("scope_sha256")!=binding["scope_sha256"]):
        raise ValueError("Readback scope mismatch")
    profiles=json.loads((directory/"profile-routing.json").read_text())
    if profiles!=profile_routes(scope):raise ValueError("Profile routing evidence mismatch")
    specs=task_specs(scope)
    persistent_ids=None
    if persistent():
        persistent_ids=validate_roster(api("/api/companies/"+cid+"/agents"),cid,specs)
        if not (ROOT/cid/"persistent-roster.json").is_file():
            raise ValueError("Missing original persistent roster receipt")
        bind_roster(ROOT,cid,persistent_ids)
        if persistent_ids["minister"]!=plan["minister"]:raise ValueError("Persistent Minister identity mismatch")
        actual={k:persistent_ids[k] for k in specs}
        if expected_agents is not None and expected_agents!=actual:raise ValueError("Persistent assignment roster mismatch")
        expected_agents=actual
    original=api("/api/issues/"+plan["parent"])
    if original.get("status")!="done" or original.get("assigneeAgentId")!=plan["minister"] or original.get("title")!=binding["parent_title"] or original.get("description")!=binding["parent_description"]:
        raise ValueError("Minister dispatch not accepted")
    parent_comments=api("/api/issues/"+plan["parent"]+"/comments")
    if not any("Plan SHA256: "+digest(plan) in c.get("body","") for c in parent_comments):
        raise ValueError("Missing native Minister plan receipt")
    records={}
    recoveries={}
    replans={}
    previous=None
    for role in MISSION_ORDER:
        iid=plan["tasks"][role]
        task=api("/api/issues/"+iid)
        if (task.get("status")!="done" or task.get("parentId")!=plan["parent"]
                or task.get("title")!=specs[role][1] or task.get("description")!=binding["child_description"]
                or (expected_agents and task.get("assigneeAgentId")!=expected_agents[role])):
            raise ValueError("Wrong native child scope")
        # Native dependency relations plus actual producer hashes bind order.
        if previous and previous not in (task.get("blockedByIssueIds") or [x.get("id") for x in task.get("blockedBy",[])]):
            # Some detail responses omit relations; check the original native
            # relation endpoint separately when present. Never fake a relation.
            raise ValueError("Native dependency edge not visible")
        previous=iid
        record=read_evidence(cid,role,plan["parent"])
        if record["issue"]!=iid or record["result"]["input_sha256"]!=scope_inputs({k:v["result"] for k,v in records.items()}):
            raise ValueError("Invalid task-bound dependency evidence")
        comments=api("/api/issues/"+iid+"/comments")
        if not any("Original public worker evidence SHA256: "+record["sha256"] in c.get("body","") for c in comments):
            raise ValueError("Missing task completion receipt")
        expected_profiles=division_receipts(role,scope,{k:v["result"] for k,v in records.items()},
                                            record["result"]["result"],directory)
        if record["result"].get("profile_receipts")!=expected_profiles:
            raise ValueError("Profile work-product receipt mismatch")
        from objective_replan import verify_completed_replan
        replan=verify_completed_replan(api,directory,cid,plan,role,record,scope)
        if replan is not None:replans[role]=digest(replan)
        else:
            from recovery_audit import verify as verify_recovery
            recovery=verify_recovery(directory,cid,role,iid,record["sha256"])
            if recovery is not None:recoveries[role]=digest(recovery)
        records[role]=record
    chief=json.loads((directory/"chief-profile.json").read_text())
    if chief!=chief_receipt(scope,plan):raise ValueError("Chief receipt mismatch")
    executed={"chief":digest(chief)}
    for row in records.values():
        for name,profile in row["result"]["profile_receipts"].items():
            if name in executed:raise ValueError("Duplicate profile execution")
            executed[name]=digest(profile)
    if len(executed)!=11:raise ValueError("Missing profile execution")
    result=verify({k:v["result"] for k,v in records.items() if k!="verification"},directory,functional_test=True,scope=scope)
    if result!=records["verification"]["result"]["result"]:
        raise ValueError("Independent verifier disagrees")
    model_executed=False
    model_info={}
    if scope["kind"]=="variable_graph":
        from native_variable import load,evidence_root
        from checkpoint_store import checked
        from model_plan import MODEL
        variable_plan=load(directory,scope,cid,plan["parent"])
        receipt=checked(evidence_root(directory)/"model-response.json",{})
        model_executed=True
        model_info={"model":MODEL,"model_digest":variable_plan["model_digest"],"model_receipt_sha256":digest(receipt),"model_eval_count":receipt["eval_count"]}
    elif "model_receipt_sha256" in plan:
        from model_plan import validate_receipt
        receipt=json.loads((directory/"minister-model-plan.json").read_text())
        from objective_mission import planning_kwargs
        if digest(receipt)!=plan["model_receipt_sha256"] or validate_receipt(receipt,cid,plan["parent"],goals=goal_texts(scope),**planning_kwargs(scope))!=plan["order"]:
            raise ValueError("Local model delegation receipt mismatch")
        model_executed=True
        model_info={"model":receipt["model"],"model_digest":receipt["model_digest"],
                    "model_receipt_sha256":digest(receipt),"model_eval_count":receipt["eval_count"]}
    if persistent():
        from production_wiring import load_prepared
        if model_executed!=(load_prepared(directory,cid,plan["parent"])["model_mode"]=="local"):
            raise ValueError("Persistent model receipt does not match prepared mode")
    return {"company":cid,"minister":plan["minister"],"parent":plan["parent"],"order":list(MISSION_ORDER),
            "verified_divisions":5,"minister_dispatch":True,**({"persistent_roster":persistent_ids} if persistent_ids is not None else {}),"minister_model_executed":model_executed,**model_info,"independent_verification":result,
            "paid_inference":False,"persistent_production":False,"scope_sha256":binding["scope_sha256"],
            "mission_kind":scope["kind"],"routed_profiles":len(profiles),"profile_worker_execution_claimed":False,"verified_profile_work_products":len(executed),"profile_receipt_sha256":executed,
            **({"recovery_receipt_sha256":recoveries} if recoveries else {}),
            **({"replan_receipt_sha256":replans} if replans else {}),
            "evidence":{k:{"issue":v["issue"],"sha256":v["sha256"]} for k,v in records.items()}}


def restart_readback():
    evidence_root=mission_dir(ROOT,owner_company(api),canonical(os.environ["PLENUM_PAPERCLIP_MISSION_UUID"])) if persistent() else ROOT
    old=json.loads((evidence_root/"qualification.json").read_text())
    plan=json.loads((mission_dir(ROOT,old["company"],old["parent"])/"minister-plan.json").read_text())
    now=readback(old["company"],plan)
    if now!=old:
        raise ValueError("Restart changed accepted mission receipts")
    from datetime import datetime, timezone
    timing=json.loads((evidence_root/"event-timing.json").read_text())
    if timing["parent"]!=now["parent"] or timing["qualification_sha256"]!=digest(now):
        raise ValueError("Timing receipt does not match accepted mission")
    restarted=datetime.now(timezone.utc)
    proof={"container_restart_readback":True,"qualification_sha256":digest(now),"provider_calls_replayed":0,
           "restart_verified_at":restarted.isoformat(),"issue_to_restart_verified_seconds":None}
    if timing["issue_created_at"]:
        proof["issue_to_restart_verified_seconds"]=round((restarted-datetime.fromisoformat(timing["issue_created_at"])).total_seconds(),3)
    target=evidence_root/"restart-timing.json"
    if target.exists():
        prior=json.loads(target.read_text())
        if prior["qualification_sha256"]!=proof["qualification_sha256"]:raise ValueError("Restart receipt mismatch")
    else:exclusive(target,proof)
    print(json.dumps(proof),flush=True)


if __name__=="__main__":
    arg=sys.argv[1] if len(sys.argv)==2 else "invalid"
    if arg not in ("minister","qualify","prepare","activate","resume","restart-readback","verify-live","preflight-live","queue-run",*MISSION_ORDER):
        raise SystemExit("Unknown bounded entrypoint")
    try:
        if arg=="minister":minister()
        elif arg in ("qualify","prepare","activate","resume"):qualify(arg)
        elif arg=="restart-readback":restart_readback()
        elif arg=="preflight-live":
            from live_preflight import preflight_live
            preflight_live(api,ROOT)
        elif arg=="verify-live":
            from live_verify import verify_live
            verify_live(api,ROOT,readback)
        elif arg=="queue-run":
            from mission_queue import queue_run
            queue_run(api,ROOT,qualify_locked,readback)
        else:
            scope=assigned_scope(api,ROOT,arg) if persistent() else active_scope()
            run_assigned(arg,mission_worker=lambda role,prior,directory:mission_worker(role,prior,directory,scope),
                         specs=task_specs(scope),description=scope_binding(scope)["child_description"],expected_scope=scope)
    except Exception as exc:
        failure_receipt(arg,exc)
        raise SystemExit(1) from None
