"""One real, auditable LangGraph -> official Playwright MCP research task.

This deliberately invokes only the strict fixed public example.com browser
MCP bridge. It does not allow a model to choose URLs or browser tools and does
not claim autonomous general-purpose internet use or AI reasoning.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import TypedDict

URL = "https://example.com/"
ROOT = Path(__file__).resolve().parents[2]
MCP_RUNNER = ROOT / "tools" / "browser-mcp" / "verify.mjs"
EXPECTED = "plenum-playwright-mcp-public-readonly-v1"

class BrowserResearchState(TypedDict, total=False):
    request: str
    allowed_url: str
    planned_operation: str
    observation: dict
    verified: bool
    error: str

def fixed_plan(state):
    if state.get("request") != "Inspect the public Example Domain page for an accessibility heading.":
        raise PermissionError("Only the preapproved public research task is supported")
    return {"allowed_url": URL, "planned_operation": "read-only public MCP navigation+snapshot"}

def call_real_mcp():
    if not MCP_RUNNER.is_file():
        raise FileNotFoundError("Pinned browser MCP runner unavailable")
    env = {k: os.environ[k] for k in ("PATH", "HOME", "TMPDIR", "CI") if k in os.environ}
    env["CI"] = "true"
    result = subprocess.run(
        ["node", str(MCP_RUNNER), URL], cwd=str(MCP_RUNNER.parent),
        env=env, capture_output=True, text=True, timeout=100, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Isolated browser MCP returned a nonzero result")
    if len(result.stdout) > 16_000:
        raise ValueError("Oversized MCP public result")
    report = json.loads(result.stdout)
    return report

def browser_node(state):
    if state.get("allowed_url") != URL:
        raise PermissionError("Browser graph attempted unauthorized URL")
    result = call_real_mcp()
    return {"observation": result}

def verify_node(state):
    x = state.get("observation", {})
    valid = (
        isinstance(x, dict) and
        x.get("schema") == EXPECTED and
        x.get("public_page") == URL and
        x.get("mcp_protocol_roundtrip_succeeded") is True and
        x.get("accessibility_snapshot_has_example_domain") is True and
        x.get("site_mutation_performed") is False and
        x.get("authenticated_browser_session_used") is False and
        x.get("AGI_demonstrated") is False and
        state.get("planned_operation") == "read-only public MCP navigation+snapshot"
    )
    if not valid:
        raise RuntimeError("Browser evidence failed independent verification")
    return {"verified": True}

def build_graph():
    from langgraph.graph import START, END, StateGraph
    g = StateGraph(BrowserResearchState)
    g.add_node("fixed_public_plan", fixed_plan)
    g.add_node("official_mcp_browser", browser_node)
    g.add_node("independent_result_gate", verify_node)
    g.add_edge(START, "fixed_public_plan")
    g.add_edge("fixed_public_plan", "official_mcp_browser")
    g.add_edge("official_mcp_browser", "independent_result_gate")
    g.add_edge("independent_result_gate", END)
    return g.compile()

def run_public_graph():
    request = "Inspect the public Example Domain page for an accessibility heading."
    final = build_graph().invoke({"request": request}, config={"recursion_limit": 8})
    if not final.get("verified"):
        raise RuntimeError("No verified browser result")
    return {
        "schema": "plenum-langgraph-browser-mcp-verified-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "orchestrator": "LangGraph fixed policy plan, browser, verifier",
        "upstream_browser": "@playwright/mcp@0.0.84",
        "public_research_page": URL,
        "browser_mcp_verified": True,
        "fixed_workflow_verified": True,
        "model_selected_browser_actions": False,
        "independent_multi_step_model_agency_demonstrated": False,
        "private_accounts_accessed": False,
        "external_website_changed": False,
        "continuous_service_running": False,
        "AGI_demonstrated": False,
        "limitations": "Public fixed page and fixed steps, no model inference, no autonomous planning, no login or website changes."
    }

if __name__ == "__main__":
    print(json.dumps(run_public_graph(), indent=2))
