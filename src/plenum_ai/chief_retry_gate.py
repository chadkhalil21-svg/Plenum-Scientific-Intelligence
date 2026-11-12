"""One safe native GitHub retry for the original public Chief mission only.

This is a privileged workflow_run gate. Never execute downloaded artifact code.
Read bounded JSON/actual public file hashes and bind the evidence to the original
founder issue before allowing GitHub's native failed-job retry once.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from .mission_checkpoint import artifact_digest, objective_digest, verified_previous_result

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"
WORKFLOW = "Plenum Chief | Founder Model-Directed Specialist Command"
API = "https://api.github.com/repos/" + REPO
KINDS = {"public_research", "public_program", "public_science", "public_creative"}
MAX_JSON = 120_000


def eligible_run(event: object) -> int | None:
    w = event.get("workflow_run") if isinstance(event, dict) else None
    if not isinstance(w, dict):
        return None
    if (w.get("name") != WORKFLOW or w.get("event") != "issues"
            or w.get("status") != "completed" or w.get("conclusion") != "failure"
            or w.get("run_attempt") != 1
            or (w.get("actor") or {}).get("login") != OWNER
            or (w.get("repository") or {}).get("full_name") != REPO
            or type(w.get("id")) is not int or w["id"] < 1):
        return None
    return w["id"]


def inspect_retry(event: object, root: Path, issue: object) -> dict:
    """Retain completed sibling; permit exactly one failed first-attempt sibling."""
    run_id = eligible_run(event)
    if run_id is None or not root.is_dir() or not isinstance(issue, dict):
        return {"status": "BLOCKED_INELIGIBLE_RUN"}
    number = issue.get("number")
    body = issue.get("body")
    if (type(number) is not int or not 0 < number < 10**9
            or issue.get("state") != "open"
            or (issue.get("user") or {}).get("login") != OWNER
            or issue.get("title") != "[Plenum Chief] public mission"
            or not isinstance(body, str)
            or not body.startswith("PLENUM_CHIEF_PUBLIC_MISSION_V1\nobjective: ")
            or len(body.splitlines()) != 2):
        return {"status": "BLOCKED_NOT_FOUNDER_PUBLIC_MISSION"}
    checkpoint_file = root / f"chief-checkpoint-{number}.json"
    result_file = root / f"chief-result-{number}.json"
    for f in (checkpoint_file, result_file):
        if not f.is_file() or f.is_symlink() or f.stat().st_size > MAX_JSON:
            return {"status": "BLOCKED_MISSING_OR_UNSAFE_CHECKPOINT"}
    try:
        cp = json.loads(checkpoint_file.read_text("utf-8"))
        report = json.loads(result_file.read_text("utf-8"))
    except (ValueError, OSError, UnicodeError):
        return {"status": "BLOCKED_INVALID_JSON"}
    team = cp.get("team")
    results = cp.get("results")
    if (not isinstance(team, list) or len(team) not in (2, 3)
            or len(set(team)) != len(team)
            or any(kind not in KINDS for kind in team)
            or not isinstance(results, dict) or set(results) != set(team)
            or cp.get("schema") != "plenum-chief-restart-v1"
            or cp.get("issue_number") != number
            or cp.get("objective_sha256") != objective_digest(body.splitlines()[1][11:])
            or cp.get("only_original_public_workers") is not True
            or cp.get("owner_private_accounts_used") is not False
            or report.get("issue_number") != number
            or report.get("mode") != "multi"
            or report.get("expected_team") != team
            or report.get("status") != "BLOCKED_PARTIAL_TEAM"
            or report.get("independent_verified") is not False):
        return {"status": "BLOCKED_UNRELATED_OR_COMPLETED_WORK"}
    done, unfinished = 0, 0
    for kind in team:
        entry = results[kind]
        if verified_previous_result(root, kind, entry) is not None:
            done += 1
        elif (not isinstance(entry, dict)
              or entry.get("status") not in {
                  "BLOCKED_WORKER_OR_VERIFICATION", "BLOCKED_ARTIFACT_NOT_PRESERVED"}
              or entry.get("verified") is True or entry.get("attempt") != 1):
            return {"status": "BLOCKED_UNSAFE_RETRY_HISTORY"}
        else:
            unfinished += 1
    if done < 1 or unfinished != 1:
        return {"status": "BLOCKED_NOT_ONE_REPAIRABLE_WORKER"}
    return {"status": "ELIGIBLE_NATIVE_RETRY_ONCE", "run_id": run_id,
            "issue_number": number, "saved_verified_workers": done}


def github_json(url: str, token: str) -> dict:
    req = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PlenumOriginalChiefSafeRetry/1",
    })
    with urlopen(req, timeout=15) as response:
        body = response.read(MAX_JSON + 1)
    if len(body) > MAX_JSON:
        raise ValueError("Unbounded GitHub response")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("Expected GitHub object")
    return data


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--event", required=True, type=Path)
    p.add_argument("--artifact-dir", required=True, type=Path)
    args = p.parse_args()
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("GITHUB_REPOSITORY") != REPO
            or os.environ.get("GITHUB_EVENT_NAME") != "workflow_run"):
        raise SystemExit("BLOCKED_NOT_ORIGINAL_GITHUB_RUNTIME")
    event = json.loads(args.event.read_text("utf-8"))
    run_id = eligible_run(event)
    if run_id is None:
        print("BLOCKED_INELIGIBLE_RUN")
        return
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("BLOCKED_SCOPED_TOKEN_MISSING")
    checkpoints = list(args.artifact_dir.glob("chief-checkpoint-*.json"))
    if len(checkpoints) != 1:
        print("BLOCKED_MISSING_UNIQUE_CHECKPOINT")
        return
    issue_id = checkpoints[0].stem.removeprefix("chief-checkpoint-")
    if not issue_id.isdecimal() or len(issue_id) > 9:
        print("BLOCKED_INVALID_ORIGINAL_ISSUE_ID")
        return
    issue = github_json(f"{API}/issues/{int(issue_id)}", token)
    permission = inspect_retry(event, args.artifact_dir, issue)
    if permission["status"] != "ELIGIBLE_NATIVE_RETRY_ONCE":
        print(permission["status"])
        return
    live = github_json(f"{API}/actions/runs/{run_id}", token)
    if (live.get("run_attempt") != 1 or live.get("status") != "completed"
            or live.get("conclusion") != "failure"
            or live.get("event") != "issues"):
        print("BLOCKED_ORIGINAL_RUN_ALREADY_CHANGED")
        return
    req = Request(f"{API}/actions/runs/{run_id}/rerun-failed-jobs",
        method="POST", data=b"{}", headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PlenumOriginalChiefSafeRetry/1",
        })
    with urlopen(req, timeout=15) as response:
        if response.status not in (201, 202):
            raise RuntimeError("GitHub rejected native original failed-job rerun")
    print("REQUESTED_ONE_NATIVE_RETRY original_run=" + str(run_id)
          + " original_issue=" + str(permission["issue_number"])
          + " saved_verified_workers=" + str(permission["saved_verified_workers"]))


if __name__ == "__main__":
    main()
