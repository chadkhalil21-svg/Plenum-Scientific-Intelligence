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
}
SHA = re.compile(r"^[a-f0-9]{40}$")
MARKER = "<!-- plenum-engineering-controller-v1:"
MAX_BYTES = 2_000_000
RECEIPT_ISSUE = 432
# One audited repair recipe, bound to original failed public development run.
WHISPER_REPAIR_RUN = 45767285022
WHISPER_REPAIR_HEAD = "a9ed286a49308fb5e01ed25a53c08f65e72445af"
WHISPER_REPAIR_JOB = 139731117752


def number(x):
    return type(x) is int and 0 < x < 10**13


def authorized_pr(pr, n):
    if n not in REGISTERED or not isinstance(pr, dict):
        return False
    branch, _, _ = REGISTERED[n]
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
    branch, workflow, _ = REGISTERED[n]
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
    if run["conclusion"] == "success":
        return {"status": "AWAIT_INDEPENDENT_EVIDENCE"}
    if run["conclusion"] != "failure":
        return {"status": "STOP_NON_SUCCESS"}
    _, _, name = REGISTERED[n]
    matches = [j for j in jobs if isinstance(j, dict) and j.get("name") == name]
    if len(matches) != 1:
        return {"status": "BLOCKED_JOB_IDENTITY"}
    job = matches[0]
    steps = job.get("steps")
    if (job.get("run_id") != run["id"] or job.get("head_sha") != run["head_sha"]
            or job.get("conclusion") != "failure" or not number(job.get("id"))
            or not isinstance(steps, list) or not steps):
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
    if not eligible_run(fresh, n, latest) or latest["run_attempt"] != run["run_attempt"] or latest["conclusion"] != run["conclusion"]:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--kind", choices=("workflow_run", "schedule", "workflow_dispatch"), required=True)
    args = parser.parse_args()
    if os.getenv("GITHUB_REPOSITORY") != REPO:
        raise PermissionError("Wrong repository")
    event = json.loads(Path(args.event).read_text())
    if args.kind == "workflow_run":
        run = event.get("workflow_run", {})
        if not number(run.get("id")) or (run.get("repository") or {}).get("full_name") != REPO:
            return
        numbers = [n for n, row in REGISTERED.items() if row[1] == run.get("name") and row[0] == run.get("head_branch")]
        results = [process(n, run["id"]) for n in numbers]
    else:
        results = [process(n) for n in REGISTERED]
    if any(x.get("whisper_repair_reserved") is True for x in results):
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as handle:
                handle.write("whisper_repair=true\n")
    print(json.dumps({"schema": "plenum-engineering-controller-v1", "results": results,
                      "paid_inference": False, "merge_authorized": False}, indent=2))


if __name__ == "__main__":
    main()
