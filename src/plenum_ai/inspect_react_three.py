"""Audit official Inspect ReAct against same three original HumanEval coding tasks.

No custom model, grader, agent loop or sandbox. This module reads original
Inspect scorers and compares actual original task IDs, specification/test
content and model outputs with an immutable independent one-shot baseline.
Default invocation does not import Inspect, download weights or invoke models.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

from .inspect_original_coding import plan as one_shot_plan
from .inspect_cross_domain import permitted_report

SCHEMA="plenum-inspect-upstream-react-3-functional-v1"
REFERENCE_RUN="42346922772"
REACT_PROOF_RUN="42349665865"
REFERENCE_SOURCE_SHA="a54a5490574e3d357442839d29dbf128bf51b4c6"
N=3
EXPECTED_IDS={"HumanEval/0","HumanEval/1","HumanEval/2"}
ORIGINAL_REFERENCE_CORRECT=2
MAX_TURNS=6
MAX_MESSAGES=14
MAX_TOKENS=256


def plan():
    source=one_shot_plan()
    if (source["candidate_model"]!="Qwen/Qwen3-1.7B"
        or source["candidate_revision"]!="70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"):
        raise ValueError("Frozen reviewed model has changed")
    return {
        "schema":SCHEMA,
        "upstream_agent":"Inspect AI react(), unchanged",
        "upstream_scorer":"original inspect_evals/humaneval verify()",
        "official_dataset":source["official_dataset"],
        "official_dataset_revision":source["official_dataset_revision"],
        "inspect_ai_version":source["inspect_ai_version"],
        "inspect_evals_version":source["inspect_evals_version"],
        "model":source["candidate_model"],
        "model_revision":source["candidate_revision"],
        "baseline_run_id":REFERENCE_RUN,
        "already_verified_single_agent_run_id":REACT_PROOF_RUN,
        "expected_original_questions":N,
        "max_turns_per_task":MAX_TURNS,
        "max_messages_per_task":MAX_MESSAGES,
        "max_output_tokens_per_turn":MAX_TOKENS,
        "sandbox":"original Inspect Docker with default network disabled",
        "paid_api_calls":0,
        "local_generation_calls":0,
        "actual_tool_calls":0,
        "actual_tool_responses":0,
        "paired_original_questions_verified":False,
        "original_scorer_verified":False,
        "original_inference_executed":False,
        "automatic_model_promotion":False,
        "AGI_demonstrated":False,
        "limitations":"Three historical public potentially contaminated programs; same-case one-shot comparison is not novel repository repair, sustained planning or AGI.",
    }


def original_paths(root):
    directory=Path(root)
    if directory.is_absolute() or ".." in directory.parts:
        raise ValueError("Original evidence must remain repository-relative")
    return (directory/("run-"+REFERENCE_RUN+".json"),
            directory/("run-"+REFERENCE_RUN+"-raw.zip"))


def verify_original_evidence(root):
    report_path,raw_path=original_paths(root)
    if not report_path.is_file() or not raw_path.is_file():
        raise FileNotFoundError("Original independent 3-question coding baseline not archived")
    summary=json.loads(report_path.read_text(encoding="utf-8"))
    if (summary.get("schema")!="plenum-original-inspect-humaneval-code-v1"
        or summary.get("source_sha")!=REFERENCE_SOURCE_SHA
        or not summary.get("original_scoring_verified")
        or summary.get("attempted")!=N
        or summary.get("correct")!=ORIGINAL_REFERENCE_CORRECT
        or summary.get("candidate_revision")!=plan()["model_revision"]
        or summary.get("AGI_demonstrated") is not False):
        raise ValueError("Original official scorer provenance changed")
    originals=summary.get("original_eval_sha256")
    if not isinstance(originals,dict) or len(originals)!=1:
        raise ValueError("One original independent Inspect eval fingerprint required")
    with ZipFile(raw_path) as archive:
        names=archive.namelist()
        if (len(names)!=1 or set(names)!=set(originals)
            or Path(names[0]).name!=names[0]
            or not names[0].endswith(".eval")
            or sha256(archive.read(names[0])).hexdigest()!=originals[names[0]]):
            raise ValueError("Altered or unexpected archived original model log")
    return summary,raw_path


def _contract(sample):
    original=(getattr(sample,"metadata",None) or {}).get("test")
    if (not isinstance(original,str) or not original
        or not sample.input or not sample.target):
        raise ValueError("Original source specification and independent test missing")
    return sha256(json.dumps({
        "prompt":str(sample.input),"target":str(sample.target),
        "test":original
    },sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def original_and_candidate_rows(reference,agent):
    """Pure exact-ID/task-content grade comparator, no model calls."""
    if set(reference)!=EXPECTED_IDS or set(agent)!=EXPECTED_IDS:
        raise ValueError("Different original HumanEval question IDs")
    baseline_correct=agent_correct=fixes=regressions=0
    detail=[]
    for key in sorted(EXPECTED_IDS):
        old=reference[key];now=agent[key]
        if (not isinstance(old,dict) or not isinstance(now,dict)
            or old.get("contract")!=now.get("contract")
            or not isinstance(old.get("contract"),str)
            or type(old.get("correct")) is not bool or type(now.get("correct")) is not bool):
            raise ValueError("Original prompt, test or independent grade differs")
        passed_before=old["correct"]
        passed_after=now["correct"]
        baseline_correct+=passed_before
        agent_correct+=passed_after
        fixes+=not passed_before and passed_after
        regressions+=passed_before and not passed_after
        for n in ("tool_calls","tool_responses"):
            if type(now.get(n)) is not int or now[n]<0 or now[n]>MAX_MESSAGES:
                raise ValueError("Actual tool transcript counts missing or invalid")
        if now["tool_responses"]>now["tool_calls"]:
            raise ValueError("Unpaired original tool results")
        detail.append({
            "original_id":key,
            "original_question_test_sha256":old["contract"],
            "one_shot_correct":passed_before,
            "agent_correct":passed_after,
            "agent_tool_calls":now["tool_calls"],
            "agent_tool_responses":now["tool_responses"],
        })
    return {
        "attempted":N,
        "one_shot_correct":baseline_correct,
        "react_correct":agent_correct,
        "react_minus_one_shot":agent_correct-baseline_correct,
        "original_cases_repaired":fixes,
        "original_cases_regressed":regressions,
        "by_original_problem":detail,
        "actual_tool_calls":sum(x["agent_tool_calls"] for x in detail),
        "actual_tool_responses":sum(x["agent_tool_responses"] for x in detail)
    }


def audit(log_dir,source_dir):
    spec=plan()
    if (importlib.metadata.version("inspect-ai")!=spec["inspect_ai_version"]
        or importlib.metadata.version("inspect-evals")!=spec["inspect_evals_version"]):
        raise RuntimeError("Unreviewed original Inspect scorer release")
    from inspect_ai.log import list_eval_logs,read_eval_log
    from inspect_ai.scorer import CORRECT,INCORRECT
    from .inspect_react_coding import count_actual_tools

    summary,raw=verify_original_evidence(source_dir)
    root=Path(log_dir)
    if (root.is_absolute() or ".." in root.parts or not root.is_dir()
        or root.name!="inspect-react-three-logs"):
        raise ValueError("Only approved three-problem agent Inspect log directory")
    recorded=list_eval_logs(log_dir=str(root))
    if len(recorded)!=1:
        raise ValueError("Need exactly one original three-question agent evaluation")
    run=read_eval_log(recorded[0].name)
    if (run.status!="success" or run.error
        or not str(run.eval.task).endswith("react_original_humaneval")
        or run.eval.model!="hf/local"):
        raise ValueError("Original agent task/model execution did not succeed")
    args=run.eval.model_args or {}
    if (args.get("device")!="cpu"
        or not str(args.get("model_path","")).endswith(spec["model_revision"])
        or str(args.get("enable_thinking")).lower()!="false"
        or not isinstance(args.get("chat_template"),str)):
        raise ValueError("Pinned CPU model or reviewed ReAct template is incorrect")
    if len(run.samples or [])!=N:
        raise ValueError("Original agent tasks incomplete")
    got={}
    for sample in run.samples:
        key=str(sample.id)
        scores=list((sample.scores or {}).values())
        if (key in got or key not in EXPECTED_IDS or
            len(scores)!=1 or scores[0].value not in (CORRECT,INCORRECT)):
            raise ValueError("Original independently graded agent answer missing")
        calls,returns=count_actual_tools(sample.messages or [])
        got[key]={"contract":_contract(sample),"correct":scores[0].value==CORRECT,
                  "tool_calls":calls,"tool_responses":returns}

    with tempfile.TemporaryDirectory(prefix="plenum-original-code-baseline-") as temp:
        with ZipFile(raw) as z:
            filename=z.namelist()[0]
            file=Path(temp)/filename
            file.write_bytes(z.read(filename))
        prev=read_eval_log(str(file))
        if (prev.status!="success" or prev.error or
            prev.eval.task not in ("humaneval","inspect_evals/humaneval") or
            len(prev.samples or [])!=N):
            raise ValueError("Altered original official reference task")
        old={}
        for sample in prev.samples:
            key=str(sample.id)
            scores=list((sample.scores or {}).values())
            if (key in old or key not in EXPECTED_IDS or
                len(scores)!=1 or scores[0].value not in (CORRECT,INCORRECT)):
                raise ValueError("Original independent reference scores missing")
            old[key]={"contract":_contract(sample),"correct":scores[0].value==CORRECT}
    paired=original_and_candidate_rows(old,got)
    if paired["one_shot_correct"]!=ORIGINAL_REFERENCE_CORRECT:
        raise ValueError("Actual original reference scores disagree with archive")
    return {
        **spec,**paired,
        "original_scorer_verified":True,
        "paired_original_questions_verified":True,
        "original_source_log_sha256_verified":True,
        "original_inference_executed":True,
        "local_generation_calls":"multiple_within_fixed_turn_budget_not_falsely_estimated",
        "paid_api_calls":0,
        "automatic_model_promotion":False,
        "AGI_demonstrated":False
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check-reference")
    parser.add_argument("--audit-dir")
    parser.add_argument("--source-dir")
    parser.add_argument("--out",default="reports/react-three-plan.json")
    args=parser.parse_args()
    out=permitted_report(args.out)
    if args.audit_dir:
        if not args.source_dir:
            raise ValueError("Require exact original independent coding reference")
        result=audit(args.audit_dir,args.source_dir)
    elif args.check_reference:
        verify_original_evidence(args.check_reference)
        result={**plan(),"original_reference_verified":True}
    else:
        result=plan()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Reused upstream ReAct three original coding problems:",
          result.get("react_correct","not run"),"/",N)


if __name__=="__main__":
    main()
