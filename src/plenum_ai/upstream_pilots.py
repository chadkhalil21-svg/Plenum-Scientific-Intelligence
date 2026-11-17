"""Read-only optional SDK checks; no agent, model, embedding, or network calls."""
import argparse
import importlib.metadata
import json
from pathlib import Path

VERSIONS={"openhands":"1.60.1","paperqa":"2026.8.12"}
PACKAGES={"openhands":"openhands-sdk","paperqa":"paper-qa"}
SCHEMA="plenum-upstream-pilots-v1"

def plan(provider):
    if provider not in VERSIONS:
        raise ValueError("Unsupported upstream provider")
    return {
        "schema":SCHEMA, "provider":provider,
        "distribution":PACKAGES[provider],
        "expected_version":VERSIONS[provider],
        "api_import_verified":False, "agent_executed":False,
        "documents_indexed":False, "model_calls":0,
        "external_api_calls":0, "deployment":False,
        "AGI_demonstrated":False,
    }

def inspect_upstream(provider):
    """Inspect public Python classes. Never instantiate agents, Docs or LLMs."""
    report=plan(provider)
    try:
        current=importlib.metadata.version(PACKAGES[provider])
    except importlib.metadata.PackageNotFoundError as e:
        raise RuntimeError("Install the separately pinned optional dependency first") from e
    if current!=VERSIONS[provider]:
        raise RuntimeError("Unreviewed upstream package version")
    if provider=="openhands":
        from openhands.sdk import Agent, Conversation, LLM, Tool
        from openhands.sdk.security.confirmation_policy import AlwaysConfirm
        for obj in (Agent, Conversation, LLM, Tool, AlwaysConfirm):
            if not isinstance(obj,type):
                raise RuntimeError("Reviewed OpenHands API changed")
        report["api_names"]=["Agent","Conversation","LLM","Tool","AlwaysConfirm"]
    else:
        from paperqa import Docs, Settings, ask
        if not isinstance(Docs,type) or not isinstance(Settings,type) or not callable(ask):
            raise RuntimeError("Reviewed PaperQA API changed")
        report["api_names"]=["Docs","Settings","ask"]
        report["citation_accuracy_evaluated"]=False
    report["api_import_verified"]=True
    return report

# Robin: adapted from Future-House/robin, robin/utils.py, commit
# 4a5cce310f3bc7663a67117db88af43b84733ffe (Copyright 2025 FutureHouse,
# Apache-2.0). Preserves uniform sampling without replacement; bounds
# inputs and uses a local PRNG instead of changing the global random seed.
def robin_pair_schedule(n_hypotheses, n_games=None):
    """Generate a bounded reproducible comparison schedule, not judgments."""
    import itertools
    import random
    if type(n_hypotheses) is not int or not 2 <= n_hypotheses <= 32:
        raise ValueError("Choose 2..32 distinct hypotheses")
    possible = n_hypotheses * (n_hypotheses - 1) // 2
    if n_games is None:
        n_games = min(300, possible)
    if type(n_games) is not int or not 1 <= n_games <= min(300, possible):
        raise ValueError("Choose 1..300 feasible distinct pair comparisons")
    pairs = random.Random(621).sample(list(itertools.combinations(range(n_hypotheses), 2)), n_games)
    return {
        "schema": "plenum-robin-pair-schedule-v1",
        "upstream_commit": "4a5cce310f3bc7663a67117db88af43b84733ffe",
        "seed": 621, "n_hypotheses": n_hypotheses, "n_games": n_games,
        "pairs": [list(pair) for pair in pairs],
        "component_executed": True, "agent_executed": False,
        "model_calls": 0, "external_api_calls": 0, "AGI_demonstrated": False,
        "hypotheses_ranked": False, "deployment": False,
    }


# ScienceClaw: adapt only the canonical-DNA statistics branch of
# skills/sequence/scripts/sequence_tools.py, commit
# 894598cd3a90891a077c254566276bd379038bad (Apache-2.0).
# Input is a short public literal, never a local file, URL or agent prompt.
def scienceclaw_dna_statistics(sequence):
    """Bounded offline public DNA composition; no synthesis or experiment."""
    if (not isinstance(sequence, str) or not 1 <= len(sequence) <= 10000
            or any(base not in "ACGT" for base in sequence.upper())):
        raise ValueError("Choose a 1..10000-base public canonical DNA literal")
    if importlib.metadata.version("biopython") != "1.86":
        raise RuntimeError("Unreviewed optional Biopython package version")
    from Bio.Seq import Seq
    from Bio.SeqUtils import gc_fraction, molecular_weight
    seq_upper = sequence.upper()
    seq = Seq(seq_upper)
    composition = {base: seq_upper.count(base) for base in "ATCG"
                   if seq_upper.count(base) > 0}
    at = seq_upper.count("A") + seq_upper.count("T")
    gc = seq_upper.count("G") + seq_upper.count("C")
    statistics = {
        "type": "dna", "length": len(sequence),
        "gc_content": round(gc_fraction(seq) * 100, 2),
        "composition": composition,
        "molecular_weight": round(molecular_weight(seq, seq_type="DNA"), 2),
    }
    if gc > 0:
        statistics["at_gc_ratio"] = round(at / gc, 3)
    return {
        "schema": "plenum-scienceclaw-dna-statistics-v1",
        "upstream_commit": "894598cd3a90891a077c254566276bd379038bad",
        "biopython_version": "1.86", "statistics": statistics,
        "component_executed": True, "agent_executed": False,
        "model_calls": 0, "external_api_calls": 0, "AGI_demonstrated": False,
        "scientific_discovery_verified": False, "deployment": False,
    }


def main():
    cli=argparse.ArgumentParser(description="Read-only upstream SDK and bounded scientist-component checks")
    cli.add_argument("--provider",choices=sorted([*VERSIONS, "robin", "scienceclaw"]),required=True)
    cli.add_argument("--verify-library",action="store_true")
    cli.add_argument("--hypotheses", type=int, help="Robin comparison schedule size")
    cli.add_argument("--games", type=int, help="Optional Robin pair count")
    cli.add_argument("--public-dna", help="ScienceClaw public literal DNA only; never private sequence")
    cli.add_argument("--out",default="reports/upstream-pilot.json")
    args=cli.parse_args()
    path=Path(args.out)
    if (path.is_absolute() or ".." in path.parts or path.suffix!=".json"
        or not path.parts or path.parts[0]!="reports" or len(path.parts)>4):
        raise ValueError("Only relative bounded reports/*.json destinations allowed")
    if args.provider == "robin":
        if args.verify_library or args.public_dna is not None or args.hypotheses is None:
            cli.error("Robin requires --hypotheses and accepts optional --games")
        report = robin_pair_schedule(args.hypotheses, args.games)
    elif args.provider == "scienceclaw":
        if (args.verify_library or args.hypotheses is not None or args.games is not None
                or args.public_dna is None):
            cli.error("ScienceClaw requires --public-dna")
        report = scienceclaw_dna_statistics(args.public_dna)
    else:
        if any(x is not None for x in (args.hypotheses, args.games, args.public_dna)):
            cli.error("Component arguments are not supported by SDK-only providers")
        report = inspect_upstream(args.provider) if args.verify_library else plan(args.provider)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    label = "bounded component executed:" if "component_executed" in report else "upstream API verified:"
    result = report.get("component_executed", report.get("api_import_verified", False))
    print(args.provider, label, result,
          "model/API calls:", report["model_calls"], report["external_api_calls"])

if __name__=="__main__":
    main()
