"""Paired official GSM8K token-budget experiment on one frozen local model.

Compare *exactly the same* 24 public GSM8K questions at 128 versus 256
maximum tokens, reading original Inspect Evals scores and immutable raw logs.
Zero third-party inference APIs; no untrusted code execution or model training.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

from .hf_model import APPROVED_MODEL, APPROVED_REVISION
from .inspect_paired_qwen import verify_reference, audited_log
from .inspect_cross_domain import INSPECT_AI, INSPECT_EVALS, permitted_report

SCHEMA = "plenum-gsm8k-output-budget-ablation-v1"
TASK = "gsm8k"
REFERENCE_TOKENS = 128
CANDIDATE_TOKENS = 256
N = 24


def plan():
    if (APPROVED_MODEL != "Qwen/Qwen3-0.6B" or
        APPROVED_REVISION != "c1899de289a04d12100db370d81485cdf75e47ca"):
        raise ValueError("Approved source model checkpoint changed")
    return {
        "schema": SCHEMA, "task": TASK,
        "original_reference_run": "42341668858",
        "model_id": APPROVED_MODEL,
        "model_revision": APPROVED_REVISION,
        "inspect_ai_version": INSPECT_AI,
        "inspect_evals_version": INSPECT_EVALS,
        "question_count": N,
        "baseline_max_tokens": REFERENCE_TOKENS,
        "candidate_max_tokens": CANDIDATE_TOKENS,
        "enable_thinking": False,
        "gsm8k_fewshot": 0,
        "local_generation_calls": 0,
        "paid_api_calls": 0,
        "inference_executed": False,
        "official_scoring_verified": False,
        "model_promoted": False,
        "AGI_demonstrated": False,
        "limitations": "Same 24 public GSM8K examples selected after investigating token-cap failures. An exploratory output-length ablation, not learning, unseen transfer or AGI.",
    }


def compare(original, revised, before_tokens, after_tokens):
    """Score only externally supplied original Inspect grades and token counts."""
    keys = set(original)
    if (len(keys) != N or set(revised) != keys or
        set(before_tokens) != keys or set(after_tokens) != keys):
        raise ValueError("Original and revised questions do not have exact matching identifiers")
    for dictionary in (original, revised):
        if any(type(v) is not bool for v in dictionary.values()):
            raise ValueError("Non-binary official grade")
    for dictionary in (before_tokens, after_tokens):
        if any(type(v) is not int or v < 0 for v in dictionary.values()):
            raise ValueError("Missing or invalid original token count")
    capped = sorted(k for k in keys if before_tokens[k] >= REFERENCE_TOKENS)
    repaired = sorted(k for k in keys if not original[k] and revised[k])
    regressed = sorted(k for k in keys if original[k] and not revised[k])
    return {
        "question_count": N,
        "baseline_correct": sum(original.values()),
        "candidate_correct": sum(revised.values()),
        "candidate_minus_baseline": sum(revised.values()) - sum(original.values()),
        "improved_count": len(repaired),
        "regressed_count": len(regressed),
        "baseline_at_token_cap_count": len(capped),
        "baseline_at_token_cap_correct": sum(original[k] for k in capped),
        "candidate_correct_on_baseline_cap_group": sum(revised[k] for k in capped),
        "candidate_at_256_token_cap_count": sum(v >= CANDIDATE_TOKENS for v in after_tokens.values()),
        "improved_example_ids": repaired,
        "regressed_example_ids": regressed,
        "baseline_at_cap_ids": capped,
        "official_scorer": "Inspect Evals original match(numeric=True)",
    }


def _token_counts(log):
    samples = log.samples or []
    tokens = {}
    for sample in samples:
        key = str(sample.id)
        usage = getattr(getattr(sample, "output", None), "usage", None)
        count = getattr(usage, "output_tokens", None)
        if not key or key in tokens or type(count) is not int:
            raise ValueError("Original Inspect generation token counts are missing or duplicated")
        tokens[key] = count
    return tokens


def audit(candidate_dir, reference_dir):
    if (importlib.metadata.version("inspect-ai") != INSPECT_AI or
        importlib.metadata.version("inspect-evals") != INSPECT_EVALS):
        raise RuntimeError("Unreviewed official evaluation framework release")
    from inspect_ai.log import list_eval_logs, read_eval_log

    original_summary, original_zip = verify_reference(reference_dir)
    if (original_summary["by_family"].get(TASK, {}).get("attempted") != N or
        original_summary["by_family"][TASK]["correct"] != 6):
        raise ValueError("Unexpected 96-question baseline mathematics scores")
    candidate = Path(candidate_dir)
    if (candidate.is_absolute() or ".." in candidate.parts or
        not candidate.is_dir() or candidate.name != "inspect-gsm8k-budget-logs"):
        raise ValueError("Only the reviewed candidate Inspect output directory is allowed")
    candidate_logs = list_eval_logs(log_dir=str(candidate))
    if len(candidate_logs) != 1:
        raise ValueError("Exactly one official GSM8K candidate evaluation is required")
    new_log = read_eval_log(candidate_logs[0].name)
    task, revised = audited_log(new_log, APPROVED_REVISION, N)
    if task != TASK:
        raise ValueError("Candidate did not evaluate official GSM8K")
    new_tokens = _token_counts(new_log)

    with tempfile.TemporaryDirectory(prefix="plenum-gsm8k-ref-") as temp:
        with ZipFile(original_zip) as zipped:
            names = [x for x in zipped.namelist() if "_gsm8k_" in x]
            if len(names) != 1:
                raise ValueError("Expected exactly one original GSM8K log")
            source = Path(temp) / Path(names[0]).name
            source.write_bytes(zipped.read(names[0]))
        old_log = read_eval_log(str(source))
        task, original = audited_log(old_log, APPROVED_REVISION, N)
        if task != TASK:
            raise ValueError("Original reference task was not GSM8K")
        old_tokens = _token_counts(old_log)
    stats = compare(original, revised, old_tokens, new_tokens)
    return {
        **plan(), **stats,
        "inference_executed": True,
        "official_scoring_verified": True,
        "reference_original_SHA256_verified": True,
        "local_generation_calls": N,
        "paid_api_calls": 0,
        "model_promoted": False,
        "AGI_demonstrated": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect original GSM8K token-budget experiment")
    parser.add_argument("--check-reference")
    parser.add_argument("--audit-dir")
    parser.add_argument("--reference-dir")
    parser.add_argument("--out", default="reports/gsm8k-token-plan.json")
    args = parser.parse_args()
    output = permitted_report(args.out)
    if args.audit_dir:
        if not args.reference_dir:
            raise ValueError("Require original archived benchmark evidence")
        record = audit(args.audit_dir, args.reference_dir)
    elif args.check_reference:
        verify_reference(args.check_reference)
        record = {**plan(), "reference_evidence_verified": True}
    else:
        record = plan()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print("GSM8K 128 vs 256 token comparison:",
          record.get("candidate_correct","not run"), "/",
          record.get("question_count",N))


if __name__ == "__main__":
    main()
