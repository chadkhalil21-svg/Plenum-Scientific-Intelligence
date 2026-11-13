"""Owner-only PUBLIC project issue re-wake after missed GitHub event.

Exactly the existing Plenum workforce parser and runner are reused.
Never a new model host, private work channel, general task API, or bypass of
GitHub Actions' per-job and acceptable-use limits. Dispatch only when needed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

from .workforce_public_inbox import REPO, OWNER, parse_public_issue, run_issue
from .chief_team_mission import MISSION_TITLE, parse_mission, execute as execute_original_team
from .mission_checkpoint import load_checkpoint, verified_previous_result

MAX_ISSUE = 10 ** 9
BASE = "https://api.github.com/repos/" + REPO + "/issues/"


def checked_issue_number(value):
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value < MAX_ISSUE:
        raise ValueError("Only an existing positive PUBLIC issue ID is allowed")
    return value


def build_original_event(issue: dict, comments: list[dict]) -> dict | None:
    number = checked_issue_number(issue.get("number"))
    if issue.get("state") != "open" or "pull_request" in issue:
        raise PermissionError("Closed or pull request threads cannot wake workers")
    if not isinstance(comments, list) or len(comments) >= 100:
        raise ValueError("Unbounded comment history may hide prior execution")
    event = {
        "action": "opened",
        "repository": {"full_name": REPO},
        "issue": {
            "number": number,
            "title": issue.get("title"),
            "body": issue.get("body"),
            "user": {"login": (issue.get("user") or {}).get("login")}
        }
    }
    if issue.get("title") == MISSION_TITLE:
        parse_mission(event)  # SAME founder/public/two-or-three specialist guards
    else:
        parse_public_issue(event)  # existing single-worker permission gate
    for item in comments:
        if not isinstance(item, dict):
            raise ValueError("Untrusted comment history")
        if ((item.get("user") or {}).get("login") == "github-actions[bot]"
                and ("<!-- plenum-public-workforce-run:" in str(item.get("body", ""))
                     or "<!-- plenum-founder-chief-run:" in str(item.get("body", ""))
                     or "Status: **DRAFT_READY_FOR_FOUNDER**" in str(item.get("body", "")))):
            return None  # Already attempted: no re-running old work
    return event


def gh_json(url: str, token: str, *, body=None):
    if not url.startswith(BASE):
        raise PermissionError("Unexpected remote resource")
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method="POST" if data is not None else "GET",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "PlenumPublicIssueWake/1"
        })
    with urlopen(req, timeout=20) as result:
        if body is not None and result.status != 201:
            raise RuntimeError("GitHub did not acknowledge status comment")
        return json.loads(result.read(140000))



def one_original_local_repair_warranted(event: dict, output_dir: Path,
                                       outcome: dict) -> bool:
    """Only repair the SAME public mission when one previously saved sibling passed.

    The original executor independently verifies that sibling's actual SHA-256
    bytes before treating it as reusable. Never re-execute all specialists.
    """
    if (outcome.get("status") != "BLOCKED_PARTIAL_TEAM"
            or outcome.get("independent_verified") is not False):
        return False
    task = parse_mission(event)
    team = task["team"]
    progress = load_checkpoint(
        output_dir, issue=task["issue_number"],
        objective=task["objective"], team=team,
    )
    if set(progress) != set(team):
        return False
    completed = 0
    incomplete = 0
    for kind in team:
        entry = progress[kind]
        if verified_previous_result(output_dir, kind, entry) is not None:
            completed += 1
        elif (isinstance(entry, dict)
              and entry.get("attempt") == 1
              and entry.get("verified") is False
              and entry.get("status") in (
                  "BLOCKED_WORKER_OR_VERIFICATION",
                  "BLOCKED_ARTIFACT_NOT_PRESERVED",
              )):
            incomplete += 1
        else:
            return False
    return completed >= 1 and incomplete == 1


def process(number: int, token: str, output_dir: Path):
    number = checked_issue_number(number)
    path = BASE + str(number)
    original = gh_json(path, token)
    comments = gh_json(path + "/comments?per_page=100", token)
    event = build_original_event(original, comments)
    if event is None:
        return {"status":"ALREADY_RECORDED", "issue_number":number, "worker_reexecuted":False}
    mission = original.get("title") == MISSION_TITLE
    if mission:
        # Reuse the SAME Chief/team engine and original hashed public artifacts.
        # A wake is only for an original issue whose prior execution is missing.
        outcome = execute_original_team(event, output_dir=output_dir)
        if one_original_local_repair_warranted(event, output_dir, outcome):
            # Same original issue, same output dir, same original Chief,
            # existing checkpoint; the verified sibling is NOT repeated.
            outcome = execute_original_team(event, output_dir=output_dir)
            outcome["same_run_bounded_recovery_attempted"] = True
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"chief-result-{number}.json").write_text(
            json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    else:
        outcome = run_issue(event, output_dir=output_dir)
    run = os.environ["GITHUB_RUN_ID"]
    marker = "<!-- plenum-public-workforce-run:" + run + " -->"
    status = outcome.get("status", "BLOCKED")
    if mission:
        summary = (
            "Original Chief public multi-specialist mission re-woken. "
            "Specialists: " + str(outcome.get("executed_workers", 0))[:4]
            + "; independent verification: "
            + str(outcome.get("independent_verified", False))
            + "; original issue is the same mission. "
        )
    else:
        summary = ("Original Plenum single public worker re-woken. "
                   "Independent scope: "
                   + str(outcome.get("verified_scope", "unverified"))[:170] + ". ")
    body = (marker + "\nStatus: **" + status + "**. " + summary
            + "No authenticated account work or persistent hosting. "
            + "Never re-run completed public tasks.")
    reply = gh_json(path + "/comments", token, body={"body":body})
    if not reply.get("html_url"):
        raise RuntimeError("Missing independently acknowledged issue comment")
    return {"status":status, "issue_number":number, "worker_reexecuted":True,
            "comment_url":reply["html_url"],"public_only":True,
            "original_multi_specialist":mission,
            "independent_verified":outcome.get("independent_verified", False) if mission else outcome.get("verified", False)}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--issue-number", required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args(argv)
    if not args.issue_number.isascii() or not args.issue_number.isdecimal():
        raise ValueError("Issue number must be numeric")
    number = checked_issue_number(int(args.issue_number))
    if not args.execute:
        print(json.dumps({"status":"DRY_RUN","issue_number":number,
                          "github_issues_modified":False}))
        return
    if (os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("GITHUB_EVENT_NAME") != "repository_dispatch"
        or os.environ.get("GITHUB_REPOSITORY") != REPO):
        raise PermissionError("Actual run requires the original GitHub repo dispatch")
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise PermissionError("Scoped GitHub token missing")
    out = process(number, token, Path("reports/public-wake"))
    print(json.dumps(out))
    if out.get("worker_reexecuted") and (
        (out.get("original_multi_specialist")
         and (out.get("status") != "VERIFIED_BOUNDED_TEAM"
              or out.get("independent_verified") is not True))
        or (not out.get("original_multi_specialist")
            and out.get("status") != "DRAFT_READY_FOR_FOUNDER")
    ):
        # An accepted failure receipt and an uploaded artifact do NOT turn a
        # failed public mission into a green Github Actions job.
        raise SystemExit(1)


if __name__ == "__main__":
    main()
