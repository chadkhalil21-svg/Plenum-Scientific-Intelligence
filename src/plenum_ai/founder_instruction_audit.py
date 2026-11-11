"""Independent founder-instruction acceptance auditor on existing GitHub Minister schedule.

No new AI model, plugin host, vendor signup or private chat ingestion. The
auditor checks explicit PUBLIC objective abstracts against original GitHub PRs
and bot-run comments. It refuses to call source-only work a live deployment.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .weekly_founder_brief import REPO, CHIEF_QUEUE, github_json, publish_once

ROOT = Path(__file__).resolve().parents[2]
COVERAGE = ROOT / "docs/PLENUM_FOUNDER_INSTRUCTION_COVERAGE.json"
VALID_SCOPES = frozenset({
    "source_only", "source_pending", "partial", "external_live",
    "narrow_public_worker", "source_research_metadata", "video_incomplete",
})


def load_coverage(path=COVERAGE):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    tasks = doc.get("requirements")
    if (doc.get("schema") != "plenum-founder-instruction-coverage-v1"
            or doc.get("complete_reconstruction") is not False
            or not isinstance(tasks, list) or not 10 <= len(tasks) <= 60
            or doc.get("founder_instructions_count") != len(tasks)):
        raise ValueError("Unreviewed coverage ledger or false history-completeness claim")
    ids = set()
    for task in tasks:
        if (not isinstance(task, dict)
                or not isinstance(task.get("id"), str)
                or task["id"] in ids
                or task.get("acceptance_scope") not in VALID_SCOPES
                or not isinstance(task.get("priority"), int)
                or task["priority"] < 1
                or not isinstance(task.get("remaining_action"), str)
                or len(task["remaining_action"]) > 500
                or task.get("private_chat_transcript_read") is not False
                or task.get("secret_included") is not False
                or task.get("founder_acceptance_recorded") is not False):
            raise ValueError("Inconsistent public objective audit record")
        ids.add(task["id"])
        for key in ("pr", "issue"):
            n = task.get(key)
            if n is not None and (not isinstance(n,int) or isinstance(n,bool) or n < 1 or n >= 1000000000):
                raise ValueError("Unapproved GitHub evidence identifier")
    return doc


def evidence_for(task, *, pulls, comments):
    scope = task["acceptance_scope"]
    num = task.get("pr")
    merged = bool(isinstance(pulls.get(num), dict) and pulls[num].get("merged") is True)
    issue = task.get("issue")
    statements = comments.get(issue, []) if issue is not None else []
    if not isinstance(statements, list):
        raise ValueError("Unable to verify GitHub agent issue comments")
    bodies = []
    for item in statements:
        if not isinstance(item, dict):
            continue
        if (item.get("user") or {}).get("login") not in ("github-actions[bot]",):
            continue
        body = item.get("body")
        if isinstance(body, str):
            bodies.append(body)
    real_chief = any("Chief status: VERIFIED_CHIEF_DELEGATION" in x
                     and "specialist_executed=True" in x for x in bodies)
    council = any("Plenum council status: ADVISORY_DELIBERATION_AWAITING_FOUNDER" in x
                  and "completed: 4/4" in x for x in bodies)
    metadata = any("DRAFT_READY_FOR_FOUNDER" in x
                   and "provider-retrieval metadata/schema only" in x for x in bodies)
    # No event, public issue, CI green, or source merge is proof of a live
    # account connection or an independently verified private business task.
    if scope == "external_live":
        status = "OPEN_LIVE_ACCEPTANCE_MISSING"
    elif scope == "video_incomplete":
        status = "OPEN_FULL_VIDEO_CONTENT_MISSING"
    elif scope == "partial":
        status = "PARTIAL_DO_NOT_CLOSE"
    elif scope == "source_research_metadata":
        status = "LIMITED_METADATA_RETRIEVED" if metadata else "OPEN_NO_VERIFIED_RESEARCH_RESULT"
    elif scope == "narrow_public_worker":
        status = "LIMITED_REAL_WORKER_EXECUTED" if real_chief else "OPEN_NO_VERIFIED_AGENT_RUN"
    elif scope == "source_only":
        status = "ACCEPTED_SOURCE_MERGE_ONLY" if merged else "OPEN_NO_VERIFIED_MERGE"
    else:
        status = "SOURCE_PREPARED_AWAITING_MERGE" if not merged else "ACCEPTED_SOURCE_MERGE_ONLY"
    if scope == "partial" and council:
        status = "PARTIAL_ADVISORY_RAN_NOT_COMPLETE"
    return {
        "id": task["id"], "owner": task["owner_role"],
        "status": status, "priority": task["priority"],
        "summary": task["public_objective_summary"],
        "next": task["remaining_action"],
        "merged_source_pr": num if merged else None,
        "public_issue": issue,
        "actual_chief_public_worker_reported": real_chief,
        "model_council_reported": council,
        "source_metadata_only": metadata,
        "live_account_operation_verified": False,
    }


def collect(token: str, doc):
    tasks = doc["requirements"]
    prs = sorted({t["pr"] for t in tasks if t.get("pr") is not None})
    issues = sorted({t["issue"] for t in tasks if t.get("issue") is not None})
    base = f"https://api.github.com/repos/{REPO}/"
    pulls, comments = {}, {}
    for n in prs:
        data = github_json(base + f"pulls/{n}", token)
        if not isinstance(data, dict) or data.get("number") != n:
            raise ValueError("Missing original PR verification")
        pulls[n] = data
    for n in issues:
        data = github_json(base + f"issues/{n}/comments?per_page=100", token)
        if not isinstance(data, list) or len(data) >= 100:
            raise ValueError("Cannot reliably see full bounded public comment history")
        comments[n] = data
    return [evidence_for(t, pulls=pulls, comments=comments) for t in tasks]


def render(rows, *, as_of_date: str, doc):
    if not isinstance(as_of_date, str) or len(as_of_date) != 10:
        raise ValueError("Invalid audit date")
    if len(rows) != doc["founder_instructions_count"]:
        raise ValueError("Cannot omit requested founder objectives")
    ordered = sorted(rows, key=lambda a: (a["priority"], a["id"]))
    counts = Counter(x["status"] for x in rows)
    lines = [
        f"<!-- plenum-founder-instruction-audit:{as_of_date} -->",
        f"## Original Chief | Independent founder-instruction coverage — {as_of_date}",
        f"**{len(rows)} PUBLIC instruction summaries checked.** This ledger is only a partial reconstruction of previous chat prompts, not a private or account-wide transcript connection.",
        "Only a merged source PR or an original GitHub Actions bot comment is accepted as evidence, each within its narrow scope. No private deployment is inferred.",
        "",
        "**Outcome counts:** " + "; ".join(f"{k}: {v}" for k,v in sorted(counts.items())),
        "",
        "### Highest priority unfulfilled or limited assignments"
    ]
    for x in ordered:
        if x["status"] == "ACCEPTED_SOURCE_MERGE_ONLY":
            continue
        lines.append(
            f"- **{x['id']}** / {x['owner']}: **{x['status']}**. "
            + x["next"] + (
                f" ([issue #{x['public_issue']}](https://github.com/{REPO}/issues/{x['public_issue']}))"
                if x["public_issue"] else ""
            )
        )
        if len(lines) > 18:
            break
    lines.extend([
        "",
        "Full status and accountable owners: [founder-instruction ledger](https://github.com/" + REPO + "/blob/main/docs/PLENUM_FOUNDER_INSTRUCTION_COVERAGE.json).",
        "This read-only audit does not copy private prompts to public GitHub, install tools, approve spending, access private accounts, or complete work by itself.",
    ])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", default="reports/minister-founder-instruction-audit.json")
    args = parser.parse_args(argv)
    doc = load_coverage()
    out = Path(args.out)
    if out.is_absolute() or out.parts[0] != "reports" or ".." in out.parts:
        parser.error("Only reports/ output path accepted")
    if not args.execute:
        print(json.dumps({"status":"REVIEWED_PUBLIC_COVERAGE_ONLY","objectives":len(doc["requirements"]),
                          "github_writes":False,"full_private_chat_access":False}))
        return
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("GITHUB_REPOSITORY") != REPO
            or os.getenv("GITHUB_EVENT_NAME") not in {"schedule","workflow_dispatch"}):
        raise PermissionError("Only original GitHub Minister schedule may run this public audit")
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise PermissionError("Original GitHub Actions token missing")
    rows = collect(token, doc)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    comment = render(rows, as_of_date=stamp, doc=doc)
    destination = publish_once(token, comment)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "schema":"plenum-founder-instruction-audit-v1",
        "as_of_utc":stamp,"publication":destination,
        "public_objectives":len(rows),"results":rows,
        "private_messages_read":False, "new_paid_model_called":False,
        "private_accounts_changed":False,
    }, indent=2) + "\n",encoding="utf-8")
    print("FOUNDER_INSTRUCTION_AUDIT " + destination)


if __name__ == "__main__":
    main()
