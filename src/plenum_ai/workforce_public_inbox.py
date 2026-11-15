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
MAGIC_V2 = "PLENUM_PUBLIC_WORKFORCE_V2"
PUBLIC_KINDS = frozenset({"public_research", "public_program", "public_science", "public_creative"})
TOPIC = re.compile(r"^[\w\s,\-.()/+]{20,120}$", re.UNICODE)

def original_source_category(objective: str) -> str:
    """Choose an EXISTING World Horizon category, never invent a new provider."""
    return ("funding" if re.search(
        r"\b(?:funding|grants?|solicitations?)\b", objective, re.I,
    ) else "all")




# Feed category is not evidence that a grant fits a specific research topic.
# Lexical matches are ONLY candidate signals; never verified eligibility.
_FUNDING_SEARCH_WORDS = frozenset("""
find review survey inspect check verify identify locate search current latest new
available open nsf nih sbir sttr funding funded funds grants grant leads lead
solicitation solicitations opportunities opportunity program programs awards award
application applications proposal proposals deadline deadlines research studies
study scientific science for from with into on the and of about that this
small business startup federal national public original sources source
""".split())


def funding_subject_title_evidence(objective: str, records: list[dict]) -> tuple[int, int]:
    """Count distinct subject stems and titles matching the subject.

    Require two matching terms when an objective has multiple subject terms;
    broad funding-program titles alone must not count as subject-specific.
    No claim of verified topical fit, eligibility or proposal deadlines.
    """
    if original_source_category(objective) != "funding":
        return 0, 0
    stems = {word[:4] for word in re.findall(r"[a-z]{4,}", objective.lower())
             if word not in _FUNDING_SEARCH_WORDS}
    if not stems:
        return 0, 0
    needed = min(2, len(stems))
    matched = 0
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("title"), str):
            continue
        title_stems = {word[:4] for word in
                       re.findall(r"[a-z]{4,}", row["title"].lower())}
        if len(stems & title_stems) >= needed:
            matched += 1
    return len(stems), matched

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
    if len(lines) == 2 and lines[0] == MAGIC and lines[1].startswith("objective: "):
        kind = "public_research"
        objective = lines[1][11:].strip()
    elif (len(lines) == 3 and lines[0] == MAGIC_V2
          and lines[1].startswith("kind: ")
          and lines[2].startswith("objective: ")):
        kind = lines[1][6:].strip()
        objective = lines[2][11:].strip()
    else:
        raise ValueError("Use exact Plenum public workforce v1 or v2 task form")
    if kind not in PUBLIC_KINDS:
        raise ValueError("Unknown public worker type")
    if (not TOPIC.fullmatch(objective) or
            any(word in objective.lower() for word in
                ("password", "secret", "credential", "token", "confidential", "private key"))):
        raise ValueError("Only a bounded, explicitly PUBLIC objective is allowed")
    from .workforce_team_dispatch import ROLES
    worker = "existing_plenum_world_horizon" if kind == "public_research" else ROLES[kind]
    return {"issue_number": issue["number"], "objective": objective,
            "kind": kind, "worker": worker,
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
    if original_source_category(objective) == "funding" and (
            report.get("category") != "funding"
            or any(not isinstance(row, dict) or row.get("category") != "funding"
                   for row in rows)):
        raise ValueError("Unrelated science feed cannot satisfy a funding-only assignment")
    if len(rows) > 200:
        raise ValueError("Unbounded research report")
    vetted = [
        x for x in rows if isinstance(x, dict)
        and isinstance(x.get("url"), str) and x["url"].startswith("https://")
        and isinstance(x.get("source"), str) and isinstance(x.get("title"), str)
    ]
    funding_terms, funding_matches = funding_subject_title_evidence(objective, vetted)
    return {
        "source_linked_records": len(vetted),
        "funding_subject_stems": funding_terms,
        "funding_subject_title_matches": funding_matches,
        "funding_topic_fit_independently_verified": False,
        "public_metadata_schema_verified": True,
        "individual_papers_independently_validated": False,
        "scientific_discovery_verified": False,
        "business_accounts_touched": False,
        "quality": "PUBLIC_SOURCE_LEADS_FOR_REVIEW" if vetted else "NO_SOURCE_LEADS",
    }


def run_issue(event: dict, *, output_dir: Path, runner=subprocess.run) -> dict:
    task = parse_public_issue(event)
    output_dir.mkdir(parents=True, exist_ok=True)
    if task["kind"] != "public_research":
        from .workforce_team_dispatch import dispatch
        try:
            outcome = dispatch(task, output_dir)
        except (OSError, ValueError, RuntimeError, SyntaxError, KeyError, TypeError):
            return {**task, "status": "BLOCKED_WORKER_OR_VERIFICATION",
                    "verified": False, "reason": "Specialist did not pass independent review",
                    "output_artifact": None}
        return {**task, **outcome, "business_accounts_touched": False,
                "no_money_spent_by_worker": True,
                "completed_at_utc": datetime.now(timezone.utc).isoformat()}
    output = output_dir / ("workforce-public-" + str(task["issue_number"]) + ".json")
    from .reviewed_domain_workers import match_original_capability, official_source_records
    capability = match_original_capability(task["objective"])
    if capability:
        # This exact scoped primary-source reader takes precedence over
        # unrelated general-science feed listings. Same ORIGINAL worker output.
        try:
            records = official_source_records(capability)
        except (OSError, ValueError, TypeError):
            records = []
        output.write_text(json.dumps({
            "schema": "plenum-public-horizon-snapshot-v1",
            "topic": task["objective"],
            "records": records,
            "independent_breakthrough_verified": False,
            "AGI_achieved": False,
            "source_scope": "original vetted first-party public docs, HTTP 200 metadata",
            "publisher_document_text_verified": False,
        }, indent=2) + "\n", encoding="utf-8")
        checked = validate_original_report(output, task["objective"])
        if not records or checked["source_linked_records"] != len(records):
            return {
                **task, **checked,
                "status": "BLOCKED_NO_PRIMARY_SOURCE_EVIDENCE",
                "verified": False, "output_artifact": output.name,
                "reason": "Trusted official source GET was unavailable",
            }
        return {
            **task, **checked,
            "status": "DRAFT_READY_FOR_FOUNDER",
            "verified": True, "output_artifact": output.name,
            "worker": task["worker"],
            "reused_existing_reviewed_primary_sources": True,
            "domain_capability": capability,
            "verified_scope": "bounded official public primary source HTTP 200 metadata only",
            "readback": "local original report parsed; no quote or commercial rate independently audited",
            "no_money_spent_by_worker": True,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        }
    # Reuse the ALREADY tested worker. No shell, model install, tokens, or new browser.
    command = [
        sys.executable, "-m", "plenum_ai.cli", "world-horizon",
        "--category", original_source_category(task["objective"]),
        "--topic", task["objective"],
        "--online", "--out", str(output),
    ]
    safe_env = {k: v for k, v in os.environ.items()
                if k not in ("GH_TOKEN", "GITHUB_TOKEN") and
                not k.endswith(("_TOKEN", "_SECRET", "_API_KEY"))}
    try:
        result = runner(command, timeout=360, cwd=str(Path(__file__).resolve().parents[2]),
                        env=safe_env, capture_output=True, text=True, check=False)
    except (subprocess.TimeoutExpired, OSError):
        return {**task, "status": "BLOCKED_WORKER_UNAVAILABLE", "verified": False,
                "reason": "Existing worker did not finish within bounded runtime",
                "output_artifact": None}
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
    if checked["source_linked_records"] == 0:
        return {**task, **checked, "status": "BLOCKED_NO_SOURCE_EVIDENCE",
                "verified": False, "output_artifact": output.name}
    if (original_source_category(task["objective"]) == "funding"
            and checked["funding_subject_stems"] > 0
            and checked["funding_subject_title_matches"] == 0):
        return {
            **task, **checked,
            "status": "BLOCKED_FUNDING_TOPIC_UNVERIFIED",
            "verified": False, "output_artifact": output.name,
            "reason": "Funding feed lacks title evidence for the requested research subject",
            "verified_scope": "provider metadata only; topic relevance not established",
            "no_money_spent_by_worker": True,
        }
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
    notes = (
        "Status: **" + status + "**. "
        "Assigned original Plenum worker: " + str(summary.get("worker", "unverified"))
        + ". Task type: " + str(summary.get("kind", "unverified"))
        + ". Verified scope: " + str(summary.get("verified_scope",
                                "blocked or incomplete"))
        + ". Public research leads: " + str(summary.get("source_linked_records", 0))
        + ". Output requires founder review; no customer accounts, "
          "private data, paid services or business writes used. "
        + "Run evidence: https://github.com/" + REPO + "/actions/runs/" + run_id
    )
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
