"""Recover original real ReAct tool-call failure; no original inference rerun.

Read Inspect's actual original .eval log and preserve a negative observation,
not a fabricated HumanEval pass or an imagined autonomous repair.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path

from .inspect_cross_domain import INSPECT_AI,permitted_report
from .inspect_react_coding import count_actual_tools

SCHEMA="plenum-original-react-tool-failure-v1"
ORIGINAL_RUN="42347377474"
ORIGINAL_SHA="054957ba0ce63004257f409d228da9f049f51680"
EXPECTED_CAUSE="Object of type Undefined is not JSON serializable"


def plan():
    return {
        "schema":SCHEMA,"original_run_id":ORIGINAL_RUN,
        "original_source_sha":ORIGINAL_SHA,
        "original_cause":EXPECTED_CAUSE,
        "original_log_reviewed":False,
        "independent_functional_grade_available":False,
        "agent_tool_calls":0,"tool_result_messages":0,
        "model_error_recovery_demonstrated":False,
        "model_retrained_or_deployed":False,"AGI_demonstrated":False,
    }


def audit(log_dir):
    if importlib.metadata.version("inspect-ai")!=INSPECT_AI:
        raise RuntimeError("Unreviewed original Inspect reader")
    from inspect_ai.log import list_eval_logs,read_eval_log
    directory=Path(log_dir)
    if (directory.is_absolute() or ".." in directory.parts
        or directory.name!="inspect-react-failed-original" or not directory.is_dir()):
        raise ValueError("Require only the retained original failed ReAct log")
    files=list_eval_logs(log_dir=str(directory))
    if len(files)!=1:
        raise ValueError("Expected one original failed agent execution")
    log=read_eval_log(files[0].name)
    if (log.status!="error"
        or not log.error
        or EXPECTED_CAUSE not in str(log.error.message)
        or str(log.eval.task)!="react_original_humaneval"
        or log.eval.model!="hf/local"):
        raise ValueError("Original ReAct failure's cause/task/model has changed")
    samples=log.samples or []
    if len(samples)!=1 or str(samples[0].id)!="HumanEval/0":
        raise ValueError("Unexpected source question, count or provenance")
    s=samples[0]
    if s.scores:
        raise ValueError("Failed pre-scoring run must not have a functional score")
    messages=s.messages or []
    calls,returned=count_actual_tools(messages)
    if (calls!=1 or returned!=1 or
        not any("NameError" in str(getattr(m,"content",""))
                and getattr(m,"role",None)=="tool" for m in messages)):
        raise ValueError("Genuine source tool call and tool error were not verified")
    return {
        **plan(),
        "original_log_reviewed":True,
        "unscored_execution":True,
        "agent_tool_calls":calls,
        "tool_result_messages":returned,
        "sandbox_tool_error_observed":True,
        "chat_template_error_observed":True,
        "independent_functional_grade_available":False,
        "model_error_recovery_demonstrated":False,
        "source_sample_id":str(s.id),
        "original_input_sha256":sha256(str(s.input).encode()).hexdigest(),
        "original_error_sha256":sha256(str(log.error.message).encode()).hexdigest(),
        "model_retrained_or_deployed":False,"AGI_demonstrated":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--audit-dir")
    parser.add_argument("--out",default="reports/react-failed-original-plan.json")
    args=parser.parse_args()
    out=permitted_report(args.out)
    record=audit(args.audit_dir) if args.audit_dir else plan()
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print("Failed original Inspect ReAct tool trace verified:",
          record["original_log_reviewed"],
          "| tool calls/returns:",record["agent_tool_calls"],record["tool_result_messages"])


if __name__=="__main__":
    main()
