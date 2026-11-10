"""Founder-gated multi-specialist PUBLIC mission, reusing the original Chief and tools.

This expands the verified one-specialist path to two or three independently
checked existing Plenum worker capabilities. It does NOT create new models,
grant private accounts, or run unreviewed catalogue personas.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re

from .chief_workforce_command import (
    CHIEF_MAGIC, CHIEF_TITLE, FORBIDDEN, HINTS, KIND_TO_AGENT,
    MODEL, MODEL_URL, parse_founder_chief, worker_event,
)
from .workforce_public_inbox import OWNER, REPO, run_issue

MISSION_TITLE = "[Plenum Chief] public mission"
MISSION_MAGIC = "PLENUM_CHIEF_PUBLIC_MISSION_V1"


def independent_expected_team(objective: str) -> tuple[str, ...]:
    """Separate founder-scope gate; never let a model expand its own tool rights."""
    words = set(re.findall(r"[a-z]+", objective.lower()))
    matching = tuple(kind for kind, terms in HINTS.items() if words & terms)
    if not 2 <= len(matching) <= 3:
        raise ValueError("Public mission requires two or three clear approved capabilities")
    return matching


def parse_mission(event: dict) -> dict:
    issue = event.get("issue") or {}
    if issue.get("title") != MISSION_TITLE or not isinstance(issue.get("body"), str):
        raise PermissionError("Not an original Plenum multi-specialist mission")
    parts = issue["body"].splitlines()
    if len(parts) != 2 or parts[0] != MISSION_MAGIC or not parts[1].startswith("objective: "):
        raise ValueError("Exact two-line mission envelope required")
    # Reuse original Chief's founder, repository, issue, length, and sensitivity
    # checks. Only the already-verified alternate title/envelope is normalized.
    legacy = {**event, "issue": {
        **issue, "title": CHIEF_TITLE,
        "body": CHIEF_MAGIC + "\n" + parts[1],
    }}
    validated = parse_founder_chief(legacy)
    team = independent_expected_team(validated["objective"])
    return {**validated, "team": team, "legacy_event": legacy}


def preflight(event: dict) -> dict:
    task = parse_mission(event)
    return {
        "schema": "plenum-chief-founder-team-v1",
        "issue_number": task["issue_number"],
        "status": "SOURCE_READY_NOT_EXECUTED",
        "mode": "multi",
        "expected_team": list(task["team"]),
        "model_called": False,
        "chief_delegated": False,
        "executed_workers": 0,
        "independent_verified": False,
        "external_account_changes": False,
        "paid_api_used": False,
    }


def independently_accept_team(expected: tuple[str, ...], routed: list[str],
                              observed: dict, calls: int) -> bool:
    """Accept distinct observed worker executions; repeat *requests* are inert."""
    required = {KIND_TO_AGENT[kind] for kind in expected}
    return bool(
        2 <= len(required) <= 3
        and calls >= len(required)
        and len(routed) == calls
        and set(routed) == required
        and set(observed) == set(expected)
        and len(observed) == len(expected)
        and all(observed[k]["status"] == "DRAFT_READY_FOR_FOUNDER"
                and observed[k].get("verified") is True for k in expected)
    )


def execute(event: dict, *, output_dir: Path) -> dict:
    report = preflight(event)
    if (os.environ.get("PLENUM_EPHEMERAL_RUNNER") != "confirmed"
            or os.environ.get("PLENUM_CHIEF_MODEL_URL") != MODEL_URL):
        raise PermissionError("Mission requires original approved ephemeral Ollama runner")

    from langchain_core.tools import tool
    from langchain_ollama import ChatOllama
    from deepagents import create_deep_agent
    from langgraph.checkpoint.memory import MemorySaver

    task = parse_mission(event)
    expected = task["team"]
    actual: dict[str, dict] = {}
    model = ChatOllama(
        model=MODEL, base_url=MODEL_URL, temperature=0,
        reasoning=False, num_ctx=8192, num_predict=600,
    )
    delegates = []
    for kind, name in KIND_TO_AGENT.items():
        def make_tool(kind=kind):
            @tool("execute_" + kind)
            def execute_original_worker() -> str:
                """Call one original approved PUBLIC Plenum tool worker, and return its independently checked result."""
                if kind not in expected:
                    return json.dumps({"status": "BLOCKED_OUTSIDE_FOUNDER_MISSION"})
                if kind in actual:
                    return json.dumps({"status": "DUPLICATE_INERT", "previous": actual[kind]["status"]})
                if len(actual) >= len(expected):
                    return json.dumps({"status": "BLOCKED_TEAM_LIMIT"})
                try:
                    original = worker_event(task["legacy_event"], kind)
                    result = run_issue(original, output_dir=output_dir / "workers" / kind)
                    actual[kind] = result
                    return json.dumps({
                        "status": result["status"], "worker": result.get("worker"),
                        "verified_scope": result.get("verified_scope", "not_verified"),
                    })
                except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
                    actual[kind] = {"status": "BLOCKED_WORKER_OR_VERIFICATION",
                                    "verified": False}
                    return json.dumps({"status": "BLOCKED_WORKER_OR_VERIFICATION"})
            return execute_original_worker

        delegates.append({
            "name": name,
            "description": {
                "public_research": "Gather actual PUBLIC research metadata and evidence-linked leads with original World Horizon worker.",
                "public_program": "Produce actual review-only Python data-validator starter with Program Foundry and independent AST/hash check.",
                "public_science": "Execute the existing known-model numerical science and independently inspect its durable checkpoint.",
                "public_creative": "Produce actual original SVG and MusicXML with Creative Studio and independently parse both files.",
            }[kind],
            "system_prompt": (
                "You are Plenum's " + name + ". For this PUBLIC mission, call your "
                "one execute tool ONCE. Do not invent an outcome or access accounts. "
                "Report only the exact status and verification scope returned."
            ),
            "tools": [make_tool()],
            "model": model,
        })

    chief = create_deep_agent(
        model=model,
        system_prompt=(
            "You are the existing Plenum Chief of Staff. The founder issued "
            "a PUBLIC mission with TWO or THREE separate deliverables. "
            "Delegate to each matching EXISTING specialist via the task tool. "
            "Choose one matching role for EACH distinct deliverable, do not "
            "answer without using specialist tools, do not invent evidence. "
            "Research/sources: research-specialist; program/validator: "
            "coding-specialist; numerical/thermal: scientific-specialist; "
            "SVG/music/illustration: creative-specialist. Never call "
            "unrelated roles. No private accounts, payments, deployments, "
            "publication, browsing logins, outbound messages or new agents."
        ),
        tools=[], subagents=delegates, checkpointer=MemorySaver(),
    )
    result = chief.invoke(
        {"messages": [{
            "role": "user",
            "content": "Founder PUBLIC mission: " + task["objective"] +
                       ". Delegate its distinct deliverables to the appropriate "
                       "existing specialists, and report observed outcomes only.",
        }]},
        config={
            "configurable": {"thread_id": "founder-team-" + str(task["issue_number"])},
            "recursion_limit": 38,
        },
    )
    calls = [
        c for msg in result.get("messages", [])
        for c in (getattr(msg, "tool_calls", None) or [])
        if c.get("name") == "task"
    ]
    routed = [
        c.get("args", {}).get("subagent_type") for c in calls
        if isinstance(c.get("args"), dict)
    ]
    correct = independently_accept_team(expected, routed, actual, len(calls))
    report.update({
        "status": "VERIFIED_CHIEF_TEAM_DELEGATION" if correct else "BLOCKED_TEAM_OR_VERIFICATION",
        "model_called": True,
        "chief_delegated": bool(calls),
        "delegation_requests": len(calls),
        "routed_roles": routed[:20],
        "executed_workers": len(actual),
        "executed_kinds": list(actual),
        "specialists": [KIND_TO_AGENT[kind] for kind in expected if kind in actual],
        "independent_verified": correct,
        "worker_results": [{
            "kind": kind,
            "status": actual[kind]["status"],
            "verified_scope": actual[kind].get("verified_scope", "not_verified"),
            "output_artifact": actual[kind].get("output_artifact"),
        } for kind in expected if kind in actual],
        "all_original_tools_reused": True,
        "founder_review_required": True,
        "external_account_changes": False,
        "paid_api_used": False,
    })
    return report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--event", required=True)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--out-dir", default="reports/workforce-chief")
    args = p.parse_args()
    out = Path(args.out_dir)
    if out.is_absolute() or ".." in out.parts or not out.parts or out.parts[0] != "reports":
        p.error("Output must remain inside reports/")
    event = json.loads(Path(args.event).read_text(encoding="utf-8"))
    report = preflight(event)
    if args.execute:
        report = execute(event, output_dir=out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / ("chief-result-" + str(report["issue_number"]) + ".json")
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("CHIEF_FOUNDER_TEAM " + report["status"])
    if args.execute and report["status"] != "VERIFIED_CHIEF_TEAM_DELEGATION":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
