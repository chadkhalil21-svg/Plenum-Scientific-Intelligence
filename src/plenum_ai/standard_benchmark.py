"""Reuse an established, version-reviewed model benchmark, not a bespoke AGI metric.

Default behavior is only a read-only execution plan. Never auto-download models
or datasets, call paid APIs, or run third-party frameworks during ordinary CI.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys

REGISTRY=Path(__file__).resolve().parents[2]/"protocols/reuse_first_registry.json"
SCHEMA="plenum-standard-benchmark-adapter-v1"
STANDARD_PACKAGE="lm-eval"
STANDARD_VERSION="0.4.13"
ALLOWED_MODELS={
    "Qwen/Qwen3-1.7B":"70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct":"31b70e2e869a7173562077fd711b654946d38674",
}
ALLOWED_TASKS=("arc_easy","hellaswag")
MAX_CASES=32
MAX_TIMEOUT_SECONDS=1200


def registry():
    r=json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries=r.get("software",[])
    expected=next((x for x in entries if x.get("name")=="EleutherAI LM Evaluation Harness"),None)
    if (r.get("schema")!="plenum-reuse-first-registry-v1"
        or not isinstance(expected,dict)
        or expected.get("release")!="v0.4.13"
        or expected.get("commit")!="ddd67220430a2470529f25fd5c05a576ca1057a0"
        or expected.get("license")!="MIT"
        or expected.get("adoption")!="guarded_optional_adapter"
        or expected.get("default_execution") is not False):
        raise ValueError("Reviewed benchmark registry altered")
    return expected


def plan(model,task="arc_easy",limit=8):
    info=registry()
    if model not in ALLOWED_MODELS or task not in ALLOWED_TASKS:
        raise ValueError("Only reviewed public models and academic benchmarks accepted")
    if type(limit) is not int or not 1<=limit<=MAX_CASES:
        raise ValueError("Limit must be an integer 1..32; full unbounded runs prohibited")
    # No shell invocation, provider tokens, arbitrary task paths or remote code.
    model_revision=ALLOWED_MODELS[model]
    cmd=[
        sys.executable,"-m","lm_eval","run",
        "--model","hf",
        "--model_args",f"pretrained={model},revision={model_revision},dtype=float32",
        "--tasks",task,
        "--limit",str(limit),
        "--device","cpu",
        "--batch_size","1",
        "--num_fewshot","0",
        "--output_path",f"reports/standard-evals/{task}-{limit}-{model.split('/')[-1]}",
    ]
    return {
        "schema":SCHEMA,
        "engine":"EleutherAI/lm-evaluation-harness",
        "reviewed_release":info["release"],
        "reviewed_upstream_commit":info["commit"],
        "license":info["license"],
        "requested_model":model,
        "model_revision":model_revision,
        "task":task,
        "sample_limit":limit,
        "command_argv":cmd,
        "execution_authorized":False,
        "paid_remote_inference":False,
        "model_weights_modified":False,
        "benchmark_data_released_as_proprietary":False,
        "AGI_demonstrated":False,
        "limitations":[
          "The standard benchmark is public and may be in model pretraining.",
          "A sample limit is for smoke testing, not statistical comparison.",
          "This provides task evaluation infrastructure, not an AGI certificate.",
          "Models and task data may be downloaded on explicit execution.",
          "No automatic caching or provenance of third-party benchmark inputs is asserted.",
        ],
    }


def execute(plan_record,*,approved=False,installed_version=None,runner=subprocess.run):
    if not approved:
        raise PermissionError("Third-party benchmark execution requires --execute")
    if not isinstance(plan_record,dict):
        raise ValueError("Invalid execution request")
    approved_plan=plan(
        plan_record.get("requested_model"),plan_record.get("task"),
        plan_record.get("sample_limit"))
    if plan_record != approved_plan:
        raise ValueError("Benchmark command or reviewed provenance was modified")
    installed=installed_version
    if installed is None:
        try:
            installed=importlib.metadata.version(STANDARD_PACKAGE)
        except importlib.metadata.PackageNotFoundError as err:
            raise RuntimeError('Install the reviewed optional package lm-eval==0.4.13 first') from err
    if installed!=STANDARD_VERSION:
        raise RuntimeError("Installed evaluator version does not match reviewed release")
    # No shell=True; bounded wall time. Runner must raise on failed subprocess.
    process=runner(approved_plan["command_argv"],check=True,timeout=MAX_TIMEOUT_SECONDS)
    return {"schema":SCHEMA,"exit_code":process.returncode,
            "benchmark_argv":approved_plan["command_argv"],
            "standard_framework_executed":True,
            "automatic_model_promotion":False,
            "AGI_demonstrated":False}


def main():
    p=argparse.ArgumentParser(description="Reuse a reviewed standard model benchmark")
    p.add_argument("--model",choices=tuple(ALLOWED_MODELS),required=True)
    p.add_argument("--task",choices=ALLOWED_TASKS,default="arc_easy")
    p.add_argument("--limit",type=int,default=8)
    p.add_argument("--execute",action="store_true",
                   help="Explicitly authorize downloads and bounded CPU benchmark run")
    p.add_argument("--out",default="reports/standard_benchmark_plan.json")
    args=p.parse_args()
    record=plan(args.model,args.task,args.limit)
    if args.execute:
        outcome=execute(record,approved=True)
        record["execution_result"]=outcome
    dest=Path(args.out)
    if dest.is_absolute() or ".." in dest.parts or dest.suffix!=".json" or len(dest.parts)>5:
        raise ValueError("Only a short relative JSON report path is accepted")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Standard benchmark:",args.task,"limit:",args.limit,
          "executed:",args.execute,"engine:",record["engine"])


if __name__=="__main__":
    main()
