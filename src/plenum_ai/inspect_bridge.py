"""Opt-in real Inspect AI evaluation smoke with frozen public answers."""
import argparse
import importlib.metadata
import json
from pathlib import Path

PIN = "0.3.287"
ROWS = (
    {"id":"correct","prompt":"What is 2 + 2?","target":"4","reply":"4"},
    {"id":"incorrect","prompt":"What is 3 * 3?","target":"9","reply":"8"},
)

def plan():
    return {"schema":"plenum-inspect-smoke-v1","upstream":"UKGovernmentBEIS/inspect_ai",
            "version":PIN,"execution_authorized":False,"model_calls":0,
            "external_api_calls":0,"AGI_demonstrated":False}

def smoke():
    """Run the installed upstream framework with zero model/API inference."""
    if importlib.metadata.version("inspect-ai") != PIN:
        raise RuntimeError("Unreviewed Inspect version")
    from inspect_ai import Task, eval as inspect_eval
    from inspect_ai.dataset import Sample
    from inspect_ai.model import ModelOutput
    from inspect_ai.scorer import CORRECT, INCORRECT, match
    from inspect_ai.solver import solver

    replies={row["id"]:row["reply"] for row in ROWS}
    @solver
    def replay():
        async def solve(state, generate):
            state.output=ModelOutput.from_content(
                model="plenum/offline-replay",content=replies[str(state.sample_id)])
            return state
        return solve
    task=Task(
        dataset=[Sample(id=r["id"],input=r["prompt"],target=r["target"]) for r in ROWS],
        solver=replay(),scorer=match(location="exact",ignore_case=False),
        time_limit=60,
    )
    logs=inspect_eval(task,model=None,log_dir="reports/inspect-logs",
                      display="none",fail_on_error=True,log_samples=True)
    if len(logs)!=1 or logs[0].status!="success" or not logs[0].samples:
        raise RuntimeError("Inspect smoke evaluation failed")
    scored={str(s.id):s.scores["match"].value for s in logs[0].samples
            if s.scores and "match" in s.scores}
    if scored!={"correct":CORRECT,"incorrect":INCORRECT}:
        raise RuntimeError("Inspect scorer did not correctly reject the wrong answer")
    return {**plan(),"execution_authorized":True,"inspect_executed":True,
            "verified_samples":len(scored)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--out",default="reports/inspect-smoke.json")
    args=parser.parse_args()
    out=Path(args.out)
    if (out.is_absolute() or ".." in out.parts or out.suffix!=".json" or
        not out.parts or out.parts[0]!="reports" or len(out.parts)>4):
        raise ValueError("Only short JSON report paths within reports/ allowed")
    result=smoke() if args.execute else plan()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Inspect:", "real smoke completed" if args.execute else "plan only",
          "| model calls",result["model_calls"])

if __name__=="__main__":
    main()
