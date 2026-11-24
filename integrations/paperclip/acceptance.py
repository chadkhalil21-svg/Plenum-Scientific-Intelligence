"""Adopt upstream Paperclip as the board, reusing existing Plenum worker code.

Disposable integration only: no public listener, provider keys, private data,
external account writes or second production queue. Existing #432 remains
authoritative until a durable owner-controlled instance passes acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit, urlencode

COMPANY = "Plenum public integration"
TASK = "Validate existing NOAA station metadata program"
DESCRIPTION = "Public integration acceptance of the original reviewed validator; not a new engineering mission."


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def api(path, method="GET", body=None, *, worker=False):
    base = os.environ.get("PAPERCLIP_API_URL", "http://127.0.0.1:3100").rstrip("/")
    url = urlsplit(base)
    if url.scheme != "http" or url.hostname not in ("localhost", "127.0.0.1") or url.port != 3100 or url.path or url.query or url.fragment or url.username:
        raise ValueError("Only isolated loopback Paperclip accepted")
    headers = {"Content-Type": "application/json"}
    if worker:
        headers["Authorization"] = "Bearer " + os.environ["PAPERCLIP_API_KEY"]
        headers["X-Paperclip-Run-Id"] = os.environ["PAPERCLIP_RUN_ID"]
    with build_opener(NoRedirect).open(Request(base + path, headers=headers,
                method=method, data=None if body is None else json.dumps(body).encode()), timeout=15) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("Unexpected Paperclip response size")
    return json.loads(raw)


def run_worker():
    from plenum_ai.workforce_team_dispatch import dispatch
    agent = os.environ["PAPERCLIP_AGENT_ID"]
    company = os.environ["PAPERCLIP_COMPANY_ID"]
    rows = api("/api/companies/" + company + "/issues?" + urlencode(
        {"assigneeAgentId": agent, "status": "todo"}), worker=True)
    matching = [r for r in rows if r.get("title") == TASK and r.get("description") == DESCRIPTION
                and r.get("assigneeAgentId") == agent]
    if not matching:
        return
    if len(matching) != 1:
        raise ValueError("Ambiguous integration task")
    issue = matching[0]["id"]
    path = "/api/issues/" + issue
    api(path + "/checkout", "POST", {"agentId": agent, "expectedStatuses": ["todo"]}, worker=True)
    with tempfile.TemporaryDirectory() as folder:
        result = dispatch({"kind": "public_program", "issue_number": 1,
            "objective": "create a NOAA station metadata validator program"}, Path(folder))
        if not result["verified"] or not result["actual_offline_functional_test_passed"]:
            raise RuntimeError("Existing worker acceptance failed")
        proof = json.loads((Path(folder) / result["output_artifact"] / "code" / "manifest.json").read_text())
        if proof["functional_verifier_executed_and_passed"] is not True:
            raise RuntimeError("Missing actual functional execution")
        note = "Original reviewed validator executed and passed. Source SHA256: " + proof["main_sha256"]
        api(path, "PATCH", {"status": "done", "comment": note}, worker=True)
        print(note)


def seed():
    # This is intentionally an isolated new integration database, not another
    # live production company. Do not duplicate a prior seeded board.
    if api("/api/companies"):
        raise RuntimeError("Expected empty integration database")
    company = api("/api/companies", "POST", {"name": COMPANY, "description": DESCRIPTION})
    cid = company["id"]
    roster = "/api/companies/" + cid + "/agents"
    command = {"command": "python3", "args": ["/plenum/integrations/paperclip/acceptance.py", "--worker"],
               "cwd": "/plenum", "timeoutSec": 180, "env": {"PYTHONPATH": "/plenum/src"}}
    def hire(name, role, parent=None):
        fields = {"name": name, "role": role, "adapterType": "process",
                  "adapterConfig": command, "budgetMonthlyCents": 0,
                  "permissions": {"canCreateAgents": False, "canCreateSkills": False}}
        if parent:
            fields["reportsTo"] = parent
        return api(roster, "POST", fields)["id"]
    minister = hire("Minister of Operations", "ceo")
    # Only Engineering is exercised by this acceptance; the other four
    # divisions and Minister are paused until distinct adapters are verified.
    api("/api/agents/" + minister + "/pause", "POST", {})
    for name in ("Scientific Research", "Commercial Operations", "Global Intelligence", "Verification and Advisory"):
        aid = hire(name, "general", minister)
        api("/api/agents/" + aid + "/pause", "POST", {})
    engineer = hire("Engineering and Manufacturing", "engineer", minister)
    issue = api("/api/companies/" + cid + "/issues", "POST", {
        "title": TASK, "description": DESCRIPTION, "status": "todo",
        "priority": "high", "assigneeAgentId": engineer})
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        result = api("/api/issues/" + issue["id"])
        if result["status"] == "done":
            comments = api("/api/issues/" + issue["id"] + "/comments")
            if not any("Original reviewed validator executed and passed. Source SHA256:" in x.get("body", "") for x in comments):
                raise RuntimeError("No original worker evidence")
            agents = api(roster)
            if len(agents) != 6:
                raise RuntimeError("Unexpected roster")
            print(json.dumps({"paperclip_company": cid, "issue": issue["id"], "status": "done",
                "roster_count": len(agents), "actual_worker": "Engineering and Manufacturing",
                "paid_inference": False, "persistent_production": False}))
            return
        time.sleep(3)
    raise RuntimeError("Paperclip did not complete the actual worker task")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    run_worker() if args.worker else seed()
