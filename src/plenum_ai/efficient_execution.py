"""Evidence-first low-cost dispatch for approved PUBLIC scientific fixtures.

This is a deterministic workflow optimizer, NOT a general reasoning agent.
It intentionally does not use model inference, install dependencies, fetch
live data, write to GitHub, or execute generated code. Unknown or private
requests are held for review rather than disguised as successful research.
"""
from hashlib import sha256
import json
from pathlib import Path
import re
from time import perf_counter

SCHEMA = "plenum-efficient-execution-v1"
# Explicit words/phrases avoid matches like "heat" in "wheat" or "ion"
# in "evolution". No fuzzy model classification is presented as truth.
ROUTES = (
    ("mechanics", ("orbit", "orbital", "gravity", "gravitational",
                   "trajectory", "satellite", "kepler")),
    ("materials", ("heat", "thermal", "cooling", "temperature")),
    ("chemistry", ("chemical reaction", "reaction rate",
                   "kinetics", "first-order reaction")),
    ("electronics", ("rc circuit", "capacitor", "circuit",
                     "electrical circuit")),
    ("molecules", ("molecule", "molecular formula", "smiles",
                   "ethanol", "molecular descriptor")),
)
PRIVATE_MARKERS = (
    "confidential", "private", "unpublished", "secret", "password",
    "api key", "credential", "personal record", "patient record",
    "proprietary",
)
MAX_TOOLS = 3
# Historical default parallel_research.run_network uses four fixed fixtures.
OLD_DEFAULT_SOLVERS = 4


def _contains(query, phrase):
    return re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", query) is not None


def plan(question):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 600:
        raise ValueError("One PUBLIC question of 1..600 characters is required")
    stripped = question.strip()
    normalized = " ".join(stripped.lower().split())
    question_digest = sha256(stripped.encode("utf-8")).hexdigest()
    private = any(_contains(normalized, marker) for marker in PRIVATE_MARKERS)
    matched = [domain for domain, words in ROUTES
               if any(_contains(normalized, term) for term in words)]
    if private:
        decision, reason, matched = (
            "review_required", "private_or_confidential_content_not_suitable_for_public_actions", [])
    elif not matched:
        decision, reason = (
            "review_required", "no_approved_fixture_reliably_matches_this_question")
    elif len(matched) > MAX_TOOLS:
        decision, reason = (
            "review_required", "too_many_distinct_domains_for_a_bounded_fixture_run")
    else:
        decision, reason = (
            "approved_known_fixture", "fewest_approved_numerical_tools_for_matching_domains")
    approved = matched if decision == "approved_known_fixture" else []
    return {
        "schema": SCHEMA,
        "question_sha256": question_digest,
        "question_text_in_public_artifact": False,
        "decision": decision,
        "reason": reason,
        "domains": approved,
        "approved_tool_count": len(approved),
        "maximum_auto_tools": MAX_TOOLS,
        "default_old_scientific_fixture_count": OLD_DEFAULT_SOLVERS,
        "unnecessary_default_fixture_calls_avoided":
            OLD_DEFAULT_SOLVERS-len(approved),
        "estimated_model_calls": 0,
        "external_requests_authorized": False,
        "paid_inference_authorized": False,
        "automated_code_changes_authorized": False,
        "user_specific_problem_solved": False,
        "method": "deterministic_keyword_router_with_strict_word_boundaries",
        "accuracy_and_novelty_not_established": True,
        "limitations": [
            "Matched tools demonstrate known fixed equations, not the user's original hypothesis.",
            "A good numerical fixture does not establish a new scientific result.",
            "Unrecognized or confidential requests are referred for review, not guessed.",
            "No general intelligence, recursive self-improvement or self-deployment is demonstrated.",
        ],
    }


def execute(question, *, dry_run=False, solver=None):
    decision = plan(question)
    if dry_run or decision["decision"] != "approved_known_fixture":
        return {**decision, "status": (
            "planned_without_execution" if dry_run else "requires_review"),
            "results": [], "known_model_checks_passed": False,
            "measured_solver_elapsed_ms": None,
            "scientific_discovery_verified": False, "AGI_demonstrated": False}
    # Resolve only when execution is authorized, after preflight.
    if solver is None:
        from .lab import solve
        solver = solve
    results = []
    started = perf_counter()
    for domain in decision["domains"]:
        try:
            output = solver(domain)
            if not isinstance(output, dict) or output.get("domain") != domain:
                raise ValueError("Scientific fixture returned an unexpected domain")
            results.append({
                "domain": domain,
                "status": "completed",
                "verified_fixture": output.get("verified_fixture") is True,
                "output": output,
            })
        except Exception as exc:
            # No fabricated substitutes and no raw exception content from public data.
            results.append({
                "domain": domain, "status": "failed",
                "verified_fixture": False, "error_type": type(exc).__name__,
            })
    passed = bool(results) and all(x["verified_fixture"] for x in results)
    return {
        **decision, "status": "known_fixtures_completed" if passed else "fixture_failed",
        "results": results,
        "known_model_checks_passed": passed,
        "measured_solver_elapsed_ms": round((perf_counter()-started)*1000, 2),
        "scientific_discovery_verified": False,
        "AGI_demonstrated": False,
        "user_specific_problem_solved": False,
    }


def save_report(path, report):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                 allow_nan=False)+"\n", encoding="utf-8")
    return str(target)
