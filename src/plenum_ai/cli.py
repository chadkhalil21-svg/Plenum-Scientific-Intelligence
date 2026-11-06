"""Command-line interface. No paid services or unrestricted AI tool use."""
import argparse
import json
from pathlib import Path
from .evolve import default_benchmarks, evaluate_evolution
from .literature import search_papers
from .physics import circular_orbit_speed
from .research import make_report
from .mission import run_mission
from .memory import make_record, verify, save
from .audit import independent_audit
import os


def save_json(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(target)


def main():
    parser = argparse.ArgumentParser(prog="plenum")
    commands = parser.add_subparsers(dest="action", required=True)
    research = commands.add_parser("research")
    research.add_argument("--query", required=True)
    research.add_argument("--out", default="reports/research.json")
    research.add_argument("--model", help="Locally running Ollama model; optional")
    improve = commands.add_parser("improve")
    improve.add_argument("--out", default="reports/improvement.json")
    physics = commands.add_parser("physics")
    physics.add_argument("--radius-m", required=True, type=float)
    mission = commands.add_parser("mission")
    mission.add_argument("--query", required=True)
    mission.add_argument("--out", default="reports/mission.json")
    mission.add_argument("--simulation", choices=["heat", "orbit", "none"], default="heat")
    mission.add_argument("--offline", action="store_true", help="Use clearly labeled offline fixture")
    mission.add_argument("--model", help="Optional locally running Ollama model")
    mission.add_argument("--hf-model", action="store_true", help="Optional reviewed tiny CPU model")
    mission.add_argument("--memory-dir", help="Public archived research metadata")
    memory = commands.add_parser("memory-record")
    memory.add_argument("--mission", required=True)
    memory.add_argument("--improvement", required=True)
    memory.add_argument("--out", default="reports/memory_entry.json")
    ingest = commands.add_parser("memory-ingest")
    ingest.add_argument("--file", required=True)
    ingest.add_argument("--dir", required=True)
    lab = commands.add_parser("lab")
    lab.add_argument("--query", required=True)
    lab.add_argument("--domains", default="mechanics,chemistry,materials,electronics,molecules")
    lab.add_argument("--out", default="reports/scientific_lab.json")
    lab.add_argument("--method", choices=["RK45","DOP853","Radau"], default="RK45")
    methods = commands.add_parser("solver-benchmark")
    methods.add_argument("--out", default="reports/solver_benchmark.json")
    team = commands.add_parser("investigate")
    team.add_argument("--query", required=True)
    team.add_argument("--domains", default="mechanics,chemistry,materials,electronics,molecules")
    team.add_argument("--out", default="reports/investigation.json")
    team.add_argument("--offline", action="store_true")
    team.add_argument("--memory-dir")
    team.add_argument("--model", help="Existing local Ollama model")
    team.add_argument("--hf-model", action="store_true")
    training = commands.add_parser("train-models")
    training.add_argument("--tasks", default="botany,chemistry,handwriting,gravity",
                          help="Comma-separated allowlisted scientific ML benchmarks")
    training.add_argument("--out", default="reports/model_training.json")
    qa = commands.add_parser("eval-science")
    qa.add_argument("--count", type=int, default=12)
    qa.add_argument("--out", default="reports/science_reasoning.json")
    tune = commands.add_parser("fine-tune-science")
    tune.add_argument("--out", default="reports/qwen3_finetune.json")
    tune.add_argument("--checkpoint-dir", default="candidates/qwen3-science-v1")
    registry = commands.add_parser("tool-registry")
    registry.add_argument("--out", default="reports/tool_registry.json")
    multi = commands.add_parser("parallel-research")
    multi.add_argument("--query", required=True)
    multi.add_argument("--tools", default="scipy.orbit,scipy.thermal,scipy.kinetics,rdkit.molecule")
    multi.add_argument("--online", action="store_true", help="Allow read-only research metadata retrieval")
    multi.add_argument("--auto", action="store_true", help="Route public question to approved tools using deterministic keywords")
    multi.add_argument("--no-optimization", action="store_true")
    multi.add_argument("--out", default="reports/parallel_research.json")
    skills = commands.add_parser("scientific-skills")
    skills.add_argument("--inspect", help="Allowlisted K-Dense skill name for pinned read-only review")
    skills.add_argument("--out", default="reports/scientific_skills.json")
    federation = commands.add_parser("federated-literature")
    federation.add_argument("--query", required=True)
    federation.add_argument("--online", action="store_true")
    federation.add_argument("--out", default="reports/federated_literature.json")
    nasa = commands.add_parser("nasa-exoplanets")
    nasa.add_argument("--out", default="reports/nasa_exoplanet_consistency.json")
    args = parser.parse_args()
    if args.action == "research":
        papers = search_papers(args.query)
        report = make_report(args.query, papers, model=args.model)
        print("Research inventory:", save_json(args.out, report), "papers:", len(papers))
    elif args.action == "improve":
        benchmarks = default_benchmarks()
        evaluation = evaluate_evolution(benchmarks)
        evaluation["independent_audit"] = independent_audit(benchmarks, evaluation)
        print("Improvement proposal:", save_json(args.out, evaluation),
              "accepted:", evaluation["accepted_for_proposal"])
    elif args.action == "mission":
        if args.model and args.hf_model:
            parser.error("Choose either local Ollama or Hugging Face model")
        if args.hf_model:
            from .hf_model import hf_generate, APPROVED_MODEL
            generator = hf_generate
            model = APPROVED_MODEL
        else:
            generator = None
            model = args.model
        report = run_mission(args.query, simulation=args.simulation,
                             offline=args.offline, model=model,
                             memory_dir=args.memory_dir,
                             generator=generator)
        print("Mission:", save_json(args.out, report),
              "benchmark:", report["numeric_benchmark_verified"],
              "model:", report["model_inference_executed"])
    elif args.action == "memory-record":
        mission_report = json.loads(Path(args.mission).read_text(encoding="utf-8"))
        improvement = json.loads(Path(args.improvement).read_text(encoding="utf-8"))
        record = make_record(mission_report, improvement,
                             os.getenv("GITHUB_RUN_ID", ""),
                             os.getenv("GITHUB_SHA", ""))
        verify(record)
        print("Validated memory record:", save_json(args.out, record), "ID:", record["id"])
    elif args.action == "memory-ingest":
        record = json.loads(Path(args.file).read_text(encoding="utf-8"))
        name, created = save(record, args.dir)
        print("Stored checksum-verified memory:", name, "new:", created)
    elif args.action == "lab":
        from .lab import run_lab
        domains = [x.strip() for x in args.domains.split(",")]
        result = run_lab(args.query, domains=domains, method=args.method)
        print("Scientific lab:", save_json(args.out,result),
              "passed:", result["known_model_checks_passed"])
    elif args.action == "solver-benchmark":
        from .lab import benchmark_methods
        result = benchmark_methods()
        print("Numerical solver benchmark:", save_json(args.out,result))
    elif args.action == "investigate":
        if args.model and args.hf_model:
            parser.error("Choose either Ollama or Qwen3")
        from .investigate import investigate
        if args.hf_model:
            from .hf_model import hf_generate, APPROVED_MODEL
            name, generator = APPROVED_MODEL, hf_generate
        else:
            name, generator = args.model, None
        report = investigate(args.query, domains=[s.strip() for s in args.domains.split(",")],
                             offline=args.offline, model=name, generator=generator,
                             memory_dir=args.memory_dir)
        print("Research team:", save_json(args.out, report),
              "verified known tools:", report["workflow_verified_as_known_tool_demonstration"],
              "new discovery:", report["hypotheses_verified"])
    elif args.action == "train-models":
        from .trainlab import run_training_lab
        tasks = [task.strip() for task in args.tasks.split(",")]
        report = run_training_lab(tasks)
        print("Trained scientific ML models:", save_json(args.out, report),
              "holdout improvements:", report["candidate_beats_dummy_in_all_tasks"],
              "production deployed:", report["deployment_authorized"])
    elif args.action == "eval-science":
        from .science_eval import run_external_evaluation
        report = run_external_evaluation(count=args.count, out=args.out)
        print("External science evaluation:", report["correct"], "/", report["total"],
              "data revision:", report["source"]["revision"],
              "model revision:", report["model_revision"])
    elif args.action == "fine-tune-science":
        from .fine_tune import run_fine_tuning
        report = run_fine_tuning(output_dir=args.checkpoint_dir, report_file=args.out)
        print("LoRA candidate training:", report["training_steps"],
              "optimizer steps; baseline:", report["baseline"]["correct"],
              "/", report["baseline"]["total"],
              "candidate:", report["candidate"]["correct"],
              "/", report["candidate"]["total"],
              "automatically deployed:", report["automatic_model_promotion"])
    elif args.action == "tool-registry":
        from .tool_registry import get_registry
        report = get_registry()
        print("Scientific tool registry:", save_json(args.out, report),
              "catalogued tools:", len(report["tools"]))
    elif args.action == "parallel-research":
        from .parallel_research import run_network
        if args.auto:
            from .tool_registry import route_request
            routing = route_request(args.query)
            tool_keys = routing["tool_keys"]
            optimization = routing["enable_optimization"] and not args.no_optimization
        else:
            routing = {"routing_method": "explicit_user_selected_tools"}
            tool_keys = [key.strip() for key in args.tools.split(",")]
            optimization = not args.no_optimization
        report = run_network(
            args.query, tool_keys=tool_keys,
            offline=not args.online, optimize=optimization,
        )
        report["routing"] = routing
        print("Parallel scientific research:", save_json(args.out, report),
              "workers:", report["parallel_tool_count"],
              "known-model checks passed:", report["known_model_integration_passed"])
    elif args.action == "scientific-skills":
        from .skill_catalog import catalog, retrieve_skill_document
        report = retrieve_skill_document(args.inspect) if args.inspect else catalog()
        print("Read-only K-Dense skill index:", save_json(args.out,report))
    elif args.action == "federated-literature":
        from .federated_sources import search_federated
        report=search_federated(args.query,offline=not args.online)
        print("Federated public literature search:",save_json(args.out,report),
              "records:",len(report["records"]))
    elif args.action == "nasa-exoplanets":
        from .nasa_exoplanets import run_nasa_catalog_consistency
        report = run_nasa_catalog_consistency()
        print("NASA catalog comparison:", save_json(args.out, report),
              "planets:", report["observations_evaluated"],
              "within ten percent:", report["fraction_within_ten_percent"],
              "independent proof:", report["independent_empirical_validation"])
    elif args.action == "physics":
        print(json.dumps({
            "radius_m": args.radius_m,
            "circular_orbit_speed_m_s": circular_orbit_speed(args.radius_m),
        }))


if __name__ == "__main__":
    main()
