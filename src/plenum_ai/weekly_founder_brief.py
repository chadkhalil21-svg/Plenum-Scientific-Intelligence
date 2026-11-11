"""Low-cost weekly PUBLIC workforce progress brief, using existing GitHub Issues.

Deterministic evidence reader, not an AI CFO or a host for model inference.
Only reads a fixed set of public Plenum issue summaries and posts one bounded
source-linked status comment to the existing Chief queue, at most once per date.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
CHIEF_QUEUE = 432
ISSUES = (
    (310, "Owner-approved signed-in browser"),
    (384, "Persistent free workforce hosting"),
    (428, "Methane funding research"),
    (429, "Methane advisory analysis"),
    (433, "Workforce public research"),
    (435, "Two-specialist Chief mission"),
    (437, "Business Advisory Council"),
    (478, "Six-video Research Engineering Verification receipt"),
    (482, "Scientific evidence reconciliation engineering repair"),
    (483, "Cloudflare Free ingress and quota-capped inference commissioning"),
    (484, "Founder workforce priorities council"),
)
STATUS_RE = re.compile(r"(?:Chief status: |Plenum council status: |Status: \*\*|Overall: )([A-Z_]+)")


def verified_comment_status(comments: list[dict]) -> str:
    """Only original issue comments carry claimed status; do not infer completion."""
    for item in reversed(comments):
        content = item.get("body", "")
        if not isinstance(content, str):
            continue
        match = STATUS_RE.search(content)
        if match:
            return match.group(1)
    return "NO_VERIFIED_RESULT_IN_COMMENTS"


def render_brief(rows: list[dict], *, as_of_date: str) -> str:
    if not re.fullmatch(r"20\d\d-\d\d-\d\d", as_of_date):
        raise ValueError("Require explicit ISO calendar date")
    if {row["number"] for row in rows} != {n for n, _ in ISSUES}:
        raise ValueError("Unreviewed or missing operating evidence set")
    by_id = {r["number"]: r for r in rows}
    lines = [
        f"<!-- plenum-weekly-public-operating-brief:{as_of_date} -->",
        f"## Plenum AI Minister of Operations | public evidence brief — {as_of_date}",
        "A factual status roll-up only; not a live CFO, legal opinion, signed-in website execution or a claim of 24/7 staff.",
        "",
        "### Original source-linked issue status",
    ]
    for n, name in ISSUES:
        item = by_id[n]
        status = item.get("status", "NO_VERIFIED_RESULT_IN_COMMENTS")
        state = item.get("state", "unknown")
        lines.append(
            f"- [{name}](https://github.com/{REPO}/issues/{n}): issue **{state}**; "
            f"last reported status **{status}**."
        )
    lines.extend([
        "",
        "### Founder decisions and remaining dependencies",
        "- Verify a real owner-approved signed-in website task and independent readback under #310; source/CI alone cannot close it.",
        "- Confirm an actual no-new-charge persistent host with resource/capacity evidence under #384 before Paperclip, Hermes and OpenClaw can run continuously.",
        "- Review the Business Advisory Council's *actual* public artifact under #437, compare with qualified human guidance, then authorize only specific next actions.",
        "- Check grant diligence #428/#429 for confirmed facts, partner requirements and decision deadlines; do not assume a budget or award.",
        "- Review accepted specialist artifacts #433/#435; metadata and output structure are not equivalent to independently fact-checked recommendations.",
    "- Review original #478 honestly as 0/6 retrieved captions until new verified source evidence exists; do not count passing CI as transcript completion.",
    "- Route specific research-memory continuity schema fault #482 to Engineering and distinct verification; do not overwrite historical science or whitelabel unknown evidence statuses.",
    "- Cloudflare Free #483 requires genuine owner account and a live original dispatch; eligible hosted inference is capped and not verified connected.",
    "- Use latest original council #484 as advisory only; a model discussion never establishes a running workforce or supplier pricing.",
        "",
        "### Deployment claim boundary",
        "Existing GitHub public worker routes are bounded and verified on actual jobs. Paperclip, Hermes WhatsApp and OpenClaw are not independently established as live services; source-only integrations are not running agents.",
        "",
        "This automation makes no purchases, external messages, private account reads, legal approvals or software deployments.",
    ])
    return "\n".join(lines) + "\n"


def github_json(url: str, token: str, *, method: str = "GET", body=None):
    if not url.startswith(f"https://api.github.com/repos/{REPO}/"):
        raise PermissionError("Only original Plenum GitHub repo may be queried")
    payload = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(
        url, data=payload, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "PlenumMinisterPublicBrief/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(req, timeout=20) as reply:
        return json.loads(reply.read(180000))


def collect_public_evidence(token: str):
    base = f"https://api.github.com/repos/{REPO}/issues/"
    rows = []
    for n, label in ISSUES:
        issue = github_json(base + str(n), token)
        comments = github_json(base + str(n) + "/comments?per_page=100", token)
        if (not isinstance(issue, dict) or issue.get("number") != n
                or not isinstance(comments, list)):
            raise ValueError("Issue readback invalid; do not post inaccurate status")
        rows.append({
            "number": n, "label": label,
            "state": issue.get("state", "unknown"),
            "status": verified_comment_status(comments),
        })
    return rows


def publish_once(token: str, report: str) -> str:
    uri = f"https://api.github.com/repos/{REPO}/issues/{CHIEF_QUEUE}/comments"
    marker = report.splitlines()[0]
    comments = github_json(uri + "?per_page=100", token)
    if not isinstance(comments, list):
        raise ValueError("Cannot independently inspect past Chief reports")
    if any(marker in str(comment.get("body", "")) for comment in comments):
        return "ALREADY_PUBLISHED"
    outcome = github_json(uri, token, method="POST", body={"body": report})
    if not isinstance(outcome, dict) or not outcome.get("html_url"):
        raise ValueError("No independent GitHub acknowledgement of report")
    return outcome["html_url"]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="GitHub Actions original-repo restricted run only")
    parser.add_argument("--out", default="reports/minister-weekly-brief.json")
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.is_absolute() or ".." in out.parts or out.parts[0] != "reports":
        parser.error("Only reports/ output accepted")
    if not args.execute:
        print("OFFLINE_SOURCE_ONLY; run --execute on reviewed original GitHub Actions schedule")
        return
    if (os.getenv("GITHUB_ACTIONS") != "true"
            or os.getenv("GITHUB_REPOSITORY") != REPO
            or os.getenv("GITHUB_EVENT_NAME") not in {"schedule", "workflow_dispatch"}):
        raise PermissionError("No general-purpose CI, model or private host execution")
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise PermissionError("No GitHub Actions scoped issue token")
    rows = collect_public_evidence(token)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = render_brief(rows, as_of_date=stamp)
    url = publish_once(token, report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "schema": "plenum-public-weekly-minister-brief-v1",
        "as_of_utc": stamp, "publication": url,
        "source_issues": [n for n, _ in ISSUES],
        "account_actions": False,
        "private_data_access": False,
        "model_inference_used": False,
        "paperclip_or_whatsapp_activated": False,
    }, indent=2) + "\n", encoding="utf-8")
    print("WEEKLY_PUBLIC_BRIEF " + url)


if __name__ == "__main__":
    main()
