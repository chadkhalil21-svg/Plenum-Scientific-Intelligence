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
    elif args.action == "physics":
        print(json.dumps({
            "radius_m": args.radius_m,
            "circular_orbit_speed_m_s": circular_orbit_speed(args.radius_m),
        }))


if __name__ == "__main__":
    main()
