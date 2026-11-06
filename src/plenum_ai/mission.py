"""A bounded research workflow. No arbitrary tool invocation, deployment or spending."""
from datetime import datetime, timezone
from .literature import search_papers
from .physics import circular_orbit_speed
from .research import make_report
from .science import diffuse_heat
from .quality import assess_answer

OFFLINE_SOURCES = [{
    "id": "OFFLINE-DEMO",
    "title": "Offline fixture: not a retrieved or independently verified paper",
    "year": None, "doi": None, "url": None,
}]


def run_mission(question, simulation="heat", model=None, generator=None,
                offline=False, searcher=search_papers):
    if not question or len(question) > 600:
        raise ValueError("Question required, maximum 600 characters")
    if simulation not in ("heat", "orbit", "none"):
        raise ValueError("Unsupported simulator")
    stages = [{"role": "planner", "action": "Bound question and select known simulator",
               "status": "complete"}]
    issues = []
    if offline:
        papers = OFFLINE_SOURCES
        source_status = "offline_fixture_no_research_retrieval"
    else:
        try:
            papers = searcher(question)
            source_status = "retrieved_metadata" if papers else "no_results"
        except Exception as exc:
            papers = []
            source_status = "source_unavailable"
            issues.append("Literature retrieval failed: " + type(exc).__name__)
    stages.append({"role": "literature_researcher", "action": "OpenAlex metadata retrieval",
                   "status": source_status})
    kw = {"model": model} if generator is None else {"model": model, "generator": generator}
    notes = make_report(question, papers, **kw)
    quality = {
        "proposer": assess_answer(notes["proposals"][0], "proposer") if model else None,
        "critic": assess_answer(notes["independent_criticisms"][0], "critic") if model else None,
    }
    stages.append({"role": "hypothesis_proposer", "action": "Local model hypothesis generation",
                   "status": "completed_unverified" if model else "not_run_no_model"})
    stages.append({"role": "adversarial_critic", "action": "Independent-role critique",
                   "status": "completed_unverified" if model else "not_run_no_model"})
    if simulation == "heat":
        sim = diffuse_heat()
        verified = sim["verification"]["conserved_discrete_total"]
    elif simulation == "orbit":
        speed = circular_orbit_speed(6_771_000)
        sim = {"model": "Newtonian circular orbit around Earth",
               "radius_m": 6_771_000, "speed_m_s": speed,
               "verification": {"plausible_low_earth_orbit_speed": 7600 < speed < 7800},
               "status": "numerical_model_only"}
        verified = sim["verification"]["plausible_low_earth_orbit_speed"]
    else:
        sim, verified = None, False
    stages.append({"role": "scientific_simulator", "action": simulation,
                   "status": "complete" if sim else "not_run"})
    stages.append({"role": "deterministic_verifier", "action": "Check stated narrow numerical invariant",
                   "status": "pass" if verified else "not_passed"})
    return {
        "question": question,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_status": source_status,
        "stages": stages,
        "literature_and_hypotheses": notes,
        "simulation": sim,
        "numeric_benchmark_verified": verified,
        "verified_new_scientific_discovery": False,
        "model_inference_executed": bool(model),
        "model_output_quality": quality,
        "model_outputs_pass_basic_screen": bool(model and quality["proposer"]["acceptable"] and quality["critic"]["acceptable"]),
        "issues": issues,
        "limitations": [
            "Role prompts are not independent model training or experimental verification.",
            "Simulation is an illustrative known physics benchmark, not validation of the proposed hypotheses.",
            "Offline fixture is not scientific evidence.",
            "No automatic source-code rewriting or production deployment occurs.",
        ],
    }
