"""Thin, opt-in wrapper for EleutherAI's upstream lm-evaluation-harness.

This code does NOT reimplement ARC/HellaSwag metrics or secretly call a model.
Default is dry-run. Actual external model/dataset downloads occur only when
the owner explicitly dispatches the separate manual GitHub Actions workflow.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess

UPSTREAM_REPO = "https://github.com/EleutherAI/lm-evaluation-harness"
UPSTREAM_LICENSE = "MIT"
UPSTREAM_TAG = "v0.4.13"
UPSTREAM_COMMIT = "ddd67220430a2470529f25fd5c05a576ca1057a0"
PACKAGE_VERSION = "0.4.13"
MODELS = {
    "Qwen/Qwen3-1.7B": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct":
        "31b70e2e869a7173562077fd711b654946d38674",
}
TASKS = ("arc_easy", "hellaswag")
OUTPUT = "reports/standard-evaluation"
MAX_EXAMPLES_PER_TASK = 16
SCHEMA = "plenum-reviewed-upstream-evaluation-v1"


def preflight(model, tasks, limit):
    if model not in MODELS:
        raise ValueError("Unsupported model; pin and review new weights first")
    if not isinstance(tasks,(list,tuple)) or not tasks or len(tasks)>len(TASKS):
        raise ValueError("Choose one or two approved benchmark tasks")
    if any(t not in TASKS for t in tasks) or len(set(tasks))!=len(tasks):
        raise ValueError("Unknown or duplicate benchmark task")
    if type(limit) is not int or not 1 <= limit <= MAX_EXAMPLES_PER_TASK:
        raise ValueError("Benchmark example budget must be an integer from 1 to 16")
    args = [
        "lm-eval", "run", "--model", "hf",
        "--model_args",
        "pretrained="+model+",revision="+MODELS[model]+",dtype=float32",
        "--tasks", *tasks, "--num_fewshot", "0",
        "--device", "cpu", "--batch_size", "1",
        "--limit", str(limit), "--seed", "20261107",
        "--output_path", OUTPUT,
    ]
    return {
        "schema": SCHEMA, "upstream_repository":UPSTREAM_REPO,
        "upstream_release":UPSTREAM_TAG,
        "reviewed_upstream_commit":UPSTREAM_COMMIT,
        "upstream_license":UPSTREAM_LICENSE,
        "upstream_package_version":PACKAGE_VERSION,
        "model":model,"model_revision":MODELS[model],
        "benchmarks":list(tasks),"limit_per_task":limit,
        "command":args,
        "model_download_enabled_by_default":False,
        "paid_api_enabled":False,
        "automatic_model_promotion":False,
        "AGI_demonstrated":False,
        "scientific_discovery_verified":False,
        "limitations":"Small sampled public multiple-choice tasks, potentially in training data. "
            "Built-in upstream metrics, not a valid AGI measure or new-science demonstration. "
            "Metrics, output compatibility and actual benchmark outcome are unverified until manually run.",
    }


def invoke(configuration):
    """Only callable after an explicit manual owner-selected --execute."""
    try:
        found=importlib.metadata.version("lm_eval")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError("Pinned lm_eval not installed. Install optional [standard_eval] first.") from exc
    if found!=PACKAGE_VERSION:
        raise RuntimeError("Upstream harness version not approved: "+found)
    Path(OUTPUT).mkdir(parents=True,exist_ok=True)
    # No shell, user-specified URLs, private datasets, or untrusted generated code.
    result=subprocess.run(configuration["command"],check=False,timeout=2400)
    if result.returncode!=0:
        raise RuntimeError("The upstream benchmark failed; do not report a model score")
    return result.returncode


def main():
    parser=argparse.ArgumentParser(description="Opt-in MIT-licensed upstream LLM evaluator")
    parser.add_argument("--model",choices=tuple(MODELS),required=True)
    parser.add_argument("--task",action="append",choices=TASKS,required=True)
    parser.add_argument("--limit",type=int,default=4)
    parser.add_argument("--execute",action="store_true",
                        help="Explicitly download and score public models and datasets")
    args=parser.parse_args()
    plan=preflight(args.model,args.task,args.limit)
    print(json.dumps({k:v for k,v in plan.items() if k!="command"},
                     indent=2,ensure_ascii=False))
    if args.execute:
        print("Executing reviewed upstream lm-evaluation-harness release",UPSTREAM_TAG)
        invoke(plan)
    else:
        print("Dry run only; model not downloaded and benchmark not executed")


if __name__=="__main__":
    main()
