"""Independent bounded reporting over the EXISTING free public-caption research worker.

Research retrieves; Engineering diagnoses retrieval vs software state; a separate
Verifier checks the evidence envelope and issues the sole founder receipt.
No new model, private accounts, paid service, or fabricated video transcript.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

from . import youtube_public_caption_worker as research

ENGINEERING_OUT = "reports/youtube-research/engineering-diagnosis.json"
VERIFICATION_OUT = "reports/youtube-research/director-verification.json"
REQUIRED = ("VR35PxCFZIQ", "LqVJORn7ogE", "fCHe_fOqlYA",
            "9Hwanevuhd8", "MvJeDME7NN8", "GMcLy4Gn7GU")


def read_founder_task(event: dict) -> tuple[int, list[str]]:
    issue = event.get("issue") or {}
    if (event.get("action") != "opened"
        or (event.get("repository") or {}).get("full_name") != research.REPO
        or (issue.get("user") or {}).get("login") != research.OWNER
        or issue.get("title") != research.TITLE
        or not isinstance(issue.get("number"), int)
        or not isinstance(issue.get("body"), str)):
        raise PermissionError("Not a real founder-issued original public caption job")
    lines = issue["body"].splitlines()
    if len(lines) != 2 or lines[0] != research.MARKER or not lines[1].startswith("videos: "):
        raise ValueError("Unexpected task envelope")
    ids = lines[1][8:].split(",")
    if not 1 <= len(ids) <= 6 or len(set(ids)) != len(ids) or any(x not in REQUIRED for x in ids):
        raise ValueError("Unreviewed public video requested")
    return issue["number"], ids


def load_if_present(path):
    file = Path(path)
    if not file.is_file():
        return None
    if file.is_symlink() or file.stat().st_size > 130000:
        raise ValueError("Unbounded or linked work artifact")
    return json.loads(file.read_text(encoding="utf-8"))


def engineering_diagnosis(report, ids):
    """An actual role-specific diagnostic, not a new pretend autonomous model."""
    outcomes = report.get("outcomes", []) if isinstance(report, dict) else []
    matched = isinstance(outcomes, list) and [x.get("id") for x in outcomes if isinstance(x, dict)] == ids
    attempts = sum(bool(x.get("fallback_attempted")) for x in outcomes if isinstance(x, dict))
    retrieved = sum(x.get("status") == "CAPTIONS_RETRIEVED" for x in outcomes if isinstance(x, dict))
    failure_classes = sorted(set(str(x.get("fallback_failure_type") or x.get("failure_type") or "")
                                 for x in outcomes if isinstance(x, dict) and x.get("status") != "CAPTIONS_RETRIEVED"))
    return {
        "role": "Engineering Director",
        "source_reuse": "original YouTube worker plus merged free Jina fallback PR #474",
        "existing_worker_integrated": callable(research.review_video) and callable(research.fetch_public_jina_captions),
        "original_issue_video_ids_match": matched,
        "videos_requested": len(ids),
        "videos_retrieved_reported_not_independently_certified": retrieved,
        "fallback_attempts_reported": attempts,
        "failure_classes": [s[:80] for s in failure_classes if s],
        "status": "SOURCE_OR_PROVIDER_BLOCKED" if matched and retrieved == 0 else (
            "RETRIEVAL_REQUIRES_INDEPENDENT_REVIEW" if matched else "MISSING_OR_MALFORMED_EVIDENCE"),
        "new_spending_authorized": False,
        "additional_automatic_retries": 0,
    }


def audit(report, engineering, ids, catalog):
    """Independent schema/lineage review; NEVER a false claim of source re-fetch."""
    outcome = {
        "role": "Independent Verifier", "research_role": "Research Director",
        "engineering_role": "Engineering Director",
        "chief_accountable": "Existing Plenum Chief of Staff",
        "requested": len(ids), "retrieved": 0, "status": "BLOCKED",
        "evidence_integrity": "NOT_VERIFIED",
        "independent_original_caption_retrieval": False,
        "all_videos_watched": False, "full_transcripts_saved": False,
        "free_public_only": True, "next_owner": "Engineering Director",
    }
    try:
        if (not isinstance(report, dict)
            or report.get("schema") != "plenum-free-captions-six-video-v1"
            or report.get("requested") != len(ids)
            or report.get("text_or_audio_saved") is not False
            or report.get("private_account_access") is not False
            or report.get("paid_inference_used") is not False
            or report.get("full_visual_playback_claimed") is not False):
            raise ValueError("Unexpected worker evidence envelope")
        entries = report.get("outcomes")
        if not isinstance(entries, list) or len(entries) != len(ids):
            raise ValueError("Missing original video outcomes")
        total = 0
        for video_id, item in zip(ids, entries):
            if not isinstance(item, dict) or item.get("id") != video_id:
                raise ValueError("Original video identity or ordering mismatch")
            original = catalog[video_id]
            if (item.get("title") != original["title"]
                or item.get("url") != "https://www.youtube.com/watch?v=" + video_id
                or item.get("caption_text_saved") is not False):
                raise ValueError("Source metadata or transcript storage claim changed")
            got = item.get("status") == "CAPTIONS_RETRIEVED"
            if item.get("status") not in ("CAPTIONS_RETRIEVED", "CAPTION_UNAVAILABLE"):
                raise ValueError("Unknown capture status")
            if item.get("captions_read") is not got:
                raise ValueError("Caption claims contradict status")
            n = item.get("caption_segments_count")
            if not isinstance(n, int) or not (8 <= n <= 5000 if got else n == 0):
                raise ValueError("Unsubstantiated segments")
            platforms = item.get("platforms")
            expected = original["platforms"]
            if not isinstance(platforms, list) or len(platforms) != len(expected):
                raise ValueError("Unreviewed platform inventory")
            found = 0
            for p, ref in zip(platforms, expected):
                if not isinstance(p, dict) or (p.get("name"), p.get("category")) != (ref["name"], ref["category"]):
                    raise ValueError("Platform mismatch")
                stamps = p.get("timestamps_seconds")
                if (not isinstance(stamps, list) or len(stamps) > 3
                    or any(not isinstance(t, int) or isinstance(t, bool) or not 0 <= t <= 86400 for t in stamps)
                    or p.get("found_in_caption") is not bool(stamps)
                    or (not got and stamps)):
                    raise ValueError("Unsupported caption timecodes")
                found += bool(stamps)
            if got and (item.get("names_confirmed_in_captions") != found
                        or item.get("platform_list_complete_by_captions_alone") is not False):
                raise ValueError("Invented caption coverage")
            total += got
        if (report.get("captions_retrieved") != total
            or not isinstance(engineering, dict)
            or engineering.get("role") != "Engineering Director"
            or engineering.get("original_issue_video_ids_match") is not True
            or engineering.get("existing_worker_integrated") is not True
            or engineering.get("videos_retrieved_reported_not_independently_certified") != total):
            raise ValueError("Engineering handoff or retrieval count failed independent check")
        outcome["retrieved"] = total
        outcome["evidence_integrity"] = "PASS_BOUNDED_SCHEMA"
        outcome["status"] = "PARTIAL_UNCONFIRMED_SOURCE" if total else "BLOCKED_UPSTREAM_CAPTIONS"
        outcome["next_owner"] = "Independent Verifier" if total else "Engineering Director"
    except (ValueError, KeyError, TypeError) as exc:
        outcome["status"] = "REJECTED_EVIDENCE"
        outcome["review_failure_type"] = type(exc).__name__
        outcome["next_owner"] = "Engineering Director"
    return outcome


def post_once(issue, result, run_id, token):
    if not (isinstance(run_id, str) and run_id.isdigit() and token):
        raise PermissionError("Scoped original GitHub run token required")
    marker = "<!-- plenum-three-directors-run:" + run_id + " -->"
    root = "https://api.github.com/repos/" + research.REPO + "/issues/" + str(issue) + "/comments"
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "User-Agent": "PlenumThreeDirectorEvidence/1"}
    with urlopen(Request(root + "?per_page=100", headers=headers), timeout=15) as r:
        comments = json.loads(r.read(250000))
    if any(marker in (c.get("body") or "") for c in comments):
        return
    body = "\n".join([
        marker, "## Chief of Staff | unified three-director acceptance",
        "**Overall: " + result["status"] + "**",
        "Research Director: retrieved **" + str(result["retrieved"]) + "/" + str(result["requested"])
          + "** public caption sets.",
        "Engineering Director: original free worker and Jina fallback reused; no new paid tools.",
        "Independent Verifier: **" + result["evidence_integrity"] + "** of bounded report integrity; "
          + "original external caption source **not independently re-read**.",
        "Next accountable owner: **" + result["next_owner"] + "**.",
        "Evidence: [original Research run](https://github.com/" + research.REPO + "/actions/runs/" + run_id +
          ") and [merged free fallback](https://github.com/" + research.REPO + "/pull/474).",
        "No full video watching, invented transcript, account access, paid service, or 24/7 worker is claimed.",
    ])
    payload = json.dumps({"body": body}).encode()
    with urlopen(Request(root, data=payload, method="POST",
                         headers={**headers, "Content-Type": "application/json"}), timeout=20) as r:
        if r.status != 201:
            raise RuntimeError("GitHub did not acknowledge the director receipt")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("engineering", "verify"), required=True)
    p.add_argument("--event", required=True)
    p.add_argument("--report", default="reports/youtube-research/free-caption-evidence.json")
    p.add_argument("--engineering", default=ENGINEERING_OUT)
    args = p.parse_args(argv)
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    number, ids = read_founder_task(event)
    catalog = research.load_catalog()
    report = load_if_present(args.report)
    if args.mode == "engineering":
        value = engineering_diagnosis(report, ids)
        dest = Path(ENGINEERING_OUT)
    else:
        value = audit(report, load_if_present(args.engineering), ids, catalog)
        dest = Path(VERIFICATION_OUT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    if args.mode == "verify":
        if os.getenv("GITHUB_ACTIONS") != "true" or os.getenv("GITHUB_REPOSITORY") != research.REPO:
            raise PermissionError("Posting permitted only from original GitHub project job")
        post_once(number, value, os.getenv("GITHUB_RUN_ID", ""), os.getenv("GH_TOKEN", ""))
        if value["status"] not in ("PARTIAL_UNCONFIRMED_SOURCE",):
            # A successful technical runner is not proof a transcription succeeded.
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
