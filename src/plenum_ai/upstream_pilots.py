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

def main():
    cli=argparse.ArgumentParser(description="Read-only upstream SDK compatibility check")
    cli.add_argument("--provider",choices=sorted(VERSIONS),required=True)
    cli.add_argument("--verify-library",action="store_true")
    cli.add_argument("--out",default="reports/upstream-pilot.json")
    args=cli.parse_args()
    path=Path(args.out)
    if (path.is_absolute() or ".." in path.parts or path.suffix!=".json"
        or not path.parts or path.parts[0]!="reports" or len(path.parts)>4):
        raise ValueError("Only relative bounded reports/*.json destinations allowed")
    report=inspect_upstream(args.provider) if args.verify_library else plan(args.provider)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(args.provider,"upstream API verified:",report["api_import_verified"],
          "model/API calls:",report["model_calls"],report["external_api_calls"])

if __name__=="__main__":
    main()
