"""Audit independent Inspect Evals grades across four published task families.

Uses the previously verified UK AISI Inspect stack, not a new evaluation
engine. Default prints an offline plan; inference runs in a separate
strictly gated workflow using existing pinned Qwen3-0.6B CPU weights.

These are historical PUBLIC tests that might be in pretraining; 96 scored
answers establish a reproducible baseline, not AGI or unseen generalization.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path

from .hf_model import APPROVED_MODEL, APPROVED_REVISION

SCHEMA = "plenum-inspect-cross-domain-v1"
INSPECT_AI = "0.3.287"
INSPECT_EVALS = "0.27.0"
TASKS = ("arc_challenge", "gsm8k", "hellaswag", "mmlu_0_shot")
SAMPLES_PER_TASK = 24
MAX_NEW_TOKENS = 128
TASK_LABELS = {
    "arc_challenge": "physical-science-reasoning",
    "gsm8k": "arithmetic-word-problems",
    "hellaswag": "commonsense-event-reasoning",
    "mmlu_0_shot": "multidisciplinary-knowledge",
}


def plan():
    if (APPROVED_MODEL != "Qwen/Qwen3-0.6B"
        or APPROVED_REVISION != "c1899de289a04d12100db370d81485cdf75e47ca"):
        raise ValueError("Unreviewed model revision")
    return {
        "schema": SCHEMA,
        "framework": "UK AI Security Institute Inspect/Inspect Evals",
        "inspect_ai_version": INSPECT_AI,
        "inspect_evals_version": INSPECT_EVALS,
        "model_id": APPROVED_MODEL,
        "model_revision": APPROVED_REVISION,
        "tasks": list(TASKS),
        "task_families": TASK_LABELS,
        "samples_per_task": SAMPLES_PER_TASK,
        "expected_total": len(TASKS)*SAMPLES_PER_TASK,
        "max_generation_tokens": MAX_NEW_TOKENS,
        "enable_thinking": False,
        "gsm8k_fewshot": 0,
        "model_calls": 0,
        "paid_api_calls": 0,
        "private_documents_used": False,
        "trained_or_promoted_model": False,
        "inference_executed": False,
        "AGI_demonstrated": False,
        "limitations": (
            "Public existing datasets, potential pretraining contamination; "
            "24 samples per family; no original code-synthesis or longitudinal-learning tasks."
        ),
    }


def permitted_report(raw):
    p = Path(raw)
    if (p.is_absolute() or ".." in p.parts or p.suffix != ".json"
        or not p.parts or p.parts[0] != "reports" or len(p.parts) > 4):
        raise ValueError("Reports must be relative JSON paths inside reports/")
    return p


def normalized_task(raw):
    if not isinstance(raw, str):
        raise ValueError("Inspect task identifier missing")
    prefix = "inspect_evals/"
    item = raw[len(prefix):] if raw.startswith(prefix) else raw
    if item not in TASKS:
        raise ValueError("Unregistered benchmark task")
    return item


def audit(log_dir):
    """Read official independent scorer outputs without self-grading any text."""
    if importlib.metadata.version("inspect-ai") != INSPECT_AI:
        raise RuntimeError("Unreviewed Inspect AI distribution")
    if importlib.metadata.version("inspect-evals") != INSPECT_EVALS:
        raise RuntimeError("Unreviewed Inspect Evals distribution")
    from inspect_ai.log import list_eval_logs, read_eval_log
    from inspect_ai.scorer import CORRECT, INCORRECT

    root = Path(log_dir)
    if (root.is_absolute() or ".." in root.parts or not root.is_dir()
        or root.name != "inspect-cross-logs"):
        raise ValueError("Missing approved Inspect log directory")
    logs = list_eval_logs(log_dir=str(root))
    if len(logs) != len(TASKS):
        raise ValueError("Missing or duplicated official task logs")
    by_family = {}
    all_ids = set()
    for item in logs:
        entry = read_eval_log(item.name)
        if entry.status != "success" or entry.error:
            raise ValueError("Official benchmark did not finish successfully")
        task = normalized_task(entry.eval.task)
        if task in by_family:
            raise ValueError("Duplicate task")
        config = entry.eval.model_args
        if (entry.eval.model != "hf/local"
            or not str(config.get("model_path", "")).endswith(APPROVED_REVISION)
            or config.get("device") != "cpu"
            or str(config.get("enable_thinking")).lower() != "false"):
            raise ValueError("Model origin, runtime or nonthinking configuration drifted")
        if not entry.samples or len(entry.samples) != SAMPLES_PER_TASK:
            raise ValueError("Unscored or partial task")
        correct = 0
        family_ids = []
        failed = []
        for sample in entry.samples:
            sample_id = str(sample.id)
            if not sample_id or sample_id in all_ids:
                raise ValueError("Duplicate or missing sample id across benchmark")
            all_ids.add(sample_id)
            family_ids.append(sample_id)
            scores = list((sample.scores or {}).values())
            if len(scores) != 1 or scores[0].value not in (CORRECT, INCORRECT):
                raise ValueError("Missing or non-binary independent scorer")
            is_correct = scores[0].value == CORRECT
            correct += is_correct
            if not is_correct:
                failed.append(sample_id)
        by_family[task] = {
            "family": TASK_LABELS[task],
            "attempted": SAMPLES_PER_TASK,
            "correct": correct,
            "accuracy": round(correct/SAMPLES_PER_TASK, 6),
            "sample_ids_sha256": sha256(
                "\n".join(sorted(family_ids)).encode("utf-8")
            ).hexdigest(),
            "incorrect_sample_ids": failed,
            "scoring": "unaltered Inspect Evals independent original scorer",
        }
    if set(by_family) != set(TASKS) or len(all_ids) != plan()["expected_total"]:
        raise ValueError("Task-family or sample-count mismatch")
    return {
        **plan(),
        "inference_executed": True,
        "independently_scored": True,
        "model_calls": len(all_ids),
        "attempted": len(all_ids),
        "correct": sum(x["correct"] for x in by_family.values()),
        "by_family": by_family,
        "AGI_demonstrated": False,
        "trained_or_promoted_model": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir")
    parser.add_argument("--out", default="reports/inspect-cross-plan.json")
    args = parser.parse_args()
    output = permitted_report(args.out)
    record = audit(args.audit_dir) if args.audit_dir else plan()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Inspect cross-domain:", record.get("correct", "plan only"),
          "/", record.get("attempted", "not executed"),
          "| AGI demonstrated:", record["AGI_demonstrated"])


if __name__ == "__main__":
    main()
