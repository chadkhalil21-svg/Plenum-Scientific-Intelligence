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
    (310, "Founder-retired custom browser"),
    (384, "Persistent free workforce hosting"),
    (428, "Methane funding research (public diligence complete)"),
    (429, "Methane advisory analysis (public review complete)"),
    (433, "Workforce public research"),
    (435, "Two-specialist Chief mission"),
    (437, "Business Advisory Council"),
    (478, "Six-video Research Engineering Verification receipt"),
    (482, "Scientific evidence reconciliation (original repair accepted)"),
    (483, "Cloudflare signed wake and private memory (bounded accepted)"),
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
        reason = item.get("state_reason")
        closure = f" ({reason})" if state == "closed" and reason in ("completed", "not_planned") else ""
        lines.append(
            f"- [{name}](https://github.com/{REPO}/issues/{n}): issue **{state}{closure}**; "
            f"last reported status **{status}**."
        )
    lines.extend([
        "",
        "### Founder decisions and remaining dependencies",
        "- FOUNDER OVERRIDE (14 Nov 2026): the custom Plenum browser #310 is RETIRED as NOT PLANNED. Never resume custom browser builds, owner session setup, deployments, acceptance checks or related login work. Existing authorized ChatGPT Work/connected provider tools and, if needed, metered TinyFish with existing credits are the web-task route.",
        "- Complete ACTUAL new founder-authorized work using existing Research, Engineering, Commercial, Global Intelligence and Verification specialists; independent provider readback and retrievable outcomes are mandatory. Do not count source catalogs, stale drafts or recurring reports as work.",
        "- Persistent host #384 is still UNVERIFIED for a no-new-charge private workforce; keep the original bounded event-driven GitHub/Cloudflare system and defer Paperclip/Hermes service installation without eligible host and privacy permissions.",
        "- Funding source diligence #428 and advisory review #429 are already delivered; do not rerun their public research. Separate founder-approved application work from a research brief and consult private correspondence privately when authorized.",
        "- Original scientific evidence reconciliation #482 was independently accepted (PR #486 / real original reconciliation run); do not reclassify it as unstarted or repeat its old test.",
        "- Cloudflare signed memory under #483 was accepted for the narrow actual owner read/write and fresh-session readback; it is NOT a guarantee of automatic recall in every ChatGPT conversation.",
        "- Preserve the original #478 six-video caption failures; do not replay the same blocked YouTube/Jina paths. Work only from new lawfully accessible original audio/document inputs.",
        "- Source-only agent frameworks are not independent live employees. The existing five divisions need useful verified results, interruption recovery without duplicate effects, and accurate free-tier accounting.",
        "",
        "### Deployment claim boundary",
        "Existing GitHub public workers have proven bounded actual tasks. Paperclip, Hermes WhatsApp and OpenClaw are not established as live private persistent services. The custom browser is founder-retired, not independently passed.",
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
        # GitHub issue comment lists can exceed 180 KB. Never parse a
        # silently truncated JSON prefix or mistake it for missing evidence.
        raw = reply.read(4_000_001)
    if len(raw) > 4_000_000:
        raise ValueError("Original GitHub response exceeds bounded audit limit")
    return json.loads(raw)


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
            "state_reason": issue.get("state_reason"),
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
