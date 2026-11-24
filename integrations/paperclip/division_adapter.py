"""Thin native Paperclip Process adapter for the existing five public divisions.

This is a scoped integration acceptance, not arbitrary task execution or a new
agent framework. Paperclip remains the task/heartbeat owner. Only exact public
integration objectives are accepted; no private records, paid inference, or
production writes. The local evidence directory belongs to the isolated board.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlencode

from acceptance import api

SPECS = {
    "research": ("Scientific Research", "Survey public corrosion monitoring papers"),
    "engineering": ("Engineering and Manufacturing", "Validate existing NOAA station metadata program"),
    "commercial": ("Commercial Operations", "Review existing public business availability"),
    "intelligence": ("Global Intelligence", "Read public NOAA station 8723214 metadata"),
    "verification": ("Verification and Advisory", "Independently review four public worker artifacts"),
}
DESCRIPTION = "Public Paperclip integration acceptance; original reviewed Plenum routines only."
ROOT = Path("/paperclip/plenum-mission-evidence")
MISSION_ORDER = ("intelligence", "research", "engineering", "commercial", "verification")


def public_worker(role, upstream=None):
    """Invoke existing real capabilities; no duplicate network or science code."""
    from plenum_ai.chief_contract_plan import run_contract, check_contract_result
    from plenum_ai.reviewed_domain_workers import reuse_original_program
    if role == "research":
        scope = {"paper_survey": SPECS[role][1]}
        result = run_contract("paper_discovery", scope, {})
        check_contract_result("paper_discovery", scope, {}, result)
        return result
    if role == "engineering":
        with tempfile.TemporaryDirectory() as tmp:
            return reuse_original_program("noaa_water_station_metadata", SPECS[role][1], Path(tmp) / "code")
    if role == "commercial":
        result = run_contract("business_readback", {}, {})
        check_contract_result("business_readback", {}, {}, result)
        return result
    if role == "intelligence":
        scope = {"station_ids": ["8723214"]}
        result = run_contract("noaa_metadata", scope, {})
        check_contract_result("noaa_metadata", scope, {}, result)
        return result
    if role == "verification":
        from plenum_ai.chief_contract_plan import selected_paper_ids, review_business_status
        from plenum_ai.chief_team_mission import _station_rows
        from plenum_ai.reviewed_domain_workers import DOMAIN_FILES
        if set(upstream or {}) != set(SPECS) - {"verification"}:
            raise ValueError("Exact four existing producer results required")
        paper_ids = selected_paper_ids({"paper_survey": SPECS["research"][1]}, upstream["research"])
        manifest = upstream["engineering"]
        if (manifest.get("functional_verifier_executed_and_passed") is not True
                or manifest.get("main_sha256") != hashlib.sha256(
                    DOMAIN_FILES["noaa_water_station_metadata"].read_bytes()).hexdigest()):
            raise ValueError("Existing program evidence failed source readback")
        commercial = review_business_status(upstream["commercial"])
        stations = _station_rows(upstream["intelligence"], ("8723214",))
        return {"research_dois": paper_ids, "engineering_source_sha256": manifest["main_sha256"],
                "commercial_review": commercial, "station_count": len(stations),
                "verified_public_artifact_scope": True, "general_autonomy_verified": False}
    raise ValueError("Unapproved division")


def read_evidence(company, role):
    path = ROOT / company / (role + ".json")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError("Missing or unsafe original public evidence")
    record = json.loads(path.read_text())
    encoded = json.dumps(record["result"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    if (record.get("role") != role or record.get("company") != company
            or hashlib.sha256(encoded).hexdigest() != record.get("sha256")):
        raise ValueError("Public evidence binding failed")
    return record


def run_assigned(role, *, mission_worker=None):
    if role not in SPECS:
        raise ValueError("Unapproved division")
    agent = os.environ["PAPERCLIP_AGENT_ID"]
    company = os.environ["PAPERCLIP_COMPANY_ID"]
    identity = api("/api/agents/me", worker=True)
    if identity["id"] != agent or identity["companyId"] != company or identity["name"] != SPECS[role][0]:
        raise PermissionError("Incorrect native agent identity")
    import uuid
    if str(uuid.UUID(company)) != company:
        raise ValueError("Invalid company identity")
    task = os.environ.get("PAPERCLIP_TASK_ID")
    if task:
        rows = [api("/api/issues/" + str(uuid.UUID(task)), worker=True)]
    else:
        rows = api("/api/companies/" + company + "/issues?" + urlencode({
            "assigneeAgentId": agent, "status": "todo,in_progress"}), worker=True)
    rows = [row for row in rows if row.get("assigneeAgentId") == agent
            and row.get("title") == SPECS[role][1] and row.get("description") == DESCRIPTION
            and row.get("status") in ("todo", "in_progress")]
    if len(rows) != 1:
        raise ValueError("Expected exactly one assigned integration task")
    task = str(uuid.UUID(rows[0]["id"]))
    path = "/api/issues/" + task
    api(path + "/checkout", "POST", {"agentId": agent, "expectedStatuses": ["todo", "in_progress"]}, worker=True)
    # The immutable task-bound receipt permits replay of a failed status write,
    # not repeating already completed network or program work.
    directory = ROOT / company
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / (role + ".json")
    if target.exists():
        receipt = read_evidence(company, role)
        if receipt.get("issue") != task:
            raise ValueError("Evidence belongs to a different task")
    else:
        # Native Paperclip owns task locks. Reserve at most two actual work
        # attempts before calling the read-only tools; a saved receipt is
        # reused without repeating provider work.
        if mission_worker is not None:
            for attempt in (1, 2):
                try:
                    with (directory / (role + ".attempt-" + str(attempt))).open("x") as stream:
                        stream.write(task)
                    break
                except FileExistsError:
                    continue
            else:
                raise RuntimeError("Bounded specialist attempt budget exhausted")
            previous = MISSION_ORDER[:MISSION_ORDER.index(role)]
            inputs = {key: read_evidence(company, key)["result"] for key in previous}
            result = mission_worker(role, inputs, directory)
        else:
            inputs = ({key: read_evidence(company, key)["result"] for key in SPECS if key != role}
                      if role == "verification" else None)
            result = public_worker(role, inputs)
        encoded = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        receipt = {"company": company, "issue": task, "role": role,
                   "result": result, "sha256": hashlib.sha256(encoded).hexdigest()}
        with target.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, sort_keys=True, allow_nan=False)
    api(path, "PATCH", {"status": "done", "comment": "Original public worker evidence SHA256: " +
        receipt["sha256"]}, worker=True)
    print(json.dumps({"division": role, "issue": task, "sha256": receipt["sha256"]}), flush=True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Specify an existing public division")
    run_assigned(sys.argv[1])
