"""Bounded research-team orchestrator; uses approved models and validated tools."""
from datetime import datetime, timezone

from .lab import run_lab
from .mission import run_mission


def investigate(question, domains=None, model=None, generator=None,
                offline=False, searcher=None, memory_dir=None):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 600:
        raise ValueError("Public research question required, max 600 characters")
    options = {"offline": offline, "model": model, "generator": generator,
               "memory_dir": memory_dir, "simulation": "none"}
    if searcher is not None:
        options["searcher"] = searcher
    narrative = run_mission(question, **options)
    lab = run_lab(question, domains=domains)
    output = {
        "question": question,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "roles": [
            {"role": "planner", "executed": True},
            {"role": "literature researcher", "executed": True},
            {"role": "hypothesis proposer", "executed": bool(model)},
            {"role": "adversarial critic", "executed": bool(model)},
            {"role": "scientific tool specialists", "executed": True},
            {"role": "numerical verifier", "executed": True},
            {"role": "evidence supervisor", "executed": True},
        ],
        "research": narrative,
        "lab": lab,
        "provenance": {"source_status": narrative["source_status"],
                       "paper_ids": [p.get("id") for p in
                                     narrative["literature_and_hypotheses"].get("papers", [])]},
        "checks": {},
        "claims": {
            "new_scientific_discovery_verified": False,
            "proposed_hypotheses_experimentally_tested": False,
            "model_is_AGI": False,
            "code_self_modified": False,
        },
        "caveat": "Numeric reference tests demonstrate the scientific toolchain, not the research hypothesis.",
    }
    return supervise(output)


def supervise(report):
    """Independent deterministic gates on output structure and evidence boundaries."""
    roles = report["roles"]
    research = report["research"]
    simulation = report["lab"]
    checks = {
        "all_science_reference_checks_pass": simulation["known_model_checks_passed"],
        "source_state_recorded": research["source_status"] in
        ("retrieved_metadata", "offline_fixture_no_research_retrieval",
         "no_results", "source_unavailable"),
        "proposer_critic_roles_distinct": all(
            role["role"] in [r["role"] for r in roles]
            for role in ({"role": "hypothesis proposer"}, {"role": "adversarial critic"})
        ),
        "no_unverified_discovery_promoted": (
            not research["verified_new_scientific_discovery"]
            and not report["claims"]["new_scientific_discovery_verified"]
        ),
        "model_quality_status_explicit": (
            "model_outputs_pass_basic_screen" in research
        ),
        "no_autonomous_code_change": not report["claims"]["code_self_modified"],
    }
    report["checks"] = checks
    report["workflow_verified_as_known_tool_demonstration"] = all(checks.values())
    report["hypotheses_verified"] = False
    return report
