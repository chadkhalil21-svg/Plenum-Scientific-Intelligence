"""Owner-only PUBLIC project issue re-wake after missed GitHub event.

Exactly the existing Plenum workforce parser and runner are reused.
Never a new model host, private work channel, general task API, or bypass of
GitHub Actions' per-job and acceptable-use limits. Dispatch only when needed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.request import Request, urlopen

from .workforce_public_inbox import REPO, OWNER, parse_public_issue, run_issue
from .chief_team_mission import MISSION_TITLE, parse_mission, preflight, execute as execute_original_team
from .mission_checkpoint import load_checkpoint, verified_previous_result

MAX_ISSUE = 10 ** 9
BASE = "https://api.github.com/repos/" + REPO + "/issues/"


def checked_issue_number(value):
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value < MAX_ISSUE:
        raise ValueError("Only an existing positive PUBLIC issue ID is allowed")
    return value


def prior_execution_bodies(number: int, comments: list[dict]) -> list[str]:
    """One existing bot-receipt contract shared by every original issue path."""
    if not isinstance(comments, list) or len(comments) >= 100:
        raise ValueError("Unbounded comment history may hide prior execution")
    recorded = []
    for item in comments:
        if not isinstance(item, dict) or not isinstance(item.get("body", ""), str):
            raise ValueError("Untrusted comment history")
        body = item.get("body", "")
        if ((item.get("user") or {}).get("login") == "github-actions[bot]"
                and ("<!-- plenum-public-workforce-run:" in body
                     or "<!-- plenum-founder-chief-run:" in body
                     or "Status: **DRAFT_READY_FOR_FOUNDER**" in body
                     # A dispatch-only reservation does NOT prove execution.
                     or (f"<!-- plenum-minister-missed-dispatch:{number} -->" in body
                         and "Original public workforce direct wake reserved before execution." in body))):
            recorded.append(body)
    return recorded


def build_original_event(issue: dict, comments: list[dict]) -> dict | None:
    number = checked_issue_number(issue.get("number"))
    if issue.get("state") != "open" or "pull_request" in issue:
        raise PermissionError("Closed or pull request threads cannot wake workers")
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
    if prior_execution_bodies(number, comments):
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


def reserve_native_issue(event: dict, token: str, *, run_id: int, attempt: int,
                         checkpoint: Path | None = None) -> bool:
    """Reserve the first native issue execution, or one exact verified retry.

    Both original native and wake workflows hold the existing per-issue lock.
    No worker/model is invoked before the original GitHub reservation ACK.
    """
    from .chief_workforce_command import CHIEF_TITLE, parse_founder_chief
    if (not token or type(run_id) is not int or not 0 < run_id < 10**13
            or type(attempt) is not int or attempt not in (1, 2)):
        return False
    if (not isinstance(event, dict) or event.get("action") != "opened"
            or (event.get("repository") or {}).get("full_name") != REPO
            or (event.get("sender") or {}).get("login") != OWNER):
        raise PermissionError("Only the original signed owner issue event may execute")
    issue = event.get("issue") or {}
    number = checked_issue_number(issue.get("number"))
    title = issue.get("title")
    if title == MISSION_TITLE:
        parse_mission(event)
    elif title == CHIEF_TITLE:
        parse_founder_chief(event)
    else:
        parse_public_issue(event)
    url = BASE + str(number)
    original = gh_json(url, token)
    if (not isinstance(original, dict) or original.get("number") != number
            or original.get("state") != "open" or "pull_request" in original
            or (original.get("user") or {}).get("login") != OWNER
            or original.get("title") != title or original.get("body") != issue.get("body")):
        raise PermissionError("Original issue closed, changed, or mismatched")
    comments = gh_json(url + "/comments?per_page=100", token)
    bodies = prior_execution_bodies(number, comments)
    if original.get("comments") not in (None, len(comments)):
        raise ValueError("Original comment history changed during reservation")
    first = f"<!-- plenum-public-workforce-run:{run_id}:execution-reserved -->"
    if attempt == 1:
        if bodies:
            return False
        marker = first
    else:
        # Only the ORIGINAL Chief's existing same-run checkpoint retry may
        # resume. A new run, unknown interruption, or missing proof is blocked.
        prior_result = f"<!-- plenum-founder-chief-run:{run_id}:attempt:1 -->"
        if (title != MISSION_TITLE or checkpoint is None
                or sum(body.splitlines()[:1] == [first] for body in bodies) != 1
                or any(body.splitlines()[:1] not in ([first], [prior_result]) for body in bodies)):
            return False
        from .chief_retry_gate import API, github_json, inspect_retry
        old_run = github_json(f"{API}/actions/runs/{run_id}/attempts/1", token)
        if old_run.get("id") != run_id:
            return False
        verdict = inspect_retry({"workflow_run": old_run}, checkpoint, original)
        if verdict.get("status") != "ELIGIBLE_NATIVE_RETRY_ONCE":
            return False
        marker = f"<!-- plenum-public-workforce-run:{run_id}:retry-2-execution-reserved -->"
    reservation = gh_json(url + "/comments", token, body={"body": (
        marker + "\nOriginal native owner issue execution reserved before invoking the worker. "
        "This is not completion; no replay except the original verified same-run checkpoint retry."
    )})
    if not isinstance(reservation, dict) or not reservation.get("html_url"):
        raise RuntimeError("Original native execution reservation acknowledgment missing")
    return True



def one_original_local_repair_warranted(event: dict, output_dir: Path,
                                       outcome: dict) -> bool:
    """Only repair the SAME public mission when one previously saved sibling passed.

    The original executor independently verifies that sibling's actual SHA-256
    bytes before treating it as reusable. Never re-execute all specialists.
    """
    if outcome.get("status") == "BLOCKED_CONTRACT_EXECUTION":
        # The same original contract gate validates the immutable plan,
        # exact prefix and artifact hashes, and permits only attempt one.
        from .chief_retry_gate import inspect_contract_retry
        task = parse_mission(event)
        if not task.get("contract_mission"):
            return False
        try:
            checkpoint = output_dir / f"chief-checkpoint-{task['issue_number']}.json"
            if not checkpoint.is_file() or checkpoint.is_symlink() or checkpoint.stat().st_size > 120_000:
                return False
            state = json.loads(checkpoint.read_text("utf-8"))
            if not isinstance(state, dict):
                return False
            verdict = inspect_contract_retry(output_dir, task, state, outcome, 1)
            return verdict.get("status") == "ELIGIBLE_NATIVE_RETRY_ONCE"
        except (OSError, ValueError, TypeError, KeyError):
            return False
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


def founder_approved_comment_event(payload: object, number: int) -> bool:
    """Verify original GitHub-signed issue_comment envelope, never its prose."""
    from .minister_missed_public_wake import LEGACY_OWNER_APPROVAL
    if not isinstance(payload, dict) or payload.get("action") not in ("created", "edited"):
        return False
    issue, comment = payload.get("issue"), payload.get("comment")
    if not isinstance(issue, dict) or not isinstance(comment, dict):
        return False
    return (issue.get("number") == checked_issue_number(number)
            and issue.get("state") == "open"
            and (issue.get("user") or {}).get("login") == OWNER
            and (comment.get("user") or {}).get("login") == OWNER
            and (payload.get("sender") or {}).get("login") == OWNER
            and isinstance(comment.get("body"), str)
            and comment["body"].splitlines()[:1] == [LEGACY_OWNER_APPROVAL])


def original_chief_worker_extras(scope: dict) -> str | None:
    """The original native Chief and wake share the same dependency selection."""
    if ("public_science" in scope.get("expected_team", [])
            or scope.get("expected_independent_kind") == "public_science"):
        return ".[numerical,orchestration]"
    if scope.get("requires_numerical") is True:
        return ".[numerical]"
    return None


def _read_original_wake_issue(path: str, number: int, token: str):
    original = gh_json(path, token)
    if (not isinstance(original, dict) or original.get("number") != number
            or original.get("state") != "open" or "pull_request" in original
            or (original.get("user") or {}).get("login") != OWNER):
        raise PermissionError("Original wake issue closed, changed, or mismatched")
    comments = gh_json(path + "/comments?per_page=100", token)
    if not isinstance(comments, list) or original.get("comments") not in (None, len(comments)):
        raise PermissionError("Original wake comment history changed during reservation")
    return original, comments


def _direct_owner_marker(original, comments, number):
    from .minister_missed_public_wake import approved_legacy_public_backlog, RECOVERY_MAGIC
    if not approved_legacy_public_backlog(original, comments, now=datetime.now(timezone.utc)):
        raise PermissionError("Original founder legacy public approval missing")
    marker = RECOVERY_MAGIC + str(number) + " -->"
    if any(isinstance(comment, dict)
           and (comment.get("user") or {}).get("login") == "github-actions[bot]"
           and isinstance(comment.get("body"), str)
           and marker in comment["body"] for comment in comments):
        return None
    return marker


def process(number: int, token: str, output_dir: Path, *,
            require_founder_approval: bool = False):
    number = checked_issue_number(number)
    path = BASE + str(number)
    original, comments = _read_original_wake_issue(path, number, token)
    if require_founder_approval:
        # Use the SAME original scheduled Minister reservation marker.
        # GitHub issue_comment can be edited repeatedly, so an ambiguous
        # prior invocation without a completed bot receipt must NOT repeat
        # the original worker or any external source operation.
        marker = _direct_owner_marker(original, comments, number)
        if marker is None:
            return {"status": "ALREADY_RECORDED", "issue_number": number,
                    "worker_reexecuted": False}
    event = build_original_event(original, comments)
    if event is None:
        return {"status":"ALREADY_RECORDED", "issue_number":number, "worker_reexecuted":False}
    mission = original.get("title") == MISSION_TITLE
    expected_team_status = None
    if mission:
        scope = preflight(event)
        if scope.get("planned_model_team_mission") or (scope.get("planned_data_mission") and not scope.get("planned_contract_mission")):
            # Legacy DATA needs the native isolated model setup. The wake
            # has no authorized model host; don't consume execution reservation.
            raise PermissionError("BLOCKED_LEGACY_DATA_REQUIRES_ORIGINAL_NATIVE_MODEL_ROUTE")
        extras = original_chief_worker_extras(scope)
        expected_team_status = ("VERIFIED_BOUNDED_CONTRACT_MISSION"
                                if scope.get("planned_contract_mission")
                                else "VERIFIED_BOUNDED_TEAM")
    else:
        extras = (".[numerical,orchestration]"
                  if parse_public_issue(event)["kind"] == "public_science" else None)
    if extras:
        # Only the original validated public scope selects these fixed extras.
        # Match the native Chief: dependencies are prepared before reservation.
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", extras])
        # Installation may take time. Rebind the exact owner-approved issue
        # and current receipts before consuming the execution reservation.
        current, current_comments = _read_original_wake_issue(path, number, token)
        if current.get("title") != original.get("title") or current.get("body") != original.get("body"):
            raise PermissionError("Original wake issue changed during dependency preparation")
        if build_original_event(current, current_comments) is None:
            return {"status":"ALREADY_RECORDED", "issue_number":number, "worker_reexecuted":False}
        if require_founder_approval and _direct_owner_marker(current, current_comments, number) is None:
            return {"status":"ALREADY_RECORDED", "issue_number":number, "worker_reexecuted":False}
    # Both routes share the workflow's per-issue concurrency group. Record
    # an execution (not dispatch) reservation before invoking either worker.
    # The existing run-marker prefix stops scheduled recovery and later wakes
    # even if this job is canceled before it can post a final receipt.
    run = os.environ["GITHUB_RUN_ID"]
    execution_marker = f"<!-- plenum-public-workforce-run:{run}:execution-reserved -->"
    reservation = gh_json(path + "/comments", token, body={"body": (
        ((marker + "\n") if require_founder_approval else "")
        + execution_marker + "\n"
        "Original public workforce execution reserved before calling the worker. "
        "No further automatic attempt if this run ends ambiguously; "
        "this marker is execution reservation evidence, not task completion."
    )})
    if not reservation.get("html_url"):
        raise RuntimeError("Original wake reservation acknowledgment missing")
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
            "expected_team_status":expected_team_status,
            "independent_verified":outcome.get("independent_verified", False) if mission else outcome.get("verified", False)}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--issue-number", required=True)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--reserve-native-issue", action="store_true")
    args = p.parse_args(argv)
    if not args.issue_number.isascii() or not args.issue_number.isdecimal():
        raise ValueError("Issue number must be numeric")
    number = checked_issue_number(int(args.issue_number))
    if not args.execute:
        print(json.dumps({"status":"DRY_RUN","issue_number":number,
                          "github_issues_modified":False}))
        return
    event_name = os.environ.get("GITHUB_EVENT_NAME")
    if args.reserve_native_issue:
        if (os.environ.get("GITHUB_ACTIONS") != "true" or event_name != "issues"
                or os.environ.get("GITHUB_REPOSITORY") != REPO):
            raise PermissionError("Native reservation requires original GitHub issue event")
        path = Path(os.environ.get("GITHUB_EVENT_PATH", ""))
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 150_000:
            raise PermissionError("Original signed issue event payload unavailable")
        event = json.loads(path.read_text(encoding="utf-8"))
        if (event.get("issue") or {}).get("number") != number:
            raise PermissionError("Native issue ID mismatch")
        approved = reserve_native_issue(
            event, os.environ.get("GH_TOKEN", ""),
            run_id=int(os.environ["GITHUB_RUN_ID"]), attempt=int(os.environ["GITHUB_RUN_ATTEMPT"]),
            checkpoint=Path("reports/workforce-chief"),
        )
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write("authorized=" + str(approved).lower() + "\n")
        print("ORIGINAL_NATIVE_EXECUTION_RESERVED" if approved else "ORIGINAL_NATIVE_EXECUTION_BLOCKED_NO_REPLAY")
        return
    if (os.environ.get("GITHUB_ACTIONS") != "true"
        or event_name not in ("repository_dispatch", "issue_comment")
        or os.environ.get("GITHUB_REPOSITORY") != REPO):
        raise PermissionError("Actual run requires original GitHub event")
    founder_comment = event_name == "issue_comment"
    if founder_comment:
        path = Path(os.environ.get("GITHUB_EVENT_PATH", ""))
        if (not path.is_file() or path.is_symlink()
                or path.stat().st_size > 150_000):
            raise PermissionError("Original GitHub event payload unavailable")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError, OSError):
            raise PermissionError("Invalid signed Github issue event") from None
        if not founder_approved_comment_event(payload, number):
            raise PermissionError("No founder-authorized original issue approval")
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise PermissionError("Scoped GitHub token missing")
    out = process(number, token, Path("reports/public-wake"),
                  require_founder_approval=founder_comment)
    print(json.dumps(out))
    if out.get("worker_reexecuted") and (
        (out.get("original_multi_specialist")
         and (out.get("status") != out.get("expected_team_status")
              or out.get("expected_team_status") not in (
                  "VERIFIED_BOUNDED_TEAM", "VERIFIED_BOUNDED_CONTRACT_MISSION")
              or out.get("independent_verified") is not True))
        or (not out.get("original_multi_specialist")
            and out.get("status") != "DRAFT_READY_FOR_FOUNDER")
    ):
        # An accepted failure receipt and an uploaded artifact do NOT turn a
        # failed public mission into a green Github Actions job.
        raise SystemExit(1)


if __name__ == "__main__":
    main()
