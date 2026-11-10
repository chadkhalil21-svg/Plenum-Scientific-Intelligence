"""Least-privilege Hermes-to-EXISTING public GitHub workforce issue bridge.

Separate from Hermes Core, and never accepts private tasks. A scoped owner
token is installed only in the PRIVATE Chief Hermes profile, not in GitHub.
"""
from __future__ import annotations

import json
import os
import re
from urllib.request import Request, build_opener

from .chief_of_staff_pilot import NoRedirects
from .workforce_public_inbox import (
    REPO, OWNER, TITLE, MAGIC_V2, parse_public_issue, PUBLIC_KINDS,
)

BASE = "https://api.github.com"
PREFIX = "https://github.com/" + REPO + "/issues/"


def _read_response(response, *, max_bytes=35000):
    payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ValueError("Unexpected oversized GitHub response")
    return json.loads(payload)


def _request(client, method, url, token, data=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "PlenumHermesPublicIssueBridge/1",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    return Request(url, method=method, data=data, headers=headers)


def _owner_token(token, client):
    if not isinstance(token, str) or not token.strip():
        raise PermissionError("An owner-authorized private GitHub Issues token is required")
    with client.open(_request(client, "GET", BASE + "/user", token), timeout=12) as response:
        info = _read_response(response, max_bytes=10000)
    if info.get("login") != OWNER:
        raise PermissionError("This GitHub token is not authenticated as Plenum's founder")
    return True


def create_public_assignment(kind: str, objective: str, *, token: str,
                             opener=None) -> dict:
    """One allowed PUBLIC issue; real GitHub checks the founder's identity."""
    if kind not in PUBLIC_KINDS:
        raise ValueError("Private or unsupported task type")
    if not isinstance(objective, str):
        raise ValueError("Public task title required")
    body = MAGIC_V2 + "\nkind: " + kind + "\nobjective: " + objective.strip()
    event = {"action": "opened", "repository": {"full_name": REPO},
             "issue": {"user": {"login": OWNER}, "title": TITLE,
                       "body": body, "number": 1}}
    parsed = parse_public_issue(event)
    client = opener or build_opener(NoRedirects)
    _owner_token(token, client)
    data = json.dumps({"title": TITLE, "body": body}).encode("utf-8")
    with client.open(_request(
        client, "POST", BASE + "/repos/" + REPO + "/issues", token, data
    ), timeout=12) as response:
        if response.status != 201:
            raise RuntimeError("GitHub did not create the approved public task")
        result = _read_response(response)
    number = result.get("number")
    if (not isinstance(number, int) or not 0 < number < 10**9
            or result.get("html_url") != PREFIX + str(number)):
        raise RuntimeError("GitHub task final-state identity not verified")
    return {"state": "FOUNDER_PUBLIC_ISSUE_CREATED",
            "kind": parsed["kind"], "issue_number": number,
            "issue_url": PREFIX + str(number),
            "note": "A GitHub Actions worker is now eligible to run; "
                    "not proof the work finished. Check this issue for its verified status."}


def read_public_assignment(issue_number: int, *, token: str,
                           opener=None) -> dict:
    """Return only the previous public workforce-status comment, never full issue text."""
    if (not isinstance(issue_number, int)
            or not 0 < issue_number < 10**9):
        raise ValueError("Invalid public issue number")
    client = opener or build_opener(NoRedirects)
    _owner_token(token, client)
    uri = BASE + "/repos/" + REPO + "/issues/" + str(issue_number) + "/comments?per_page=100"
    with client.open(_request(client, "GET", uri, token), timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("GitHub status read unavailable")
        comments = _read_response(response, max_bytes=100000)
    if not isinstance(comments, list):
        raise RuntimeError("Unexpected GitHub comments format")
    statuses = ("DRAFT_READY_FOR_FOUNDER", "BLOCKED_WORKER_FAILED",
                "BLOCKED_WORKER_UNAVAILABLE", "BLOCKED_VERIFICATION",
                "BLOCKED_NO_SOURCE_EVIDENCE", "BLOCKED_WORKER_OR_VERIFICATION")
    verified = []
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        actor = (comment.get("user") or {}).get("login")
        text = comment.get("body") or ""
        if actor != "github-actions[bot]" or not text.startswith(
            "<!-- plenum-public-workforce-run:"
        ):
            continue
        status = next((x for x in statuses if "Status: **" + x + "**" in text), None)
        if status:
            verified.append(status)
    return {"issue_url": PREFIX + str(issue_number),
            "status": verified[-1] if verified else "NO_WORKFORCE_RESULT_YET",
            "verified_as": "public_workflow_bot_comment_only",
            "private_or_full_issue_content_returned": False}
