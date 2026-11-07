"""Review stronger pinned pretrained model on matched official Inspect examples.

No homegrown benchmark, no LLM-judge: original Inspect Evals scores and
the archived 0.6B experiment provide the paired reference. CLI defaults to
a pure dry-run protocol without imports, downloads, GPUs or model calls.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

from .inspect_cross_domain import (
    INSPECT_AI, INSPECT_EVALS, TASKS, normalized_task,
    permitted_report,
)
from .hf_model import APPROVED_MODEL as BASE_MODEL, APPROVED_REVISION as BASE_REVISION

SCHEMA = "plenum-paired-qwen17-cross-domain-v1"
MODEL = "Qwen/Qwen3-1.7B"
REVISION = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
BASELINE_RUN = "42341668858"
BASELINE_COMMIT = "738e97210ff7e74bd957e06ca8b78cc14750178a"
SAMPLES_PER_TASK = 12
MAX_TOKENS = 128


def plan():
    if (BASE_MODEL != "Qwen/Qwen3-0.6B" or
        BASE_REVISION != "c1899de289a04d12100db370d81485cdf75e47ca"):
        raise ValueError("Reference model revision is no longer reviewed")
    return {
        "schema": SCHEMA,
        "framework": "UK AISI Inspect AI and Inspect Evals",
        "inspect_ai_version": INSPECT_AI,
        "inspect_evals_version": INSPECT_EVALS,
        "candidate_model": MODEL, "candidate_revision": REVISION,
        "reference_model": BASE_MODEL, "reference_revision": BASE_REVISION,
        "reference_run_id": BASELINE_RUN,
        "reference_source_commit": BASELINE_COMMIT,
        "tasks": list(TASKS),
        "samples_per_task": SAMPLES_PER_TASK,
        "total_matched_cases": 4 * SAMPLES_PER_TASK,
        "max_new_tokens": MAX_TOKENS,
        "enable_thinking": False,
        "gsm8k_fewshot": 0,
        "paid_api_calls": 0, "model_calls": 0,
        "inference_executed": False,
        "paired_scoring_verified": False,
        "automatic_promotion": False, "AGI_demonstrated": False,
        "limitations": "Four familiar public benchmark families; 12 matched first examples per family, different model sizes but unchanged questions, no independent AGI or novelty proof.",
    }


def baseline_paths(root):
    path = Path(root)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Only repository-relative reference evidence allowed")
    return (
        path / ("run-" + BASELINE_RUN + ".json"),
        path / ("run-" + BASELINE_RUN + "-raw.zip"),
    )


def verify_reference(root):
    """Verify exact archived original Inspect logs, not hand copied scores."""
    summary_path, archive_path = baseline_paths(root)
    if not summary_path.is_file() or not archive_path.is_file():
        raise FileNotFoundError("A fully archived 96-item reference is required before candidate inference")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (summary.get("schema") != "plenum-inspect-cross-domain-v1"
        or not summary.get("inference_executed")
        or not summary.get("independently_scored")
        or summary.get("attempted") != 96
        or summary.get("source_sha") != BASELINE_COMMIT
        or summary.get("model_revision") != BASE_REVISION
        or summary.get("AGI_demonstrated") is not False):
        raise ValueError("Invalid or unsupported reference benchmark")
    expected = summary.get("original_eval_sha256")
    if not isinstance(expected, dict) or len(expected) != 4:
        raise ValueError("Original Inspect raw log fingerprints missing")
    with ZipFile(archive_path) as z:
        names = z.namelist()
        if (len(names) != 4 or len(set(names)) != 4
            or any(Path(x).name != x or not x.endswith(".eval") for x in names)
            or set(names) != set(expected)):
            raise ValueError("Malformed or extra archived model logs")
        for name in names:
            content = z.read(name)
            if sha256(content).hexdigest() != expected[name]:
                raise ValueError("Original Inspect raw logs changed")
    return summary, archive_path


def grades(log):
    from inspect_ai.scorer import CORRECT, INCORRECT

    if log.status != "success" or log.error:
        raise ValueError("Unsuccessful official Inspect task")
    results = {}
    for sample in log.samples or []:
        key = str(sample.id)
        if not key or key in results:
            raise ValueError("Duplicate or absent example ID")
        scores = list((sample.scores or {}).values())
        if len(scores) != 1 or scores[0].value not in (CORRECT, INCORRECT):
            raise ValueError("Missing original independent binary grade")
        results[key] = scores[0].value == CORRECT
    return results


def audited_log(log, expected_rev, count):
    if normalized_task(log.eval.task) not in TASKS:
        raise ValueError("Unexpected benchmark task")
    args = log.eval.model_args or {}
    if (log.eval.model != "hf/local" or
        not str(args.get("model_path", "")).endswith(expected_rev)
        or args.get("device") != "cpu"
        or str(args.get("enable_thinking")).lower() != "false"):
        raise ValueError("Unexpected model, checkpoint, CPU or generation configuration")
    got = grades(log)
    if len(got) != count:
        raise ValueError("Unexpected number of original independent scores")
    return normalized_task(log.eval.task), got


def compare_matched(previous, current):
    """Pure independent paired-grade arithmetic; both inputs are official grades."""
    if set(previous) != set(TASKS) or set(current) != set(TASKS):
        raise ValueError("Missing or unexpected official task family")
    paired = {}
    for name in TASKS:
        past = previous[name]
        now = current[name]
        if (len(past) != SAMPLES_PER_TASK or len(now) != SAMPLES_PER_TASK
            or set(past) != set(now)
            or any(type(value) is not bool for value in list(past.values())+list(now.values()))):
            raise ValueError("Reference/candidate example IDs, counts or grades differ")
        better = sum((not past[k]) and now[k] for k in past)
        worse = sum(past[k] and (not now[k]) for k in past)
        prior_correct = sum(past.values())
        candidate_correct = sum(now.values())
        paired[name] = {
            "attempted": SAMPLES_PER_TASK,
            "reference_correct": prior_correct,
            "candidate_correct": candidate_correct,
            "candidate_minus_reference": candidate_correct-prior_correct,
            "paired_improved": better,
            "paired_regressed": worse,
            "example_ids_sha256": sha256(
                "\n".join(sorted(past)).encode("utf-8")).hexdigest(),
            "candidate_incorrect_ids": [k for k in past if not now[k]],
            "original_scorer": "Inspect Evals",
        }
    return paired


def select_matching_reference(original_grades, candidate_grades):
    """Match by actual Inspect sample ID; log completion order is not dataset order.

    Official Inspect evaluator records may arrive in completion order. Taking
    the first twelve from a twenty-four-response reference silently mismatches
    source questions despite identical underlying fixed datasets.
    """
    if (len(original_grades) != 24
        or len(candidate_grades) != SAMPLES_PER_TASK
        or not set(candidate_grades).issubset(set(original_grades))):
        raise ValueError("Reference and candidate must share exact original IDs")
    return {key: original_grades[key] for key in candidate_grades}


def question_contract(log):
    """Preserve exact task inputs and scoring targets, not only answer IDs."""
    record = {}
    for sample in log.samples or []:
        identifier = str(sample.id)
        if not identifier or identifier in record:
            raise ValueError("Invalid or duplicate independently scored question")
        record[identifier] = (
            sample.input, sample.target, str(sample.choices),
        )
    return record


def audit(candidate_dir, reference_dir):
    if importlib.metadata.version("inspect-ai") != INSPECT_AI:
        raise RuntimeError("Inspect AI upstream release changed")
    if importlib.metadata.version("inspect-evals") != INSPECT_EVALS:
        raise RuntimeError("Inspect Evals upstream release changed")
    from inspect_ai.log import list_eval_logs, read_eval_log

    baseline_summary, archive = verify_reference(reference_dir)
    candidate = Path(candidate_dir)
    if (candidate.is_absolute() or ".." in candidate.parts
        or candidate.name != "inspect-paired-logs" or not candidate.is_dir()):
        raise ValueError("Missing reviewable candidate log directory")
    candidate_entries = list_eval_logs(log_dir=str(candidate))
    if len(candidate_entries) != 4:
        raise ValueError("Need all four candidate benchmark families")
    current = {}
    candidate_questions = {}
    for entry in candidate_entries:
        log = read_eval_log(entry.name)
        name, marks = audited_log(log, REVISION, SAMPLES_PER_TASK)
        if name in current:
            raise ValueError("Repeated candidate task")
        current[name] = marks
        candidate_questions[name] = question_contract(log)

    previous = {}
    verified_question_contracts = {}
    with tempfile.TemporaryDirectory(prefix="plenum-reference-") as temp:
        with ZipFile(archive) as z:
            for fname in z.namelist():
                if Path(fname).name != fname:
                    raise ValueError("Unsafe reference filename")
                file = Path(temp) / fname
                file.write_bytes(z.read(fname))
                log = read_eval_log(str(file))
                name, marks = audited_log(log, BASE_REVISION, 24)
                if name in previous:
                    raise ValueError("Repeated reference task")
                # Inspect logs arrive in completion order. Match ONLY the
                # actual candidate sample IDs, not the first 12 log records.
                previous[name] = select_matching_reference(marks, current[name])
                source_questions = question_contract(log)
                expected_questions = candidate_questions[name]
                if any(source_questions[k] != expected_questions[k]
                       for k in expected_questions):
                    raise ValueError("Paired prompts, choices or scoring targets differ")
                verified_question_contracts[name] = True
    if set(previous) != set(TASKS) or set(current) != set(TASKS):
        raise ValueError("Missing one of four benchmark families")

    paired = compare_matched(previous, current)
    if set(verified_question_contracts) != set(TASKS):
        raise ValueError("Original sample content was not checked across all domains")
    return {
        **plan(),
        "reference_source_sha": baseline_summary["source_sha"],
        "reference_raw_log_fingerprints_checked": True,
        "original_prompt_and_scoring_targets_matched": True,
        "inference_executed": True,
        "paired_scoring_verified": True,
        "model_calls": 48,
        "total_matched_cases": 48,
        "reference_correct": sum(x["reference_correct"] for x in paired.values()),
        "candidate_correct": sum(x["candidate_correct"] for x in paired.values()),
        "by_family": paired,
        "automatic_promotion": False, "AGI_demonstrated": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-reference", help="Preflight only; require archived Inspect baseline")
    parser.add_argument("--audit-dir")
    parser.add_argument("--reference-dir")
    parser.add_argument("--out", default="reports/paired-qwen-plan.json")
    args = parser.parse_args()
    dest = permitted_report(args.out)
    if args.audit_dir:
        if not args.reference_dir:
            raise ValueError("Must supply original evidence reference")
        report = audit(args.audit_dir, args.reference_dir)
    elif args.check_reference:
        verify_reference(args.check_reference)
        report = {**plan(), "reference_archive_verified": True}
    else:
        report = plan()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Paired Qwen:", "verified" if report.get("paired_scoring_verified") else "preflight only",
          "| model calls in plan", report["model_calls"])


if __name__ == "__main__":
    main()
