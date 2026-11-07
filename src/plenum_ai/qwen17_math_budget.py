"""Official Inspect paired 128-vs-256 token math ablation on frozen Qwen3-1.7B.

This is a POST-HOC format confound diagnostic. The same twelve official
GSM8K questions were already scored at 128 output tokens in original run
42342242561. Reference raw logs have been independently archived after
an auditor ordering fix. No model is used in default planning/auditing.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile
from hashlib import sha256

from .inspect_cross_domain import INSPECT_AI, INSPECT_EVALS, permitted_report
from .inspect_paired_qwen import REVISION, MODEL, audited_log, question_contract
from .gsm8k_token_budget import compare, _token_counts

SCHEMA = "plenum-qwen17-gsm8k-128-vs-256-v1"
ORIGINAL_RUN = "42342242561"
ORIGINAL_SOURCE_SHA = "dbd7636a936f8090a11031debf685dea40a1d91c"
ORIGINAL_COUNT = 12
ORIGINAL_CORRECT = 1
ORIGINAL_AT_CAP = 10


def plan():
    if (MODEL != "Qwen/Qwen3-1.7B"
        or REVISION != "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"):
        raise ValueError("Candidate model source no longer reviewed")
    return {
        "schema": SCHEMA,
        "model": MODEL,
        "model_revision": REVISION,
        "inspect_ai_version": INSPECT_AI,
        "inspect_evals_version": INSPECT_EVALS,
        "source_run": ORIGINAL_RUN,
        "source_commit": ORIGINAL_SOURCE_SHA,
        "task": "inspect_evals/gsm8k",
        "question_count": ORIGINAL_COUNT,
        "original_max_tokens": 128,
        "retest_max_tokens": 256,
        "fewshot": 0,
        "enable_thinking": False,
        "paid_api_calls": 0,
        "local_generation_calls": 0,
        "inference_executed": False,
        "original_question_contracts_verified": False,
        "independently_scored": False,
        "automatic_model_promotion": False,
        "AGI_demonstrated": False,
        "limitations": "Twelve public historical post-hoc math cases, potential pretraining overlap; not statistical model selection, genuine new learning, AGI or proof of reliable mathematics.",
    }


def original_paths(root):
    d = Path(root)
    if d.is_absolute() or ".." in d.parts:
        raise ValueError("Only repository-relative original archived evidence")
    return (d/("run-"+ORIGINAL_RUN+".json"),
            d/("run-"+ORIGINAL_RUN+"-raw.zip"))


def verify_original(root):
    summary_path, archive = original_paths(root)
    if not summary_path.is_file() or not archive.is_file():
        raise FileNotFoundError("Previously independently archived 1.7B source missing")
    record = json.loads(summary_path.read_text(encoding="utf-8"))
    if (record.get("schema") != "plenum-paired-qwen17-cross-domain-v1"
        or not record.get("paired_scoring_verified")
        or not record.get("original_prompt_and_scoring_targets_matched")
        or record.get("source_sha") != ORIGINAL_SOURCE_SHA
        or record.get("candidate_revision") != REVISION
        or record.get("candidate_correct") != 21
        or record.get("by_family",{}).get("gsm8k",{}).get("candidate_correct") != ORIGINAL_CORRECT
        or record.get("AGI_demonstrated") is not False):
        raise ValueError("Original source provenance or official scores changed")
    files = record.get("original_eval_sha256")
    if not isinstance(files, dict) or len(files) != 4:
        raise ValueError("Four original candidate SHA256 records required")
    with ZipFile(archive) as zipped:
        names = zipped.namelist()
        if (len(names)!=4 or set(names)!=set(files)
            or any(Path(n).name!=n or not n.endswith(".eval") for n in names)):
            raise ValueError("Unexpected original source ZIP structure")
        for fname in names:
            if sha256(zipped.read(fname)).hexdigest()!=files[fname]:
                raise ValueError("Tampered original 1.7B model log")
    return record, archive


def audit(log_dir, source_dir):
    if (importlib.metadata.version("inspect-ai") != INSPECT_AI
        or importlib.metadata.version("inspect-evals") != INSPECT_EVALS):
        raise RuntimeError("Unreviewed independent Inspect evaluator")
    from inspect_ai.log import list_eval_logs, read_eval_log
    summary, archived = verify_original(source_dir)
    path = Path(log_dir)
    if (path.is_absolute() or ".." in path.parts
        or path.name != "inspect-qwen17-math-budget-logs"
        or not path.is_dir()):
        raise ValueError("Missing approved original Inspect candidate log directory")
    logs = list_eval_logs(log_dir=str(path))
    if len(logs)!=1:
        raise ValueError("Exactly one original candidate GSM8K benchmark required")
    current = read_eval_log(logs[0].name)
    task, revised = audited_log(current, REVISION, ORIGINAL_COUNT)
    if task!="gsm8k":
        raise ValueError("Expected official GSM8K task")
    current_contract = question_contract(current)
    output_tokens = _token_counts(current)

    with tempfile.TemporaryDirectory(prefix="plenum-q17-mathref-") as td:
        with ZipFile(archived) as z:
            originals = [name for name in z.namelist() if "_gsm8k_" in name]
            if len(originals)!=1:
                raise ValueError("Missing exactly one original 1.7B math benchmark")
            file=Path(td)/Path(originals[0]).name
            file.write_bytes(z.read(originals[0]))
        original = read_eval_log(str(file))
        task, first = audited_log(original, REVISION, ORIGINAL_COUNT)
        if task!="gsm8k":
            raise ValueError("Wrong source family")
        original_contract = question_contract(original)
        first_tokens = _token_counts(original)

    if (set(first)!=set(revised)
        or any(original_contract[k]!=current_contract[k] for k in revised)):
        raise ValueError("Original math question IDs/prompts/scorer targets changed")
    scores=compare(first,revised,first_tokens,output_tokens,count=ORIGINAL_COUNT)
    if (scores["baseline_correct"]!=ORIGINAL_CORRECT
        or scores["baseline_at_token_cap_count"]!=ORIGINAL_AT_CAP
        or scores["baseline_at_token_cap_correct"]!=0):
        raise ValueError("Original recorded math result does not match observed source")
    return {
        **plan(),
        **scores,
        "inference_executed": True,
        "independently_scored": True,
        "original_question_contracts_verified": True,
        "original_log_sha256_verified": True,
        "source_recovery_sha": summary["recovery_sha"],
        "local_generation_calls": ORIGINAL_COUNT,
        "paid_api_calls": 0,
        "automatic_model_promotion": False,
        "AGI_demonstrated": False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-original")
    parser.add_argument("--audit-dir")
    parser.add_argument("--source-dir")
    parser.add_argument("--out",default="reports/qwen17-math-budget-plan.json")
    args=parser.parse_args()
    output=permitted_report(args.out)
    if args.audit_dir:
        if not args.source_dir:
            raise ValueError("Original source directory required for audited outputs")
        result=audit(args.audit_dir,args.source_dir)
    elif args.check_original:
        verify_original(args.check_original)
        result={**plan(),"original_archive_verified":True}
    else:
        result=plan()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Frozen Qwen3-1.7B math 128/256: ",
          result.get("candidate_correct","not run"),
          "/",result["question_count"])


if __name__=="__main__":
    main()
