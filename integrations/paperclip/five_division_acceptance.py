"""Actual upstream board acceptance: four producer divisions and one dependent reviewer."""
import json
import time
from urllib.parse import urlencode
from acceptance import api
from division_adapter import SPECS, DESCRIPTION, read_evidence, public_worker


def seed():
    if api("/api/companies"):
        raise RuntimeError("Expected fresh isolated integration database")
    cid = api("/api/companies", "POST", {"name": "Plenum five-division acceptance",
        "description": DESCRIPTION})["id"]
    roster = "/api/companies/" + cid + "/agents"
    issues = "/api/companies/" + cid + "/issues"
    def hire(name, title, role, parent=None):
        fields = {"name": name, "role": title, "runner": "legacy", "adapterType": "process",
            "adapterConfig": {"command": "python3", "args": ["/plenum/integrations/paperclip/division_adapter.py", role],
                "cwd": "/plenum", "timeoutSec": 240, "env": {"PYTHONPATH": "/plenum/src"}},
            "budgetMonthlyCents": 0, "runtimeConfig": {"heartbeat": {"enabled": False,
                "wakeOnAssignment": True, "maxConcurrentRuns": 1}},
            "permissions": {"canCreateAgents": False, "canCreateSkills": False}}
        if parent:
            fields["reportsTo"] = parent
        return api(roster, "POST", fields)["id"]
    minister = hire("Minister of Operations", "ceo", "not_active")
    api("/api/agents/" + minister + "/pause", "POST", {})
    agents = {key: hire(name, "engineer" if key == "engineering" else "general", key, minister)
              for key, (name, _) in SPECS.items()}
    tasks = {}
    # Paperclip's own dependency graph controls the reviewer wake. No parallel
    # scheduler or paid provider, and no manual replay of unknown executions.
    for role in SPECS:
        fields = {"title": SPECS[role][1], "description": DESCRIPTION,
            "status": "todo", "priority": "high", "assigneeAgentId": agents[role]}
        if role == "verification":
            fields["blockedByIssueIds"] = list(tasks.values())
        tasks[role] = api(issues, "POST", fields)["id"]
    deadline = time.monotonic() + 330
    while time.monotonic() < deadline:
        states = {key: api("/api/issues/" + iid)["status"] for key, iid in tasks.items()}
        if all(x == "done" for x in states.values()):
            break
        time.sleep(5)
    else:
        for key, aid in agents.items():
            runs = api("/api/companies/" + cid + "/heartbeat-runs?" + urlencode({"agentId": aid, "limit": 10}))
            diagnostics = []
            for row in runs[:3]:
                diagnostic = {k: row.get(k) for k in ("id", "status", "exitCode", "errorCode")}
                try:
                    content = str(api("/api/heartbeat-runs/" + row["id"] +
                        "/log?offset=0&limitBytes=16000").get("content", ""))
                    diagnostic["categories"] = [x for x in ("HTTPError", "ValueError", "KeyError", "PermissionError",
                        "ModuleNotFoundError", "FileNotFoundError", "RuntimeError", "TimeoutError") if x in content]
                except Exception as exc:
                    diagnostic["log_error"] = type(exc).__name__
                diagnostics.append(diagnostic)
            print(json.dumps({"division": key, "status": states[key], "runs": diagnostics}), flush=True)
        raise RuntimeError("Not all native divisions completed")
    evidence = {}
    for role, iid in tasks.items():
        record = read_evidence(cid, role)
        if record["issue"] != iid:
            raise ValueError("Wrong issue identity in artifact")
        comments = api("/api/issues/" + iid + "/comments")
        if not any("Original public worker evidence SHA256: " + record["sha256"] in c.get("body", "")
                   for c in comments):
            raise ValueError("Missing task-bound completion receipt")
        evidence[role] = record
    independent = public_worker("verification", {key: rec["result"] for key, rec in evidence.items()
                                                  if key != "verification"})
    if independent != evidence["verification"]["result"]:
        raise ValueError("Independent reviewer output disagrees")
    if len(api(roster)) != 6:
        raise ValueError("Incorrect workforce roster")
    print(json.dumps({"company": cid, "verified_divisions": len(evidence),
        "native_dependency_review": True, "minister_model_executed": False,
        "persistent_production": False, "paid_inference": False,
        "evidence": {key: {"issue": rec["issue"], "sha256": rec["sha256"]} for key, rec in evidence.items()}}), flush=True)


if __name__ == "__main__":
    seed()
