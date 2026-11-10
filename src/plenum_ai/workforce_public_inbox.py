"""Public founder task inbox bridging existing GitHub Issues to existing Plenum workers.

This adapter is deliberately NOT another agent framework. GitHub Issues hold
public work state; GitHub Actions supplies free short-lived compute. Private
tasks, sensitive data, payments, emails, browser sessions, and account writes
are forbidden. Original Deep Agents Chief and n8n specialists are preserved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import Request, build_opener

from .chief_of_staff_pilot import NoRedirects

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"
TITLE = "[Plenum Workforce] public research"
MAGIC = "PLENUM_PUBLIC_WORKFORCE_V1"
TOPIC = re.compile(r"^[\w\s,\-.()/+]{20,120}$", re.UNICODE)


def parse_public_issue(event: dict) -> dict:
    """Fail closed before running software, including on non-owner issue events."""
    issue = event.get("issue") or {}
    if (event.get("action") != "opened"
            or (event.get("repository") or {}).get("full_name") != REPO
            or (issue.get("user") or {}).get("login") != OWNER
            or issue.get("title") != TITLE
            or not isinstance(issue.get("number"), int)
            or not isinstance(issue.get("body"), str)):
        raise ValueError("Not a founder-authorized public research assignment")
    lines = issue["body"].splitlines()
    if (len(lines) != 2 or lines[0] != MAGIC
            or not lines[1].startswith("objective: ")):
        raise ValueError("Public task must use exact two-line workforce form")
    objective = lines[1][11:].strip()
    if (not TOPIC.fullmatch(objective) or
            any(word in objective.lower() for word in
                ("password", "secret", "credential", "token", "confidential", "private key"))):
        raise ValueError("Only a bounded, explicitly PUBLIC objective is allowed")
    return {"issue_number": issue["number"], "objective": objective,
            "kind": "public_research", "worker": "existing_plenum_world_horizon",
            "requested_by": OWNER, "cost_ceiling_usd": 0,
            "approval": "read_only_public_sources_only"}


def validate_original_report(path: Path, objective: str) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    if (report.get("schema") != "plenum-public-horizon-snapshot-v1"
            or report.get("topic") != objective
            or report.get("independent_breakthrough_verified") is not False
            or report.get("AGI_achieved") is not False
            or not isinstance(report.get("records"), list)):
        raise ValueError("Original research worker did not produce its accepted schema")
    rows = report["records"]
    if len(rows) > 200:
        raise ValueError("Unbounded research report")
    vetted = [
        x for x in rows if isinstance(x, dict)
        and isinstance(x.get("url"), str) and x["url"].startswith("https://")
        and isinstance(x.get("source"), str) and isinstance(x.get("title"), str)
    ]
    return {
        "source_linked_records": len(vetted),
        "public_metadata_schema_verified": True,
        "individual_papers_independently_validated": False,
        "scientific_discovery_verified": False,
        "business_accounts_touched": False,
        "quality": "PUBLIC_SOURCE_LEADS_FOR_REVIEW" if vetted else "NO_SOURCE_LEADS",
    }


def run_issue(event: dict, *, output_dir: Path, runner=subprocess.run) -> dict:
    task = parse_public_issue(event)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / ("workforce-public-" + str(task["issue_number"]) + ".json")
    # Reuse the ALREADY tested worker. No shell, model install, tokens, or new browser.
    command = [
        sys.executable, "-m", "plenum_ai.cli", "world-horizon",
        "--category", "all", "--topic", task["objective"],
        "--online", "--out", str(output),
    ]
    safe_env = {k: v for k, v in os.environ.items()
                if k not in ("GH_TOKEN", "GITHUB_TOKEN") and
                not k.endswith(("_TOKEN", "_SECRET", "_API_KEY"))}
    result = runner(command, timeout=360, cwd=str(Path(__file__).resolve().parents[2]),
                    env=safe_env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {**task, "status": "BLOCKED_WORKER_FAILED", "verified": False,
                "reason": "Original public research worker failed",
                "output_artifact": None}
    try:
        checked = validate_original_report(output, task["objective"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {**task, "status": "BLOCKED_VERIFICATION", "verified": False,
                "reason": "Original report failed independent schema check",
                "output_artifact": None}
    return {
        **task, **checked, "status": "DRAFT_READY_FOR_FOUNDER",
        "verified": True, "output_artifact": output.name,
        "verified_scope": "provider-retrieval metadata/schema only",
        "readback": "independent local report parse, not second publication fact-check",
        "no_money_spent_by_worker": True,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def publish_status(issue_number: int, summary: dict, *, token: str,
                   run_id: str, opener=None) -> str:
    """Post only nonsecret, bounded completion status to the SAME public issue."""
    if not token or not str(run_id).isdigit() or not 0 < issue_number < 10**10:
        raise ValueError("No valid GitHub automation identity")
    url = "https://api.github.com/repos/" + REPO + f"/issues/{issue_number}/comments"
    client = opener or build_opener(NoRedirects)
    common = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "User-Agent": "PlenumPublicWorkforce/1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    marker = "<!-- plenum-public-workforce-run:" + run_id + " -->"
    try:
        with client.open(Request(url + "?per_page=100", headers=common), timeout=12) as response:
            comments = json.loads(response.read(100001))
    except Exception as exc:
        raise RuntimeError("Could not check issue comment idempotency") from exc
    if not isinstance(comments, list):
        raise RuntimeError("Invalid issue comment response")
    if any(isinstance(x, dict) and marker in str(x.get("body", "")) for x in comments):
        return "ALREADY_RECORDED"
    status = summary["status"]
    notes = ("Status: **" + status + "**. "
             "Worker: existing Plenum public research reader. "
             "Public source records: " + str(summary.get("source_linked_records", 0))
             + ". Findings are unreviewed leads, not validated discoveries. "
             "No customer accounts, private data or business writes accessed. "
             "Run evidence: https://github.com/" + REPO + "/actions/runs/" + run_id)
    body = marker + "\n" + notes[:1200]
    data = json.dumps({"body": body}).encode()
    with client.open(Request(url, data=data,
                             headers={**common, "Content-Type": "application/json"},
                             method="POST"), timeout=12) as response:
        if response.status != 201:
            raise RuntimeError("GitHub did not accept task completion status")
    return "RECORDED"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--event", required=True)
    p.add_argument("--out-dir", default="reports/workforce")
    args = p.parse_args()
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    out = Path(args.out_dir)
    if out.is_absolute() or ".." in out.parts or not out.parts or out.parts[0] != "reports":
        p.error("Output directory must be within reports/")
    task = parse_public_issue(event)
    result = run_issue(event, output_dir=out)
    status_file = out / ("status-" + str(task["issue_number"]) + ".json")
    status_file.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    record = publish_status(task["issue_number"], result, token=os.getenv("GH_TOKEN", ""),
                            run_id=os.environ.get("GITHUB_RUN_ID", ""))
    print("WORKFORCE_INBOX " + result["status"] + " issue=" + str(task["issue_number"])
          + " posted=" + record)
    if result["status"] != "DRAFT_READY_FOR_FOUNDER":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
