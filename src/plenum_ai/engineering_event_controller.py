"""Trusted, bounded event-driven engineering supervision.

Never execute PR code, use untrusted logs as instructions, or auto-merge.
The original Minister retains control. Only public repository-development
checks named in the approved registry may be observed or retried.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"
API = "https://api.github.com/repos/" + REPO
REGISTERED = {
    924: ("prometheus-upstream-expansion-20261125",
          "Prometheus upstream skill supply-chain qualification", "static-review"),
    925: ("prometheus-local-document-retrieval",
          "Prometheus model-free document retrieval qualification", "public-fixture"),
    928: ("prometheus-whisper-local-qualification",
          "Prometheus | Pinned local speech recognition qualification", "synthetic-speech"),
    929: ("prometheus-blender-scientific-render",
          "Prometheus | Blender concept geometry qualification", "original-concept"),
    935: ("prometheus-hyperframes-local-qualification",
          "Prometheus | HyperFrames local motion qualification", "local-motion"),
    936: ("prometheus-accepted-upstream-evidence-registry",
          "Prometheus upstream skill supply-chain qualification", "static-review"),
}
SHA = re.compile(r"^[a-f0-9]{40}$")
# New work must have an explicit owner-approved, exact-head admission line.
# This is observation and setup-only recovery, NEVER code or merge authority.
APPROVAL = re.compile(r"^<!-- plenum-engineering-observe-v1:([a-f0-9]{40}):([A-Za-z0-9 ._|-]{1,100}):([A-Za-z0-9 ._|-]{1,100}) -->$", re.MULTILINE)
BRANCH = re.compile(r"^prometheus-[a-z0-9][a-z0-9-]{0,100}$")
MAX_DYNAMIC = 12
DYNAMIC = {}

def dynamic_entry(pr):
    if not isinstance(pr, dict) or not number(pr.get("number")):
        return None
    n = pr["number"]
    if n in REGISTERED or pr.get("state") != "open" or pr.get("draft") is not False:
        return None
    head, base = pr.get("head") or {}, pr.get("base") or {}
    if ((pr.get("user") or {}).get("login") != OWNER
            or (head.get("repo") or {}).get("full_name") != REPO
            or (base.get("repo") or {}).get("full_name") != REPO
            or base.get("ref") != "main" or not isinstance(head.get("ref"), str)
            or not BRANCH.fullmatch(head["ref"]) or not isinstance(pr.get("body"), str)):
        return None
    lines = [line for line in pr["body"].splitlines() if "plenum-engineering-observe-v1:" in line]
    if len(lines) != 1:
        return None
    m = APPROVAL.fullmatch(lines[0])
    if m is None or m[1] != head.get("sha"):
        return None
    return (head["ref"], m[2], m[3], m[1])

def owner_approval(pr, row):
    # PR descriptions are editable by collaborators. Require the exact
    # unedited owner-authored comment as separate admission evidence.
    n = pr["number"]
    rows = request(f"/issues/{n}/comments?per_page=100")
    if not isinstance(rows, list) or len(rows) >= 100:
        return False
    expected = f"<!-- plenum-engineering-observe-v1:{row[3]}:{row[1]}:{row[2]} -->"
    matches = [c for c in rows if isinstance(c, dict)
               and c.get("body") == expected
               and (c.get("user") or {}).get("login") == OWNER
               and (c.get("user") or {}).get("id") == 251133044
               and c.get("author_association") == "OWNER"
               and isinstance(c.get("created_at"), str)
               and c.get("created_at") == c.get("updated_at")]
    return len(matches) == 1

def registry():
    return {**REGISTERED, **{n: row[:3] for n, row in DYNAMIC.items()}}

def discover():
    rows = request("/pulls?state=open&base=main&per_page=100")
    if not isinstance(rows, list) or len(rows) >= 100:
        raise RuntimeError("Open PR discovery exceeds bounded scope")
    found = {}
    for pr in rows:
        row = dynamic_entry(pr)
        if row is not None and owner_approval(pr, row):
            n = pr["number"]
            if n in found:
                raise RuntimeError("Duplicate PR identity")
            found[n] = row
    if len(found) > MAX_DYNAMIC:
        raise RuntimeError("Approved engineering queue exceeds bounded scope")
    DYNAMIC.clear()
    DYNAMIC.update(found)
MARKER = "<!-- plenum-engineering-controller-v1:"
MAX_BYTES = 2_000_000
RECEIPT_ISSUE = 432
WAKE_TITLE = "[Plenum Engineering] approved backlog wake"
WAKE_BODY = "PLENUM_ENGINEERING_WAKE_V1"
# One audited repair recipe, bound to original failed public development run.
WHISPER_REPAIR_RUN = 45767285022
WHISPER_REPAIR_HEAD = "a9ed286a49308fb5e01ed25a53c08f65e72445af"
WHISPER_REPAIR_JOB = 139731117752


def number(x):
    return type(x) is int and 0 < x < 10**13


def authorized_pr(pr, n):
    if n not in registry() or not isinstance(pr, dict):
        return False
    if n in DYNAMIC and dynamic_entry(pr) != DYNAMIC[n]:
        return False
    branch, _, _ = registry()[n]
    head, base = pr.get("head") or {}, pr.get("base") or {}
    return (
        pr.get("number") == n and pr.get("state") == "open"
        and (pr.get("user") or {}).get("login") == OWNER
        and head.get("ref") == branch and base.get("ref") == "main"
        and (head.get("repo") or {}).get("full_name") == REPO
        and (base.get("repo") or {}).get("full_name") == REPO
        and isinstance(head.get("sha"), str) and SHA.fullmatch(head["sha"]) is not None
    )


def eligible_run(pr, n, run):
    if not authorized_pr(pr, n) or not isinstance(run, dict):
        return False
    branch, workflow, _ = registry()[n]
    return (
        number(run.get("id")) and run.get("name") == workflow
        and run.get("event") == "pull_request"
        and run.get("head_branch") == branch
        and run.get("head_sha") == pr["head"]["sha"]
        and (run.get("repository") or {}).get("full_name") == REPO
        and (run.get("head_repository") or {}).get("full_name") == REPO
        and (run.get("actor") or {}).get("login") == OWNER
        and type(run.get("run_attempt")) is int and 1 <= run["run_attempt"] <= 2
        and run.get("status") == "completed"
        and run.get("conclusion") in ("success", "failure", "cancelled", "timed_out")
    )


def diagnose(pr, n, run, jobs):
    """Retry only a demonstrably unstarted first-attempt infrastructure job.

    A dependency, test, scan or model failure is NEVER automatically replayed.
    A successful run is not an independent artifact or merge acceptance.
    """
    if not eligible_run(pr, n, run) or not isinstance(jobs, list):
        return {"status": "INELIGIBLE"}
    if run["conclusion"] not in ("success", "failure"):
        return {"status": "STOP_NON_SUCCESS"}
    _, _, name = registry()[n]
    matches = [j for j in jobs if isinstance(j, dict) and j.get("name") == name]
    if len(matches) != 1:
        return {"status": "BLOCKED_JOB_IDENTITY"}
    job = matches[0]
    steps = job.get("steps")
    if (job.get("run_id") != run["id"] or job.get("head_sha") != run["head_sha"]
            or not number(job.get("id")) or not isinstance(steps, list) or not steps
            or not all(isinstance(s, dict) for s in steps)):
        return {"status": "BLOCKED_JOB_IDENTITY"}
    if run["conclusion"] == "success":
        # A skipped or unrelated approved job cannot enter evidence review.
        if job.get("conclusion") != "success":
            return {"status": "BLOCKED_APPROVED_JOB_NOT_SUCCESS"}
        return {"status": "AWAIT_INDEPENDENT_EVIDENCE"}
    if job.get("conclusion") != "failure":
        return {"status": "BLOCKED_JOB_IDENTITY"}
    failed = [s for s in steps if s.get("conclusion") == "failure"]
    # Exact original speech fixture reached inference; the observed failure
    # was a transcript mismatch. Qualify a DIFFERENT pinned model once,
    # not a retry of the rejected tiny.en inference or a relaxed gate.
    if (n == 928 and run["id"] == WHISPER_REPAIR_RUN
            and run["head_sha"] == WHISPER_REPAIR_HEAD
            and run["run_attempt"] == 1 and job["id"] == WHISPER_REPAIR_JOB
            and len(failed) == 1
            and failed[0].get("name") == "Qualify upstream CLI on public synthetic fixture in isolated network namespace"
            and all(any(s.get("name") == name and s.get("conclusion") == "success"
                        for s in steps) for name in (
                "Build exact official whisper.cpp release",
                "Verify official MIT tiny English model and create original synthetic test speech"))):
        return {"status": "QUALIFY_PINNED_WHISPER_BASE_CORRECTION_ONCE"}
    # Retry only if checkout, dependency installs and all substantive steps
    # were never started. No retry for failed validation or partial execution.
    if (run["run_attempt"] == 1 and len(failed) == 1
            and failed[0].get("name") == "Set up job"
            and all(s is failed[0] or s.get("conclusion") in ("skipped", None)
                    for s in steps)):
        return {"status": "RETRY_UNSTARTED_INFRASTRUCTURE_ONCE", "job_id": job["id"]}
    return {"status": "BLOCKED_NEEDS_CORRECTION"}


def request(path, method="GET", payload=None):
    # No externally supplied URL, redirects or shell interpolation.
    from urllib.request import build_opener, HTTPRedirectHandler
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise RuntimeError("Unexpected API redirect")
    token = os.environ["GH_TOKEN"]
    data = None if payload is None else json.dumps(payload).encode()
    req = Request(API + path, data=data, method=method,
                  headers={"Authorization": "Bearer " + token,
                           "Accept": "application/vnd.github+json",
                           "X-GitHub-Api-Version": "2022-11-28",
                           "Content-Type": "application/json"})
    with build_opener(NoRedirect).open(req, timeout=15) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise RuntimeError("Oversized GitHub response")
        return json.loads(raw) if raw else {}


def marker(n, run, status):
    return f"{MARKER}{n}:{run['id']}:{run['run_attempt']}:{run['head_sha']}:{status} -->"


def process(n, run_id=None):
    pr = request(f"/pulls/{n}")
    if not authorized_pr(pr, n):
        return {"pr": n, "status": "NOT_AUTHORIZED_OR_CLOSED"}
    sha = pr["head"]["sha"]
    if run_id is None:
        runs = request(f"/actions/runs?head_sha={sha}&event=pull_request&per_page=30").get("workflow_runs", [])
    else:
        if not number(run_id):
            raise ValueError("Invalid run identifier")
        runs = [request(f"/actions/runs/{run_id}")]
    matching = [w for w in runs if eligible_run(pr, n, w)]
    if not matching:
        return {"pr": n, "status": "NO_ELIGIBLE_TERMINAL_RUN"}
    run = max(matching, key=lambda w: (w["id"], w["run_attempt"]))
    # If a newer matching same-head run is queued or running, do not issue
    # a repair/retry based on stale failure information.
    all_runs = request(f"/actions/runs?head_sha={sha}&event=pull_request&per_page=30").get("workflow_runs", [])
    if any(w.get("name") == run["name"] and w.get("head_sha") == sha
           and (w.get("id", 0) > run["id"] or
                (w.get("id") == run["id"] and w.get("run_attempt", 0) > run["run_attempt"]))
           for w in all_runs):
        return {"pr": n, "status": "SUPERSEDED"}
    jobs = request(f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs?per_page=30").get("jobs", [])
    result = diagnose(pr, n, run, jobs)
    result.update({"pr": n, "run": run["id"], "head": sha,
                   "paid_inference": False, "merge_authorized": False})
    if result["status"] == "INELIGIBLE":
        return result
    receipt = marker(n, run, result["status"])
    # Use the original master issue, not a PR comment requiring broader rights.
    # Fixed per-run receipt; only a genuine Actions bot receipt counts as a
    # prior reservation. Bound pagination rather than silently ignoring old
    # reservations. Fail closed if the limit is exceeded.
    from datetime import datetime, timezone
    from urllib.parse import urlencode
    created = run.get("created_at")
    if not isinstance(created, str):
        raise ValueError("Missing original run creation time")
    started = datetime.fromisoformat(created.replace("Z", "+00:00"))
    if started.tzinfo is None or started > datetime.now(timezone.utc):
        raise ValueError("Invalid run creation time")
    comments = []
    for page in range(1, 6):
        query = urlencode({"per_page": 100, "page": page, "since": created})
        rows = request(f"/issues/{RECEIPT_ISSUE}/comments?{query}")
        if not isinstance(rows, list):
            raise RuntimeError("Invalid comment list")
        comments.extend(rows)
        if len(rows) < 100:
            break
    else:
        raise RuntimeError("Receipt history exceeds bounded search")
    if any((c.get("user") or {}).get("login") == "github-actions[bot]"
           and isinstance(c.get("body"), str) and c["body"].startswith(receipt + "\n")
           for c in comments):
        result["already_recorded"] = True
        return result
    # Re-read the owner PR and run before any side effect.
    fresh = request(f"/pulls/{n}")
    latest = request(f"/actions/runs/{run['id']}")
    if (not eligible_run(fresh, n, latest) or latest["run_attempt"] != run["run_attempt"]
            or latest["conclusion"] != run["conclusion"]
            or (n in DYNAMIC and not owner_approval(fresh, DYNAMIC[n]))):
        result["status"] = "SUPERSEDED"
        return result
    body = receipt + "\n" + (
        f"Minister engineering controller: {result['status']}. "
        f"Run {run['id']}, exact head {sha}. No paid inference or merge authorization."
    )
    # Reserve before any retry. Ambiguous reservations never replay.
    posted = request(f"/issues/{RECEIPT_ISSUE}/comments", "POST", {"body": body})
    if (posted.get("user") or {}).get("login") != "github-actions[bot]" or posted.get("body") != body:
        raise RuntimeError("Reservation identity not confirmed")
    if result["status"] == "RETRY_UNSTARTED_INFRASTRUCTURE_ONCE":
        request(f"/actions/jobs/{result['job_id']}/rerun", "POST", {})
        result["retry_requested"] = True
    if result["status"] == "QUALIFY_PINNED_WHISPER_BASE_CORRECTION_ONCE":
        # Only the newly posted canonical reservation can activate this job.
        result["whisper_repair_reserved"] = True
    return result


def wake_authorized(event):
    if not isinstance(event, dict):
        return False
    issue = event.get("issue") or {}
    return (
        event.get("action") == "opened"
        and (event.get("repository") or {}).get("full_name") == REPO
        and (event.get("sender") or {}).get("login") == OWNER
        and (issue.get("user") or {}).get("login") == OWNER
        and number(issue.get("number"))
        and issue.get("state") == "open"
        and "pull_request" not in issue
        and issue.get("title") == WAKE_TITLE
        and issue.get("body") == WAKE_BODY
    )


def approval_event_number(event):
    """A new owner admission comment may wake only its exact approved PR."""
    if not isinstance(event, dict) or event.get("action") != "created":
        return None
    issue, comment = event.get("issue") or {}, event.get("comment") or {}
    sender, author = event.get("sender") or {}, comment.get("user") or {}
    if ((event.get("repository") or {}).get("full_name") != REPO
            or sender.get("login") != OWNER or sender.get("id") != 251133044
            or author.get("login") != OWNER or author.get("id") != 251133044
            or comment.get("author_association") != "OWNER"
            or not isinstance(comment.get("created_at"), str)
            or comment.get("created_at") != comment.get("updated_at")
            or not isinstance(comment.get("body"), str)
            or APPROVAL.fullmatch(comment["body"]) is None
            or not number(issue.get("number")) or issue.get("state") != "open"
            or "pull_request" not in issue
            or (issue.get("user") or {}).get("login") != OWNER):
        return None
    return issue["number"]


def fallback_authorized(event, now=None):
    import time
    now = int(time.time() * 1000) if now is None else now
    if not isinstance(event, dict):
        return False
    payload = event.get("client_payload")
    if not isinstance(payload, dict) or set(payload) != {"slot"}:
        return False
    slot = payload["slot"]
    return (event.get("action") == "plenum_engineering_backlog_tick_v1"
            and (event.get("repository") or {}).get("full_name") == REPO
            and (event.get("sender") or {}).get("login") == OWNER
            and type(slot) is int and slot > 0 and slot % 300000 == 0
            and 0 <= now - slot < 300000)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--kind", choices=("workflow_run", "schedule", "workflow_dispatch", "issues", "issue_comment", "repository_dispatch"), required=True)
    args = parser.parse_args()
    if os.getenv("GITHUB_REPOSITORY") != REPO:
        raise PermissionError("Wrong repository")
    event = json.loads(Path(args.event).read_text())
    if args.kind == "issue_comment":
        n = approval_event_number(event)
        if n is None:
            raise PermissionError("Not an authorized new engineering approval")
        # Re-read live PR and exact owner comment. An event alone cannot
        # establish current scope or authorize a stale head.
        pr = request(f"/pulls/{n}")
        row = dynamic_entry(pr)
        if (row is None or event["comment"]["body"] !=
                f"<!-- plenum-engineering-observe-v1:{row[3]}:{row[1]}:{row[2]} -->"
                or not owner_approval(pr, row)):
            raise PermissionError("Engineering approval no longer current")
        DYNAMIC.clear()
        DYNAMIC[n] = row
        results = [process(n)]
    else:
        discover()
    if args.kind == "issue_comment":
        pass  # Already scoped to the one approved task above.
    elif args.kind == "workflow_run":
        run = event.get("workflow_run", {})
        if not number(run.get("id")) or (run.get("repository") or {}).get("full_name") != REPO:
            return
        numbers = [n for n, row in registry().items() if row[1] == run.get("name") and row[0] == run.get("head_branch")]
        if not numbers:
            return
        # A registered completion also drains any older eligible backlog.
        # The exact-head, terminal, bot receipt, and no-replay gates remain.
        results = [process(n, run["id"] if n in numbers else None) for n in registry()]
    elif args.kind == "repository_dispatch":
        if not fallback_authorized(event):
            raise PermissionError("Not a current authorized engineering fallback")
        results = [process(n) for n in registry()]
    elif args.kind == "issues":
        if not wake_authorized(event):
            raise PermissionError("Not an authorized engineering wake")
        results = [process(n) for n in registry()]
    else:
        results = [process(n) for n in registry()]
    if any(x.get("whisper_repair_reserved") is True for x in results):
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as handle:
                handle.write("whisper_repair=true\n")
    print(json.dumps({"schema": "plenum-engineering-controller-v1", "results": results,
                      "paid_inference": False, "merge_authorized": False}, indent=2))


if __name__ == "__main__":
    main()
