"""Bounded, founder-authorized specialist missions using EXISTING Plenum tools.

One local Qwen Chief previously hit LangGraph's recursion ceiling without
finishing a two-worker mission (original run 42796438425). Do NOT multiply
recursion or inference. For unambiguous, PUBLIC tool missions, deterministic
scope-gated routing is faster, cheaper, and produces durable actual artifacts.

No new agent framework/model, private app access, or arbitrary code execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from .chief_workforce_command import (
    CHIEF_MAGIC, CHIEF_TITLE, HINTS, KIND_TO_AGENT,
    parse_founder_chief, worker_event,
)
from .workforce_public_inbox import run_issue
from .agent_library import suggest_sources

MISSION_TITLE = "[Plenum Chief] public mission"
MISSION_MAGIC = "PLENUM_CHIEF_PUBLIC_MISSION_V1"


def independent_expected_team(objective: str) -> tuple[str, ...]:
    """Fixed independent permission gate, not an LLM or externally found text."""
    words = set(re.findall(r"[a-z]+", objective.lower()))
    matching = tuple(kind for kind, terms in HINTS.items() if terms & words)
    if not 2 <= len(matching) <= 3:
        raise ValueError("Only two or three unambiguously supported capabilities")
    return matching


def parse_mission(event: dict) -> dict:
    issue = event.get("issue") or {}
    if issue.get("title") != MISSION_TITLE or not isinstance(issue.get("body"), str):
        raise PermissionError("Not a founder-issued Plenum team mission")
    lines = issue["body"].splitlines()
    if len(lines) != 2 or lines[0] != MISSION_MAGIC or not lines[1].startswith("objective: "):
        raise ValueError("Exact two-line founder mission envelope required")
    # Preserve all existing founder, issue, public-input and scope guards.
    original = {**event, "issue": {**issue, "title": CHIEF_TITLE,
                                   "body": CHIEF_MAGIC + "\n" + lines[1]}}
    checked = parse_founder_chief(original)
    return {**checked, "team": independent_expected_team(checked["objective"]),
            "original": original}


def preflight(event: dict) -> dict:
    task = parse_mission(event)
    return {
        "schema": "plenum-chief-founder-team-v2",
        "issue_number": task["issue_number"],
        "status": "SOURCE_READY_NOT_EXECUTED",
        "mode": "multi",
        "dispatcher": "deterministic_existing_chief_scope_gate",
        "expected_team": list(task["team"]),
        # Read-only source suggestions; never import third-party source into the
        # runner or treat a reference as a verified executable worker.
        "candidate_sources": suggest_sources(task["objective"], limit=6),
        "upstream_sources_installed": 0,
        "new_external_models_started": 0,
        "source_selection_inference_calls": 0,
        "model_called": False,
        "chief_model_delegated": False,
        "executed_workers": 0,
        "tool_outputs_verified": False,
        "independent_verified": False,
        "external_account_changes": False,
        "paid_api_used": False,
    }


def independently_accept_team(expected: tuple[str, ...], observed: dict) -> bool:
    """All requested, distinct original tools must complete their own checks."""
    return (
        2 <= len(expected) <= 3
        and len(set(expected)) == len(expected)
        and set(observed) == set(expected)
        and all(
            observed[k].get("status") == "DRAFT_READY_FOR_FOUNDER"
            and observed[k].get("verified") is True
            and isinstance(observed[k].get("worker"), str)
            and bool(observed[k].get("output_artifact"))
            for k in expected
        )
    )


def execute(event: dict, *, output_dir: Path) -> dict:
    report = preflight(event)
    task = parse_mission(event)
    observed = {}
    for kind in task["team"]:
        # No LLM role selection is needed when the founder's public objective
        # identifies exact existing capabilities. Tools run once each.
        original_event = worker_event(task["original"], kind)
        try:
            result = run_issue(
                original_event, output_dir=output_dir / "workers" / kind,
            )
            if not isinstance(result, dict):
                raise ValueError("Original worker returned a non-object")
            observed[kind] = result
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, ImportError) as exc:
            # Preserve the outcome of any other completed specialist, while
            # withholding a positive mission status if one fails.
            observed[kind] = {
                "status": "BLOCKED_WORKER_OR_VERIFICATION",
                "verified": False,
                "failure_type": type(exc).__name__,
            }
    verified = independently_accept_team(task["team"], observed)
    report.update({
        "status": ("VERIFIED_BOUNDED_TEAM" if verified
                   else "BLOCKED_PARTIAL_TEAM"),
        "automated_routing": True,
        "model_called": False,
        "chief_model_delegated": False,
        "executed_workers": len(observed),
        "successfully_verified_workers": sum(
            x.get("status") == "DRAFT_READY_FOR_FOUNDER"
            and x.get("verified") is True for x in observed.values()
        ),
        "specialists": [KIND_TO_AGENT[k] for k in task["team"]],
        "tool_outputs_verified": verified,
        "independent_verified": verified,
        "worker_results": [{
            "kind": kind,
            "worker": observed[kind].get("worker"),
            "status": observed[kind].get("status", "BLOCKED"),
            "verified_scope": observed[kind].get("verified_scope", "not_verified"),
            "output_artifact": (
                "workers/" + kind + "/" + observed[kind]["output_artifact"]
                if observed[kind].get("output_artifact") else None
            ),
            "failure_type": observed[kind].get("failure_type"),
        } for kind in task["team"]],
        "all_existing_worker_tools_reused": True,
        "founder_review_required": True,
        "new_general_agent_capability_claimed": False,
        "external_account_changes": False,
        "paid_api_used": False,
    })
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out-dir", default="reports/workforce-chief")
    args = parser.parse_args()
    out = Path(args.out_dir)
    if out.is_absolute() or ".." in out.parts or not out.parts or out.parts[0] != "reports":
        parser.error("Only relative reports/ paths accepted")
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    report = execute(event, output_dir=out) if args.execute else preflight(event)
    out.mkdir(parents=True, exist_ok=True)
    (out / ("chief-result-" + str(report["issue_number"]) + ".json")).write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("PLENUM_BOUNDED_TEAM " + report["status"])
    if args.execute and not report["independent_verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
