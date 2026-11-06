"""Dependency-aware multi-tool research graph with dynamic parallel fan-out.

LangGraph Send creates one worker per authorized scientific tool. A subsequent
OpenMDAO node explicitly depends on validated SciPy thermal output. All claims
are restricted to prewritten known-model fixtures.
"""
from datetime import datetime, timezone
import operator
from typing import Annotated, TypedDict

from .tool_registry import approve_request, get_registry

class ResearchState(TypedDict, total=False):
    question: str
    tool_keys: list[str]
    offline: bool
    enable_optimization: bool
    results: Annotated[list[dict], operator.add]
    optimized: dict
    verification: dict

def _execute_tool(tool_key, question, offline):
    try:
        if tool_key.startswith("scipy.") or tool_key == "rdkit.molecule":
            from .lab import solve
            names = {
                "scipy.orbit": "mechanics",
                "scipy.thermal": "materials",
                "scipy.kinetics": "chemistry",
                "scipy.electronics": "electronics",
                "rdkit.molecule": "molecules",
            }
            result = solve(names[tool_key])
            return {
                "tool": tool_key, "status": "completed",
                "verified_fixture": bool(result["verified_fixture"]),
                "output": result,
            }
        if tool_key == "federated.metadata":
            from .federated_sources import search_federated
            evidence=search_federated(question, offline=offline)
            status=("skipped_offline" if offline else
                    "retrieved_metadata" if evidence["all_providers_healthy"]
                    else "partial_metadata")
            return {"tool":tool_key, "status":status, "verified_fixture":False,
                    "evidence":evidence, "citation_verified":False}
        if tool_key == "openalex.metadata":
            if offline:
                return {
                    "tool": tool_key, "status": "skipped_offline",
                    "verified_fixture": False, "papers": [],
                    "note": "No fabricated literature. Enable online retrieval deliberately.",
                }
            from .literature import search_papers
            papers = search_papers(question, limit=5)
            return {
                "tool": tool_key, "status": "retrieved_metadata",
                "verified_fixture": False,
                "papers": papers,
                "note": "Metadata is not paper-content or citation verification",
            }
        raise ValueError("Unexpected unapproved scientific tool")
    except Exception as exc:
        return {
            "tool": tool_key, "status": "failed",
            "verified_fixture": False,
            "error_type": type(exc).__name__,
        }

def _planner(state):
    approve_request(state["tool_keys"])
    return {}

def _fanout(state):
    from langgraph.types import Send
    return [
        Send("worker", {
            "tool": key,
            "question": state["question"],
            "offline": state["offline"],
        })
        for key in state["tool_keys"]
    ]

def _worker(state):
    return {"results": [_execute_tool(state["tool"], state["question"], state["offline"])]}

def _optimize(state):
    if not state["enable_optimization"]:
        return {"optimized": {"status": "not_requested"}}
    matching = [x for x in state["results"] if x["tool"] == "scipy.thermal"
                and x["status"] == "completed" and x["verified_fixture"]]
    if len(matching) != 1:
        return {"optimized": {"status": "blocked_missing_verified_thermal_input"}}
    try:
        from .openmdao_adapter import optimize_cooling_area
        return {"optimized": optimize_cooling_area(matching[0]["output"])}
    except Exception as exc:
        return {"optimized": {"status": "failed", "error_type": type(exc).__name__}}

def _verify(state):
    tools = state["results"]
    keys = state["tool_keys"]
    unique = len({x["tool"] for x in tools}) == len(keys)
    complete = all(any(x["tool"] == key for x in tools) for key in keys)
    requested_solver = [x for x in tools if x["tool"] not in
                        ("openalex.metadata", "federated.metadata")]
    solvers_pass = bool(requested_solver) and all(
        x["status"] == "completed" and x["verified_fixture"] for x in requested_solver
    )
    literature = [x for x in tools if x["tool"] in
                  ("openalex.metadata", "federated.metadata")]
    literature_ok = all(x["status"] in ("retrieved_metadata", "partial_metadata", "skipped_offline")
                        for x in literature)
    optimize_ok = (state["optimized"].get("verified_fixture", False)
                   if state["enable_optimization"] else True)
    no_errors = all(x["status"] != "failed" for x in tools)
    return {
        "verification": {
            "all_requested_tools_reported": bool(unique and complete),
            "known_scientific_fixtures_passed": bool(solvers_pass),
            "literature_retrieval_status_acceptable": bool(literature_ok),
            "dependency_satisfied": bool(optimize_ok),
            "no_failed_tool_calls": bool(no_errors),
            "scientific_discovery_verified": False,
            "AGI_demonstrated": False,
            "production_code_modified_by_agents": False,
        }
    }

def build_graph():
    from langgraph.graph import START, END, StateGraph
    graph = StateGraph(ResearchState)
    graph.add_node("planner", _planner)
    graph.add_node("worker", _worker)
    graph.add_node("dependent_openmdao", _optimize)
    graph.add_node("independent_verifier", _verify)
    graph.add_edge(START, "planner")
    graph.add_conditional_edges("planner", _fanout, ["worker"])
    graph.add_edge("worker", "dependent_openmdao")
    graph.add_edge("dependent_openmdao", "independent_verifier")
    graph.add_edge("independent_verifier", END)
    return graph.compile()

def run_network(question, tool_keys=None, offline=True, optimize=True, graph=None):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 600:
        raise ValueError("Public research question must have 1..600 characters")
    default = ("scipy.orbit", "scipy.thermal", "scipy.kinetics", "rdkit.molecule")
    keys = approve_request(default if tool_keys is None else tool_keys)
    if optimize and "scipy.thermal" not in keys:
        raise ValueError("Dependent OpenMDAO cooling optimization requires scipy.thermal")
    workflow = graph if graph is not None else build_graph()
    result = workflow.invoke({
        "question": question, "tool_keys": keys,
        "offline": bool(offline), "enable_optimization": bool(optimize),
        "results": [],
    }, config={"max_concurrency": 5, "recursion_limit": 12})
    order = {key: index for index, key in enumerate(keys)}
    results = sorted(result["results"], key=lambda row: order.get(row["tool"], 100))
    registry = get_registry()
    executed = set(keys)
    if optimize:
        executed.add("openmdao.cooling")
    relevant = [item for item in registry["tools"] if item["key"] in executed]
    checks = result["verification"]
    acceptable = all(checks[k] for k in (
        "all_requested_tools_reported", "known_scientific_fixtures_passed",
        "literature_retrieval_status_acceptable", "dependency_satisfied",
        "no_failed_tool_calls"
    ))
    return {
        "schema": "plenum-parallel-science-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "execution": "LangGraph Send fan-out, fan-in, then dependency-aware OpenMDAO",
        "parallel_tool_count": len(keys),
        "requested_tools": keys,
        "workers": results,
        "dependent_optimization": result["optimized"],
        "registry": relevant,
        "verification": checks,
        "known_model_integration_passed": bool(acceptable),
        "scientific_discovery_verified": False,
        "hypotheses_validated": False,
        "model_inference_used": False,
        "external_execution_enabled": False,
        "limitations": [
            "Scientific models are fixed demonstrators, not novel user-specific simulations.",
            "Concurrent tasks can require more memory/CPU; limit five per batch.",
            "OpenMDAO only runs after a verified SciPy thermal fixture.",
            "OpenAlex provides public metadata only, subject to network availability.",
            "Model weights, deployments, paid actions and third-party skills remain untouched.",
        ]
    }
