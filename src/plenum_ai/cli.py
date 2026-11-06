"""Command-line interface. No paid services or unrestricted AI tool use."""
import argparse
import json
from pathlib import Path
from .evolve import default_benchmarks, evaluate_evolution
from .literature import search_papers
from .physics import circular_orbit_speed
from .research import make_report


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
    args = parser.parse_args()
    if args.action == "research":
        papers = search_papers(args.query)
        report = make_report(args.query, papers, model=args.model)
        print("Research inventory:", save_json(args.out, report), "papers:", len(papers))
    elif args.action == "improve":
        evaluation = evaluate_evolution(default_benchmarks())
        print("Improvement proposal:", save_json(args.out, evaluation),
              "accepted:", evaluation["accepted_for_proposal"])
    elif args.action == "physics":
        print(json.dumps({
            "radius_m": args.radius_m,
            "circular_orbit_speed_m_s": circular_orbit_speed(args.radius_m),
        }))


if __name__ == "__main__":
    main()
