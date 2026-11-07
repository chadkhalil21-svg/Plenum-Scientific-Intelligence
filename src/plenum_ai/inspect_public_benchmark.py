"""Pre-registered real, third-party ARC science evaluations using Inspect.

The default is an offline execution plan. Actual inference uses the pinned
Qwen3-0.6B checkpoint and the unmodified official Inspect Evals ARC tasks.
The independent Inspect scorers, not the model, decide correctness.

Public historical ARC examples may have appeared in training. The result is a
limited baseline, not an unseen AGI examination or scientific discovery.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path

from .hf_model import APPROVED_MODEL, APPROVED_REVISION

SCHEMA="plenum-upstream-public-science-benchmark-v2"
INSPECT_VERSION="0.3.287"
EVALS_VERSION="0.27.0"
TASKS=("arc_easy","arc_challenge")
SAMPLE_LIMIT=12
MAX_TOKENS=48

def plan():
    if APPROVED_MODEL!="Qwen/Qwen3-0.6B" or APPROVED_REVISION!="c1899de289a04d12100db370d81485cdf75e47ca":
        raise ValueError("The source checkpoint pin changed")
    return {
        "schema":SCHEMA, "framework":"UK AISI Inspect",
        "inspect_ai_version":INSPECT_VERSION,
        "inspect_evals_version":EVALS_VERSION,
        "model_id":APPROVED_MODEL, "model_revision":APPROVED_REVISION,
        "tasks":list(TASKS), "sample_limit_per_task":SAMPLE_LIMIT,
        "enable_thinking":False, "evaluation_variant":"nonthinking-v2",
        "max_generation_tokens":MAX_TOKENS, "max_model_connections":1,
        "paid_model_apis":False, "private_data_used":False,
        "model_training":False, "automatic_promotion":False,
        "inference_executed":False, "AGI_demonstrated":False,
        "limitations":"Official historical public ARC tasks; 12 per task, may overlap training; not a generalization or AGI claim.",
    }

def checked_path(raw):
    path=Path(raw)
    if (path.is_absolute() or ".." in path.parts or path.suffix!=".json"
        or not path.parts or path.parts[0]!="reports" or len(path.parts)>4):
        raise ValueError("Only short reports/*.json paths permitted")
    return path

def canonical_task(name):
    mapping={f"inspect_evals/{task}":task for task in TASKS}
    if name not in mapping:
        raise ValueError("Unknown or noncanonical upstream ARC task identifier")
    return mapping[name]

def audit(log_dir):
    """Read the official Inspect native scores; never reinterpret model text."""
    if importlib.metadata.version("inspect-ai")!=INSPECT_VERSION:
        raise RuntimeError("Inspect evaluator package version changed")
    if importlib.metadata.version("inspect-evals")!=EVALS_VERSION:
        raise RuntimeError("Inspect Evals package version changed")
    from inspect_ai.log import list_eval_logs, read_eval_log
    from inspect_ai.scorer import CORRECT, INCORRECT

    root=Path(log_dir)
    if root.is_absolute() or ".." in root.parts or not root.is_dir():
        raise ValueError("Missing bounded local evaluator logs")
    files=list_eval_logs(log_dir=str(root))
    if len(files)!=len(TASKS):
        raise ValueError("Missing or duplicate upstream science benchmark logs")
    summary={}
    for entry in files:
        log=read_eval_log(entry.name)
        if log.status!="success" or log.error:
            raise ValueError("Upstream evaluation failed")
        task=canonical_task(log.eval.task)
        if task not in TASKS or task in summary:
            raise ValueError("Unexpected or duplicated benchmark task")
        if not log.samples or len(log.samples)!=SAMPLE_LIMIT:
            raise ValueError("Scored sample count does not match preregistration")
        decisions=[]
        for sample in log.samples:
            scores=list((sample.scores or {}).values())
            if len(scores)!=1 or scores[0].value not in (CORRECT,INCORRECT):
                raise ValueError("Missing or unrecognized independent Inspect accuracy grade")
            decisions.append(scores[0].value==CORRECT)
        summary[task]={"attempted":len(decisions),"correct":sum(decisions),
                       "accuracy":round(sum(decisions)/len(decisions),6),
                       "scorer":"Inspect Evals original public task scorer"}
    if set(summary)!=set(TASKS):
        raise ValueError("Missing one of the precommitted tasks")
    return {**plan(),"inference_executed":True,"independently_scored":True,
            "total_attempted":sum(x["attempted"] for x in summary.values()),
            "total_correct":sum(x["correct"] for x in summary.values()),
            "domain_scores":summary,
            "automatic_promotion":False, "AGI_demonstrated":False}

def main():
    cli=argparse.ArgumentParser(description="Precommitted upstream science benchmark")
    cli.add_argument("--audit-dir",default=None)
    cli.add_argument("--out",default="reports/inspect-science-plan.json")
    args=cli.parse_args()
    result=audit(args.audit_dir) if args.audit_dir else plan()
    path=checked_path(args.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Official Inspect ARC evaluation:",result.get("total_correct","no inference"),
          "/",result.get("total_attempted","not run"))

if __name__=="__main__":
    main()
