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
PUBLIC_KINDS = frozenset({"public_research", "public_program", "public_science", "public_creative", "public_verification"})
TOPIC = re.compile(r"^[\w\s,\-.()/+]{20,120}$", re.UNICODE)

def original_source_category(objective: str) -> str:
    """Choose an EXISTING World Horizon category, never invent a new provider."""
    from .world_horizon import paper_survey_subject
    if paper_survey_subject(objective):
        return "journals"
    return ("funding" if re.search(
        r"\b(?:funding|grants?|solicitations?)\b", objective, re.I,
    ) else "all")



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
    if kind == "public_verification":
        from .workforce_team_dispatch import parse_numeric_grounding
        parse_numeric_grounding(objective)
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
    return {
        "source_linked_records": len(vetted),
        "public_metadata_schema_verified": True,
        "individual_papers_independently_validated": False,
        "scientific_discovery_verified": False,
        "business_accounts_touched": False,
        "quality": ("FUNDING_CATEGORY_ONLY_SUBJECT_REVIEW_REQUIRED"
                    if original_source_category(objective) == "funding" and vetted
                    else "PUBLIC_SOURCE_LEADS_FOR_REVIEW" if vetted
                    else "NO_SOURCE_LEADS"),
        "funding_subject_relevance_independently_verified": False,
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
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {**task, "status": "BLOCKED_WORKER_UNAVAILABLE", "verified": False,
                "failure_type": type(exc).__name__,
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
    # A broad source survey can be completed with an official agency directory
    # even when the original opportunity search returns no matching titles.
    # This does NOT accept an eligibility, deadline or specific grant request.
    if checked["source_linked_records"] == 0 and re.fullmatch(
            r"(?:Survey|Review) public (?:agricultural|agriculture) funding sources",
            task["objective"], re.I):
        from .reviewed_domain_workers import DOMAIN_SOURCES
        capability = "usda_agricultural_funding_directory"
        expected = {(title, organization, url)
                    for title, organization, url in DOMAIN_SOURCES[capability]}
        try:
            records = official_source_records(
                capability, opener=build_opener(NoRedirects).open)
            identities = {(row.get("title"), row.get("source"), row.get("url"))
                          for row in records}
            if (len(records) >= 2 and len(identities) == len(records)
                    and identities <= expected
                    and all(row.get("http_status") == 200
                            and row.get("independently_quoted_page_text") is False
                            for row in records)):
                original = json.loads(output.read_text("utf-8"))
                if original["records"]:
                    raise ValueError("Fallback requires no original records")
                original["funding_recovery"] = {
                    "strategy": "reviewed_official_agency_directory",
                    "prior_source_linked_records": 0,
                    "original_provider_diagnostics_preserved": True,
                    "opportunity_eligibility_or_deadline_verified": False,
                }
                original["records"] = [{**row, "category": "funding"} for row in records]
                output.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
                accepted = validate_original_report(output, task["objective"])
                return {**task, **accepted,
                        "status": "DRAFT_READY_FOR_FOUNDER", "verified": True,
                        "output_artifact": output.name,
                        "quality": "OFFICIAL_FUNDING_SOURCE_DIRECTORY_VERIFIED",
                        "funding_source_directory_verified": True,
                        "funding_subject_relevance_independently_verified": False,
                        "verified_scope": "reviewed official agricultural funding directory HTTP 200 metadata only; eligibility and deadlines not independently audited",
                        "no_money_spent_by_worker": True,
                        "completed_at_utc": datetime.now(timezone.utc).isoformat()}
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            pass
    if checked["source_linked_records"] == 0:
        return {**task, **checked, "status": "BLOCKED_NO_SOURCE_EVIDENCE",
                "verified": False, "output_artifact": output.name}
    from .world_horizon import paper_survey_subject, paper_title_matches
    subject=paper_survey_subject(task["objective"])
    if subject:
        rows=json.loads(output.read_text("utf-8"))["records"]
        matched=bool(rows) and all(
            row.get("source")=="crossref_journals"
            and row.get("category")=="journals"
            and re.fullmatch(r"https://doi\.org/10\.[0-9]{4,9}/[^\s?#]+",row.get("url",""))
            and paper_title_matches(subject,row.get("title"))
            for row in rows)
        return {**task,**checked,
                "status":"DRAFT_READY_FOR_FOUNDER" if matched else "BLOCKED_PAPER_TOPIC_RELEVANCE",
                "verified":matched,"output_artifact":output.name,
                "paper_title_match_verified":matched,
                "individual_papers_independently_validated":False,
                "verified_scope":"topic-matched Crossref journal metadata only; paper contents and scientific claims not audited",
                "no_money_spent_by_worker":True,
                "completed_at_utc":datetime.now(timezone.utc).isoformat()}
    if original_source_category(task["objective"]) == "funding":
        from .world_horizon import funding_survey_subject, funding_title_matches
        subject=funding_survey_subject(task["objective"])
        if subject:
            report=json.loads(output.read_text("utf-8"))
            rows=report["records"]
            if (rows and all(row.get("source")=="grants_gov_search"
                    and re.fullmatch(r"https://www\.grants\.gov/search-results-detail/[1-9][0-9]{0,11}",row.get("url",""))
                    and funding_title_matches(subject,row.get("title"))
                    and str(row.get("metadata_note","")).startswith(("posted;","forecasted;"))
                    for row in rows)):
                return {**task,**checked,"status":"DRAFT_READY_FOR_FOUNDER","verified":True,
                        "output_artifact":output.name,
                        "quality":"PUBLIC_FUNDING_TITLE_MATCHED_SOURCE_SURVEY_ONLY",
                        "funding_title_match_verified":True,
                        "funding_subject_relevance_independently_verified":False,
                        "verified_scope":"official public funding search metadata and explicit title matches only; eligibility and deadlines not independently audited",
                        "no_money_spent_by_worker":True,
                        "completed_at_utc":datetime.now(timezone.utc).isoformat()}
        # Original mission #708 retrieved genuine funding-category records
        # unrelated to the founder's photonics objective. A real provider URL
        # and category tag do NOT independently establish program fit.
        # Preserve useful leads, but NEVER claim the requested subject verified.
        return {
            **task, **checked,
            "status": "REVIEW_REQUIRED_FUNDING_SUBJECT_RELEVANCE",
            "verified": False, "output_artifact": output.name,
            "verified_scope": "funding-category public metadata only",
            "reason": "Specific topic, application scope and eligibility remain unverified",
            "no_money_spent_by_worker": True,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
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
