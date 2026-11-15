"""Original Minister: catch up on genuine missed owner public issue dispatches.

This runs in the EXISTING Plenum Minister's Github Actions job. It NEVER
creates missions, chooses unrelated backlog work, executes private tasks, or
claims any model is resident. It only reawakens a NEW, still-unattempted,
explicitly founder-authored PUBLIC mission through the EXISTING same-repo
repository_dispatch worker, at most two per run and once per issue.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
import os
import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .chief_team_mission import MISSION_TITLE, parse_mission
from .workforce_public_inbox import REPO, OWNER, TITLE, parse_public_issue

API = "https://api.github.com/repos/" + REPO
RECOVERY_MAGIC = "<!-- plenum-minister-missed-dispatch:"
FIRST_ELIGIBLE_UTC = datetime(2026, 11, 13, tzinfo=timezone.utc)
# Historic founder issues must be separately opted in on the SAME issue.
# We never sweep the entire old backlog just because it has no bot comment.
LEGACY_EARLIEST_UTC = datetime(2026, 11, 10, tzinfo=timezone.utc)
LEGACY_OWNER_APPROVAL = "<!-- plenum-minister-legacy-public-backlog-v1 -->"
MIN_ISSUE_AGE = timedelta(minutes=65)
MAX_ISSUES_PER_RUN = 2
MAX_RESPONSE = 1_000_000
# Reuse native GitHub Actions rerun after the original Free Worker AI day rolls over.
# This is not a new agent, scheduler, paid fallback, or permission for broad retries.
CODER_TITLE = "[Plenum OpenHands] public repair"
CODER_WORKFLOW = ".github/workflows/business-workforce-runtime.yml"
CODER_WORKFLOW_ID = 412824880  # Original live #733 authenticated run.
CODER_STATUS = "BLOCKED_LOCAL_FREE_AI_DAILY_CAP_NO_SAME_DAY_RETRY"
CODER_RESERVATION = "<!-- plenum-minister-nextday-free-coder:"
CODER_EXECUTION = "<!-- plenum-openhands-execution-reserved:"
CODER_TERMINAL = "<!-- plenum-openhands-review:"
CODER_RECEIPT = re.compile(
    r"^<!-- plenum-openhands-review:([1-9][0-9]{0,12}):attempt:([1-9][0-9]?) -->\n"
    r"\*\*(OpenHands original public repair|Aider local original public repair): ([A-Z0-9_]+)\*\*",
    re.MULTILINE,
)


def _utc_datetime(value: object):
    if not isinstance(value, str):
        return None
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return date.astimezone(timezone.utc) if date.tzinfo else None



def _coder_bot_bodies(comments: object) -> list[str]:
    """Only bounded, authenticated bot comment history authorizes a coding action."""
    if not isinstance(comments, list) or len(comments) >= 100:
        raise ValueError("Unbounded original coding comment history")
    bodies = []
    for item in comments:
        if not isinstance(item, dict) or not isinstance(item.get("body", ""), str):
            raise ValueError("Malformed original coding comment history")
        if (item.get("user") or {}).get("login") == "github-actions[bot]":
            bodies.append(item.get("body", ""))
    return bodies


def _coder_execution_marker(run_id: int, attempt: int) -> str:
    return f"{CODER_EXECUTION}{run_id}:attempt:{attempt} -->"


def has_original_coder_terminal_receipt(comments: object, run_id: int, attempt: int) -> bool:
    """An untrusted public comment cannot suppress the authentic terminal receipt."""
    marker = f"{CODER_TERMINAL}{run_id}:attempt:{attempt} -->"
    legacy = f"{CODER_TERMINAL}{run_id} -->"
    return any(body.splitlines()[:1] == [marker]
               or (attempt == 1 and body.splitlines()[:1] == [legacy])
               for body in _coder_bot_bodies(comments))


def _original_coder_run_matches(run: object, run_id: int, now: datetime) -> bool:
    return (isinstance(run, dict)
            and run.get("id") == run_id
            and run.get("event") == "issues"
            and run.get("workflow_id") == CODER_WORKFLOW_ID
            and run.get("path") == CODER_WORKFLOW
            and run.get("display_title") == CODER_TITLE
            and run.get("head_branch") == "main"
            and run.get("status") == "completed"
            and run.get("conclusion") == "failure"
            and run.get("run_attempt") == 1
            and (run.get("repository") or {}).get("full_name") == REPO
            and (run.get("repository") or {}).get("id") == 1447724141
            and (run.get("actor") or {}).get("login") == OWNER
            and (run.get("actor") or {}).get("id") == 251133044
            and _utc_datetime(run.get("created_at")) is not None
            and _utc_datetime(run["created_at"]).date() < now.astimezone(timezone.utc).date())


def reserve_native_coder(event: dict, token: str, *, run_id: int, attempt: int,
                         now: datetime) -> bool:
    """Reserve the original coding execution before any model/provider access.

    The ORIGINAL coding job already holds the per-issue concurrency group.
    Missing terminal evidence is never permission to invoke the model again.
    A native attempt 2 needs the exact existing Minister next-day reservation,
    first attempt terminal quota receipt and authenticated prior run metadata.
    """
    from .openhands_coding_agent import parse_owner_repair_event
    if (not token or type(run_id) is not int or not 0 < run_id < 10**13
            or type(attempt) is not int or attempt not in (1, 2)
            or now.tzinfo is None):
        return False
    if (not isinstance(event, dict) or (event.get("sender") or {}).get("login") != OWNER):
        raise PermissionError("Only original signed owner coding issues")
    contract = parse_owner_repair_event(event)
    issue = event["issue"]
    number = contract["issue_number"]
    url = API + f"/issues/{number}"
    original = request_json(url, token)
    if (not isinstance(original, dict) or original.get("number") != number
            or original.get("state") != "open" or "pull_request" in original
            or (original.get("user") or {}).get("login") != OWNER
            or original.get("title") != issue.get("title")
            or original.get("body") != issue.get("body")):
        raise PermissionError("Original coding issue closed, changed, or mismatched")
    comments = request_json(url + "/comments?per_page=100", token)
    bodies = _coder_bot_bodies(comments)
    if original.get("comments") not in (None, len(comments)):
        raise ValueError("Original coding comment history changed during reservation")
    relevant = [body for body in bodies
                if any(magic in body for magic in
                       (CODER_EXECUTION, CODER_TERMINAL, CODER_RESERVATION))]
    if attempt == 1:
        if relevant:
            return False
    else:
        nextday = f"{CODER_RESERVATION}{number}:{run_id} -->"
        reservations = [body for body in relevant if CODER_RESERVATION in body]
        if len(reservations) != 1 or reservations[0].splitlines()[:1] != [nextday]:
            return False
        prior_comments = [item for item in comments
                          if not ((item.get("user") or {}).get("login") == "github-actions[bot]"
                                  and item.get("body", "").splitlines()[:1] == [nextday])]
        if free_coder_nextday_candidate(original, prior_comments, now) != run_id:
            return False
        prior_run = request_json(API + f"/actions/runs/{run_id}/attempts/1", token)
        if not _original_coder_run_matches(prior_run, run_id, now):
            return False
    marker = _coder_execution_marker(run_id, attempt)
    result = request_json(url + "/comments", token, method="POST", payload={"body": (
        marker + "\nOriginal owner coding execution reserved before any model access. "
        "No completion claimed; never retry an unknown or unreceipted execution."
    )})
    if (not isinstance(result, dict) or not result.get("html_url")
            or (result.get("user") or {}).get("login") != "github-actions[bot]"
            or result.get("body", "").splitlines()[:1] != [marker]):
        raise RuntimeError("Original coding execution reservation acknowledgment missing")
    return True


def free_coder_nextday_candidate(issue: object, comments: object, now: datetime):
    """Accept only ONE authentic failed original issue-run, from a past UTC day."""
    if (not isinstance(issue, dict) or "pull_request" in issue
            or issue.get("state") != "open"
            or issue.get("title") != CODER_TITLE
            or (issue.get("user") or {}).get("login") != OWNER
            or not isinstance(comments, list) or len(comments) >= 100):
        return None
    number = issue.get("number")
    if type(number) is not int or not 1 <= number < 10**9:
        return None
    from .openhands_coding_agent import parse_owner_repair_event
    try:
        contract = parse_owner_repair_event({
            "action": "opened", "repository": {"full_name": REPO}, "issue": issue,
        })
        if contract.get("engine", "openhands") != "openhands":
            return None  # A local model cannot have this Cloudflare quota receipt.
    except (PermissionError, ValueError, TypeError, OSError):
        return None
    receipts = []
    executions = []
    try:
        _coder_bot_bodies(comments)
    except ValueError:
        return None
    for item in comments:
        body = item.get("body", "")
        # Even an untrusted next-day reservation blocks rather than replays.
        if CODER_RESERVATION in body:
            return None
        if (item.get("user") or {}).get("login") != "github-actions[bot]":
            continue
        if ("Local fallback attempted: true" in body
                or "Gemini fallback attempted: true" in body):
            return None  # Same-job alternate engineering consumed the task.
        if CODER_EXECUTION in body:
            executions.append(body.splitlines()[0])
        match = CODER_RECEIPT.match(body)
        if CODER_TERMINAL in body and match is None:
            return None  # Unknown/legacy coding receipts never authorize a rerun.
        if match:
            receipts.append((int(match[1]), int(match[2]), match[3], match[4],
                             _utc_datetime(item.get("created_at"))))
    if len(receipts) != 1:
        return None
    run_id, attempt, engine_headline, status, recorded = receipts[0]
    if executions not in ([], [_coder_execution_marker(run_id, 1)]):
        return None
    if (attempt != 1 or engine_headline != "OpenHands original public repair"
            or status != CODER_STATUS or recorded is None
            or now.tzinfo is None or recorded.date() >= now.astimezone(timezone.utc).date()
            or now - recorded < timedelta(hours=2)):
        return None
    return run_id


def recover_one_post_reset_original_coder(*, items: list, token: str,
                                          now: datetime, awaiting_receipt=None):
    """One local-budget retry after UTC reset; runs original signed issue context."""
    for issue in items:
        if (not isinstance(issue, dict) or issue.get("state") != "open"
                or issue.get("title") != CODER_TITLE
                or (issue.get("user") or {}).get("login") != OWNER):
            continue
        number = issue.get("number")
        if type(number) is not int or not 1 <= number < 10**9:
            continue
        comments = request_json(API + f"/issues/{number}/comments?per_page=100",
                                token)
        run_id = free_coder_nextday_candidate(issue, comments, now)
        if run_id is None:
            if awaiting_receipt is not None:
                created = _utc_datetime(issue.get("created_at"))
                try:
                    bodies = _coder_bot_bodies(comments)
                except ValueError:
                    bodies = []
                if (created is not None and created + MIN_ISSUE_AGE <= now
                        and not any(CODER_TERMINAL in body for body in bodies)):
                    awaiting_receipt.append(number)
            continue
        run = request_json(API + f"/actions/runs/{run_id}", token)
        if not _original_coder_run_matches(run, run_id, now):
            continue
        # Reserve on the SAME original issue BEFORE a potentially ambiguous
        # dispatch response. Fail closed rather than create duplicate inference.
        request_json(API + f"/issues/{number}/comments", token, method="POST",
                     payload={"body": (
                         f"{CODER_RESERVATION}{number}:{run_id} -->\n"
                         "The original Minister reserved ONE post-UTC-reset "
                         "re-execution of the existing signed GitHub issue run. "
                         "This is NOT evidence the model has completed. "
                         "Never retry this run again automatically."
                     )})
        # The original GitHub service may accept a rerun before the response
        # disappears. Preserve the reservation and report uncertainty, never
        # repeat it or turn a lost response into a confirmed model run.
        evidence = {"issue_number": number, "run_id": run_id,
                    "original_github_run_reused": False, "requested": False,
                    "dispatch_outcome": "AMBIGUOUS_RESERVED_NO_RETRY"}
        try:
            request_json(API + f"/actions/runs/{run_id}/rerun",
                         token, method="POST")
        except (TimeoutError, ConnectionError):
            return evidence
        except URLError as exc:
            if not isinstance(exc.reason, (TimeoutError, ConnectionError)):
                raise
            return evidence
        return {**evidence, "requested": True, "original_github_run_reused": True,
                "dispatch_outcome": "ACCEPTED"}
    return None




def original_issue_eligible(issue: object, *, now: datetime,
                            legacy_approved: bool = False) -> bool:
    if not isinstance(issue, dict) or "pull_request" in issue:
        return False
    num = issue.get("number")
    if (type(num) is not int or not 1 <= num < 10**9
            or issue.get("state") != "open"
            or (issue.get("user") or {}).get("login") != OWNER
            or issue.get("title") not in (MISSION_TITLE, TITLE)):
        return False
    raw_date = issue.get("created_at")
    if not isinstance(raw_date, str):
        return False
    try:
        created = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
    except ValueError:
        return False
    if (created.tzinfo is None or created + MIN_ISSUE_AGE > now
            or created < (LEGACY_EARLIEST_UTC if legacy_approved else FIRST_ELIGIBLE_UTC)):
        return False
    event = {"action": "opened", "repository": {"full_name": REPO},
             "issue": issue}
    try:
        if issue["title"] == MISSION_TITLE:
            parse_mission(event)
        else:
            parse_public_issue(event)
    except (ValueError, PermissionError, KeyError, TypeError):
        return False
    return True


def approved_legacy_public_backlog(issue: object, comments: object,
                                   *, now: datetime) -> bool:
    """One founder-authored approval on the original legacy issue, no blanket sweep.

    This is an OLD, already requested, explicitly PUBLIC task that has never
    left a bot receipt. Owner approval is a comment from the ORIGINAL GitHub
    owner, not untrusted issue body text, task title, or external webpage.
    """
    if not isinstance(issue, dict) or not isinstance(comments, list):
        return False
    created = _utc_datetime(issue.get("created_at"))
    if (created is None or created >= FIRST_ELIGIBLE_UTC
            or issue.get("comments") not in (None, len(comments))
            or not original_issue_eligible(issue, now=now, legacy_approved=True)):
        return False
    approvals = [
        comment for comment in comments if isinstance(comment, dict)
        and (comment.get("user") or {}).get("login") == OWNER
        and isinstance(comment.get("body"), str)
        and comment["body"].splitlines()[0:1] == [LEGACY_OWNER_APPROVAL]
    ]
    return len(approvals) == 1


def missing_original_attempt(comments: object, issue_number: int) -> bool:
    """Do not wake any existing attempt, including a FAILED old attempt."""
    if not isinstance(comments, list) or len(comments) >= 100:
        return False
    for comment in comments:
        if not isinstance(comment, dict):
            return False
        body = comment.get("body", "")
        user = (comment.get("user") or {}).get("login")
        if not isinstance(body, str):
            return False
        if (user == "github-actions[bot]" and (
                "<!-- plenum-founder-chief-run:" in body
                or "<!-- plenum-public-workforce-run:" in body
                or "**Chief status:" in body
                or "Status: **" in body
                or RECOVERY_MAGIC in body)):
            return False
        if (RECOVERY_MAGIC + str(issue_number) + " -->") in body:
            return False
    return True


def request_json(url: str, token: str, *, method="GET", payload=None):
    if not (url.startswith(API + "/") or url == API + "/dispatches"):
        raise PermissionError("Only the ORIGINAL repository may be contacted")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PlenumExistingMinisterMissedPublicIssue/1",
    })
    with urlopen(request, timeout=18) as response:
        raw = response.read(MAX_RESPONSE + 1)
        status = response.status
    if len(raw) > MAX_RESPONSE:
        raise ValueError("Unbounded GitHub public evidence response")
    if method == "POST" and url == API + "/dispatches":
        if status != 204:
            raise RuntimeError("Original GitHub dispatch not accepted")
        return None
    if (method == "POST" and
            re.fullmatch(re.escape(API) + r"/actions/runs/[1-9][0-9]*/rerun", url)):
        if status != 201:
            raise RuntimeError("Original GitHub Action rerun not accepted")
        return None
    if status not in (200, 201):
        raise RuntimeError("GitHub evidence request was not accepted")
    return json.loads(raw)


def resume_missed_public_issues(*, token: str, now: datetime) -> dict:
    if not token:
        raise ValueError("Missing original ephemeral GitHub token")
    items = request_json(
        API + "/issues?state=open&sort=created&direction=desc&per_page=100",
        token,
    )
    if not isinstance(items, list):
        raise ValueError("Invalid original issue list")
    # If pagination might hide older issues, do not widen or invent work.
    # Descending creation order prioritizes the youngest eligible tasks.
    dispatched = []
    ambiguous = []
    for issue in items:
        if len(dispatched) + len(ambiguous) >= MAX_ISSUES_PER_RUN:
            break
        fresh = original_issue_eligible(issue, now=now)
        legacy = (not fresh and isinstance(issue, dict)
                  and issue.get("comments", 0) in (0, 1, 2)
                  and original_issue_eligible(issue, now=now,
                                              legacy_approved=True))
        if not fresh and not legacy:
            continue
        number = issue["number"]
        comments = request_json(
            API + f"/issues/{number}/comments?per_page=100", token)
        if (legacy and not approved_legacy_public_backlog(
                issue, comments, now=now)):
            continue
        if not missing_original_attempt(comments, number):
            continue
        # Reserve FIRST: GitHub may accept a dispatch even if the runner
        # crashes or the network response is lost. A second Minister sweep
        # must never duplicate the original action in that ambiguous state.
        # The original dispatch receiver independently verifies owner,
        # exact public scope and absence of completed bot receipts.
        request_json(API + f"/issues/{number}/comments", token, method="POST",
                     payload={"body": (
                         RECOVERY_MAGIC + str(number) + " -->\n"
                         "Original Minister reserved ONE existing public "
                         "specialist wake for this original owner issue. "
                         "A failed dispatch remains reserved for manual review, "
                         "never silently repeated or claimed completed."
                     )})
        try:
            request_json(API + "/dispatches", token, method="POST",
                         payload={
                             "event_type": "plenum_public_issue_wakeup",
                             "client_payload": {"issue_number": number},
                         })
        except (TimeoutError, ConnectionError):
            # The reservation is already durable. Do not resend the POST;
            # record uncertainty and leave independent eligible work runnable.
            ambiguous.append(number)
            continue
        except URLError as exc:
            # urllib can wrap the same transport failures. Authorization,
            # HTTP errors and unexpected exceptions still stop the sweep.
            if not isinstance(exc.reason, (TimeoutError, ConnectionError)):
                raise
            ambiguous.append(number)
            continue
        dispatched.append(number)
    awaiting_receipt = []
    coder_recovery = recover_one_post_reset_original_coder(
        items=items, token=token, now=now, awaiting_receipt=awaiting_receipt)
    return {
        "schema": "plenum-original-minister-missed-public-issue-recovery-v1",
        "original_coder_recovery": coder_recovery,
        "original_coder_awaiting_authentic_terminal_receipt_no_replay": awaiting_receipt,
        "status": ("PARTIAL_AMBIGUOUS_DISPATCH_RESERVED_NO_RETRY" if ambiguous
                   else "AMBIGUOUS_ORIGINAL_CODER_RERUN_RESERVED_NO_RETRY"
                   if coder_recovery and not coder_recovery["requested"]
                   else "REQUESTED_EXISTING_PUBLIC_WORKER_WAKES" if dispatched
                   else "REQUESTED_EXISTING_ORIGINAL_CODER_RERUN" if coder_recovery
                   else "CODER_TERMINAL_RECEIPT_PENDING_NO_REPLAY" if awaiting_receipt
                   else "NO_NEW_MISSED_PUBLIC_MISSION"),
        "original_issues_woken": dispatched,
        "ambiguous_dispatch_issues": ambiguous,
        "new_agents_created": 0,
        "private_accounts_used": False,
        "persistent_ai_host_claimed": False,
        "charged_provider_used": False,
        "mission_completion_claimed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(
        "reports/minister-missed-public-wake.json"))
    args = parser.parse_args()
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("GITHUB_REPOSITORY") != REPO
            or os.environ.get("GITHUB_EVENT_NAME") != "schedule"):
        raise SystemExit("BLOCKED_NOT_ORIGINAL_SCHEDULED_MINISTER")
    token = os.environ.get("GH_TOKEN", "")
    report = resume_missed_public_issues(
        token=token, now=datetime.now(timezone.utc))
    if (args.out.is_absolute() or len(args.out.parts) > 4
            or args.out.parts[0] != "reports"
            or ".." in args.out.parts):
        raise SystemExit("BLOCKED_UNSAFE_PUBLIC_REPORT_PATH")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", "utf-8")
    print("EXISTING_MINISTER " + report["status"]
          + " original_public_issues=" + str(report["original_issues_woken"])
          + " nextday_coder=" + str(report["original_coder_recovery"]))


if __name__ == "__main__":
    main()
