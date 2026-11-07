"""Audit real model-generated code with unchanged upstream Inspect HumanEval tests.

This module DOES NOT write a benchmark or execute model code itself.
Original Inspect Evals HumanEval runs Python in its networkless Docker sandbox.
Default CLI only prints a bounded preflight without model calls.
"""
import argparse
import importlib.metadata
from hashlib import sha256
import json
from pathlib import Path

from .inspect_cross_domain import INSPECT_AI,INSPECT_EVALS,permitted_report
from .inspect_paired_qwen import MODEL,REVISION

SCHEMA="plenum-original-inspect-humaneval-code-v1"
TASK="inspect_evals/humaneval"
DATASET="openai/openai_humaneval"
DATASET_REV="7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544"
N=3
MAX_TOKENS=256


def plan():
    if (MODEL!="Qwen/Qwen3-1.7B"
        or REVISION!="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"):
        raise ValueError("Original model was not previously reviewed")
    return {
        "schema":SCHEMA,
        "framework":"original UK AISI Inspect AI / Inspect Evals",
        "inspect_ai_version":INSPECT_AI,
        "inspect_evals_version":INSPECT_EVALS,
        "official_task":TASK,
        "official_dataset":DATASET,
        "official_dataset_revision":DATASET_REV,
        "candidate_model":MODEL,
        "candidate_revision":REVISION,
        "expected_original_problems":N,
        "epochs":1,
        "maximum_output_tokens":MAX_TOKENS,
        "thinking_enabled":False,
        "scoring":"unchanged original inspect_evals/humaneval verify() scorer",
        "sandbox":"docker",
        "default_container_network_disabled":True,
        "run_timeout_minutes":32,
        "local_generation_requests":0,
        "paid_api_calls":0,
        "inference_executed":False,
        "model_generated_code_executed":False,
        "independent_function_tests_executed":False,
        "original_scoring_verified":False,
        "automatic_model_promotion":False,
        "AGI_demonstrated":False,
        "limitations":"Three public historical coding questions, possible pretraining overlap; one-shot program synthesis, not autonomous agentic coding, independent scientific discovery, or AGI."
    }


def _score_rows(samples):
    """Read original official binary C/I scores; never execute model output here."""
    from inspect_ai.scorer import CORRECT,INCORRECT
    if len(samples)!=N:
        raise ValueError("Original HumanEval dataset incomplete or duplicate")
    seen=set()
    output=[]
    for sample in samples:
        key=str(sample.id)
        if (not key.startswith("HumanEval/")
            or len(key)>100 or key in seen):
            raise ValueError("Unreviewed or duplicate original HumanEval sample ID")
        seen.add(key)
        values=list((sample.scores or {}).values())
        if len(values)!=1 or values[0].value not in (CORRECT,INCORRECT):
            raise ValueError("Original independent HumanEval grade missing")
        public_test=(getattr(sample,"metadata",None) or {}).get("test")
        generated=getattr(getattr(sample,"output",None),"completion",None)
        if (not isinstance(public_test,str) or not public_test
            or not sample.input or not sample.target
            or not isinstance(generated,str)):
            raise ValueError("Original source, source tests or model output missing")
        original=sha256(json.dumps({
            "sample_id":key,"prompt":str(sample.input),
            "target":str(sample.target),"test":public_test
        },sort_keys=True).encode()).hexdigest()
        output.append({
            "id":key,
            "correct":values[0].value==CORRECT,
            "question_and_original_test_sha256":original,
            "generated_text_sha256":sha256(generated.encode()).hexdigest(),
            "generated_chars":len(generated),
            "scorer":"original Inspect Evals HumanEval verify()"
        })
    return sorted(output,key=lambda x:x["id"])


def audit(raw_dir):
    if (importlib.metadata.version("inspect-ai")!=INSPECT_AI
        or importlib.metadata.version("inspect-evals")!=INSPECT_EVALS):
        raise RuntimeError("Original scorer versions not approved")
    from inspect_ai.log import list_eval_logs,read_eval_log
    root=Path(raw_dir)
    if (root.is_absolute() or ".." in root.parts
        or root.name!="inspect-original-coding-logs" or not root.is_dir()):
        raise ValueError("Require bounded original coding log directory")
    original=list_eval_logs(log_dir=str(root))
    if len(original)!=1:
        raise ValueError("Expected one original upstream coding evaluation")
    log=read_eval_log(original[0].name)
    if log.status!="success" or log.error:
        raise ValueError("Original coding evaluation was not successful")
    if log.eval.task not in (TASK,"humaneval"):
        raise ValueError("Incorrect original upstream coding task")
    args=log.eval.model_args or {}
    if (log.eval.model!="hf/local" or args.get("device")!="cpu"
        or not str(args.get("model_path","")).endswith(REVISION)
        or str(args.get("enable_thinking")).lower()!="false"):
        raise ValueError("Original model and source revision not verified")
    rows=_score_rows(log.samples or [])
    return {
        **plan(),
        "inference_executed":True,
        "model_generated_code_executed":True,
        "independent_function_tests_executed":True,
        "original_scoring_verified":True,
        "attempted":N,
        "correct":sum(row["correct"] for row in rows),
        "failures":[row["id"] for row in rows if not row["correct"]],
        "samples":rows,
        "local_generation_requests":N,
        "paid_api_calls":0,
        "automatic_model_promotion":False,
        "AGI_demonstrated":False
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--audit-dir")
    parser.add_argument("--out",default="reports/original-coding-plan.json")
    args=parser.parse_args()
    dest=permitted_report(args.out)
    result=audit(args.audit_dir) if args.audit_dir else plan()
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Original code-scoring result:",
          result.get("correct","not run"),"/",result.get("attempted",N))


if __name__=="__main__":
    main()
