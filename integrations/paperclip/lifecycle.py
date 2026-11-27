"""Explicit persistent board and UUID-scoped evidence paths. No secret storage."""
from pathlib import Path
from uuid import UUID
import json
import os
from urllib.parse import urlencode

def persistent():
    return os.getenv("PLENUM_PERSISTENT_BOARD")=="confirmed"

def canonical(value):
    if not isinstance(value,str) or str(UUID(value))!=value:raise ValueError("Canonical native UUID required")
    return value

def mission_dir(root, company, mission=None):
    root=Path(root)
    company=canonical(company)
    if not persistent():return root/company
    mission=canonical(mission)
    target=root/company/mission
    if any(p.is_symlink() for p in (root,root/company,target)):raise ValueError("Unsafe persistent evidence path")
    return target

def owner_company(api):
    cid=canonical(os.environ["PLENUM_PAPERCLIP_COMPANY_UUID"])
    if not any(row.get("id")==cid for row in api("/api/companies")):
        raise ValueError("Persistent native company not found")
    return cid

def assigned_scope(api, root, role):
    from mission_scope import validate_scope
    cid=canonical(os.environ["PAPERCLIP_COMPANY_ID"])
    aid=canonical(os.environ["PAPERCLIP_AGENT_ID"])
    hint=os.getenv("PAPERCLIP_TASK_ID")
    rows=[api("/api/issues/"+canonical(hint),worker=True)] if hint else api(
        "/api/companies/"+cid+"/issues?"+urlencode({"assigneeAgentId":aid,"status":"todo,in_progress"}),worker=True)
    candidates=[r for r in rows if r.get("assigneeAgentId")==aid and r.get("status") in ("todo","in_progress")]
    if len(candidates)!=1:raise ValueError("Persistent board requires one active assigned mission")
    row=candidates[0]
    mid=canonical(row["id"] if role=="minister" else row["parentId"])
    binding=json.loads((mission_dir(root,cid,mid)/"mission-scope.json").read_text())
    return validate_scope(binding["scope"])

# The pinned upstream redacts ALL plain env bindings in agent responses.
# A persistent adapter has no stored env at all; its fixed non-secret mode is
# encoded in the exact reviewed entrypoint and role argument, visible on readback.
PERSISTENT_ENTRYPOINT="/plenum/integrations/paperclip/persistent_entrypoint.py"

def persistent_adapter(role):
    if role not in ("minister","intelligence","research","engineering","commercial","verification"):
        raise ValueError("Unknown persistent role")
    # Longer minister budget is restricted to a disposable, explicitly scoped CI board.
    magentic_ci=(os.getenv("GITHUB_ACTIONS")=="true" and os.getenv("PLENUM_CI_MAGENTIC_NATIVE")=="confirmed")
    return {"command":"python3","args":[PERSISTENT_ENTRYPOINT,role],
            "cwd":"/plenum","timeoutSec":(900 if magentic_ci else 150) if role=="minister" else 480 if role=="commercial" else 120,"env":{}}

def validate_roster(rows, company, specs):
    if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):
        raise ValueError("Persistent roster shape mismatch")
    names={"minister":"Minister of Operations",**{k:v[0] for k,v in specs.items()}}
    by_name={r.get("name"):r for r in rows}
    if len(rows)!=6 or set(by_name)!=set(names.values()):
        raise ValueError("Persistent roster must be the existing exact workforce")
    ids={k:canonical(by_name[name]["id"]) for k,name in names.items()}
    if len(set(ids.values()))!=6:raise ValueError("Persistent roster identity collision")
    for role,name in names.items():
        row=by_name[name]
        cfg=row.get("adapterConfig")
        expected=persistent_adapter(role)
        # Missing or empty env are equivalent: there must be no stored binding,
        # redacted or otherwise. Never accept a redacted value as authorization.
        if not isinstance(cfg,dict) or {**cfg,"env":cfg.get("env",{})}!=expected:
            raise ValueError("Persistent roster adapter mismatch: "+role)
        if (row.get("companyId")!=company or row.get("adapterType")!="process"
            or row.get("reportsTo")!=(None if role=="minister" else ids["minister"])
            or row.get("budgetMonthlyCents")!=0):
            raise ValueError("Persistent roster identity or budget mismatch: "+role)
        hb=(row.get("runtimeConfig") or {}).get("heartbeat") or {}
        perms=row.get("permissions") or {}
        if (hb.get("enabled") is not False or hb.get("wakeOnAssignment") is not True
            or hb.get("maxConcurrentRuns")!=1 or perms.get("canCreateAgents") is not False
            or perms.get("canCreateSkills") is not False):
            raise ValueError("Persistent roster execution permissions mismatch: "+role)
    return ids

def bind_roster(root, company, ids):
    from checkpoint_store import exclusive, checked
    directory=Path(root)/canonical(company)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    if directory.is_symlink():raise ValueError("Unsafe persistent company path")
    path=directory/"persistent-roster.json"
    value={"company":company,"agents":ids,"schema":"plenum-persistent-roster-v1"}
    if path.exists() or path.is_symlink():
        if checked(path,value)!=value:raise ValueError("Persistent roster continuity mismatch")
    else:exclusive(path,value)
    return value
