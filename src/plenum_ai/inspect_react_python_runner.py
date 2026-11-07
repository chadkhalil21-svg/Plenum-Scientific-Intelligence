"""Invoke pinned Inspect original ReAct task with typed Python model args.

Inspect CLI -M model-arg parsing can split a multiline Jinja chat template
at commas, producing a list instead of a string. The supported Inspect
eval() Python API accepts an actual dict, eliminating that ambiguity.
No new agent, tool, grading engine, model checkpoint or weight modification.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from .inspect_cross_domain import permitted_report
from .inspect_paired_qwen import REVISION,MODEL
from .qwen3_chat_template import PATCH

SCHEMA="plenum-inspect-react-python-typed-model-args-v1"
TASK="src/plenum_ai/inspect_react_coding.py"


def model_args(model_path, template):
    if not isinstance(model_path,str) or not model_path or not model_path.endswith(REVISION):
        raise ValueError("Unreviewed original Qwen model path")
    if not isinstance(template,str) or not 100 < len(template) < 20000:
        raise ValueError("Original patched template must be a real string")
    if ("tool_call.function is string" not in template
        or PATCH not in template):
        raise ValueError("Original Qwen tool-history patch is absent")
    return {
        "model_path":model_path,
        "device":"cpu",
        "do_sample":False,
        "enable_thinking":False,
        "chat_template":template,
    }


def arguments(run, model_path, template):
    """Pass exact original source and TYPE-CHECKED kwargs to upstream eval."""
    config=model_args(model_path,template)
    return run(
        TASK,model="hf/local",model_args=config,
        limit=1,epochs=1,max_samples=1,max_sandboxes=1,
        max_connections=1,max_tokens=256,temperature=0,
        turn_limit=6,message_limit=14,time_limit=240,
        log_dir="reports/inspect-react-coding-logs",display="none"
    )


def plan():
    return {
        "schema":SCHEMA,
        "source_task":TASK,
        "provider":"official inspect_ai.eval Python API",
        "model":MODEL,"model_revision":REVISION,
        "model_arg_chat_template_type":"str",
        "model_arg_parser":"none; direct Python dict",
        "original_scorer":"inspect_evals/humaneval verify()",
        "one_public_original_task":True,
        "model_calls":0,
        "paid_api_calls":0,
        "actual_model_inference_executed":False,
        "original_functional_grade_verified":False,
        "AGI_demonstrated":False,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--model-path")
    parser.add_argument("--template-path")
    parser.add_argument("--out",default="reports/original-react-typed-plan.json")
    opts=parser.parse_args()
    dest=permitted_report(opts.out)
    if opts.execute:
        if opts.template_path!="reports/qwen3-react-template.jinja":
            raise ValueError("Unsupported original template location")
        if not opts.model_path:
            raise ValueError("Pinned model path required")
        from inspect_ai import eval as inspect_eval
        template=Path(opts.template_path).read_text(encoding="utf-8")
        output=arguments(inspect_eval,opts.model_path,template)
        if len(output)!=1:
            raise ValueError("Expected exactly one official Inspect task result")
        report={
            **plan(),
            "run_invoked":True,
            "eval_status":output[0].status,
            "model_arg_template_sha256":sha256(template.encode()).hexdigest(),
            "actual_model_inference_executed":True,
            "original_functional_grade_verified":False,
            "AGI_demonstrated":False,
        }
    else:
        report=plan()
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("Inspect typed ReAct args:",report.get("eval_status","preflight_only"),
          "original grade independently verified:",report["original_functional_grade_verified"])


if __name__=="__main__":
    main()
