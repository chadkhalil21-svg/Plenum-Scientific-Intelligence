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
from pathlib import Path
from urllib.request import Request, urlopen

from .chief_team_mission import MISSION_TITLE, parse_mission
from .workforce_public_inbox import REPO, OWNER, TITLE, parse_public_issue

API = "https://api.github.com/repos/" + REPO
RECOVERY_MAGIC = "<!-- plenum-minister-missed-dispatch:"
FIRST_ELIGIBLE_UTC = datetime(2026, 11, 13, tzinfo=timezone.utc)
MIN_ISSUE_AGE = timedelta(minutes=65)
MAX_ISSUES_PER_RUN = 2
MAX_RESPONSE = 1_000_000


def original_issue_eligible(issue: object, *, now: datetime) -> bool:
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
    if (created.tzinfo is None or created < FIRST_ELIGIBLE_UTC
            or created + MIN_ISSUE_AGE > now):
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
    for issue in items:
        if len(dispatched) >= MAX_ISSUES_PER_RUN:
            break
        if not original_issue_eligible(issue, now=now):
            continue
        number = issue["number"]
        comments = request_json(
            API + f"/issues/{number}/comments?per_page=100", token)
        if not missing_original_attempt(comments, number):
            continue
        request_json(API + "/dispatches", token, method="POST",
                     payload={
                         "event_type": "plenum_public_issue_wakeup",
                         "client_payload": {"issue_number": number},
                     })
        # The original source dispatcher will still independently check
        # founder identity, exact public envelope, and completed bot receipts.
        # Record one durable wake-attempt marker on the SAME original issue.
        request_json(API + f"/issues/{number}/comments", token, method="POST",
                     payload={"body": (
                         RECOVERY_MAGIC + str(number) + " -->\n"
                         "Original Minister found no recorded original public "
                         "execution 65+ minutes after issue creation. Requested "
                         "ONE existing GitHub public specialist wake. "
                         "This is dispatch only, NOT completed work or private access."
                     )})
        dispatched.append(number)
    return {
        "schema": "plenum-original-minister-missed-public-issue-recovery-v1",
        "status": ("REQUESTED_EXISTING_PUBLIC_WORKER_WAKES" if dispatched
                   else "NO_NEW_MISSED_PUBLIC_MISSION"),
        "original_issues_woken": dispatched,
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
          + " original_public_issues=" + str(report["original_issues_woken"]))


if __name__ == "__main__":
    main()
