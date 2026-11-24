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
