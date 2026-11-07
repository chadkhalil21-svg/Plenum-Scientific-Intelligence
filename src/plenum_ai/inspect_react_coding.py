"""Thin adapter: original Inspect Evals HumanEval + built-in Inspect ReAct agent.

No custom planner, model evaluator, synthetic grader or production actions.
Model tools execute only in the upstream networkless Docker sandbox.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path

from inspect_ai import Task,task
from inspect_ai.agent import react
from inspect_ai.tool import python
from inspect_ai.log import list_eval_logs,read_eval_log
from inspect_ai.scorer import CORRECT,INCORRECT
from inspect_evals.humaneval.humaneval import humaneval

from plenum_ai.inspect_original_coding import plan as original_plan
from plenum_ai.inspect_cross_domain import permitted_report
from plenum_ai.inspect_paired_qwen import REVISION

SCHEMA="plenum-upstream-inspect-react-coding-agent-v1"
TASK_NAME="react_original_humaneval"
MAX_MESSAGES=14
MAX_TURNS=6
MAX_TOKENS=256
MAX_TOOL_SECONDS=20
PROMPT=(
    "You are a bounded Python programming assistant. Implement the supplied "
    "public function specification. You may use the python sandbox tool to "
    "test examples or debug syntax. Never request secrets, network access, "
    "or files outside the disposable task sandbox. "
    "Finish by submitting only a Python implementation for the requested "
    "function (include body and imports if needed); no commentary. "
    "This is one evaluation task, not a permission to modify repositories."
)


def plan():
    base=original_plan()
    return {
        "schema":SCHEMA,
        "upstream_scoring":"unchanged inspect_evals/humaneval verify()",
        "upstream_agent":"Inspect AI react()",
        "official_dataset":base["official_dataset"],
        "official_dataset_revision":base["official_dataset_revision"],
        "candidate_model":base["candidate_model"],
        "candidate_revision":REVISION,
        "sample_count":1,
        "max_messages":MAX_MESSAGES,
        "max_turns":MAX_TURNS,
        "max_output_tokens_per_turn":MAX_TOKENS,
        "tool_timeout_seconds":MAX_TOOL_SECONDS,
        "sandbox":"docker",
        "docker_network":"disabled by default",
        "paid_api_calls":0,
        "local_generation_calls":0,
        "inference_executed":False,
        "official_functional_test_scored":False,
        "actual_model_tool_calls":0,
        "actual_tool_results":0,
        "agent_loop_verified":False,
        "AGI_demonstrated":False,
        "automated_deployment":False,
        "limitations":"One old published code problem. Checks whether existing real ReAct agent can call tools and pass original tests, not AGI, reliable autonomy or novel repo repair."
    }


@task
def react_original_humaneval():
    original=humaneval()
    return Task(
        dataset=original.dataset,
        solver=react(
            prompt=PROMPT,
            tools=[python(timeout=MAX_TOOL_SECONDS)],
            attempts=1
        ),
        scorer=original.scorer,
        sandbox="docker",
        message_limit=MAX_MESSAGES
    )


def count_actual_tools(messages):
    """Count tool CALLS separately from observed tool RESULTS."""
    calls=0
    returns=0
    for message in messages:
        if getattr(message,"role",None)=="assistant":
            calls+=len(getattr(message,"tool_calls",None) or [])
        if getattr(message,"role",None)=="tool":
            returns+=1
    if returns>calls:
        raise ValueError("Unpaired tool results in original transcript")
    return calls,returns


def audit(directory):
    base=original_plan()
    if (importlib.metadata.version("inspect-ai")!=base["inspect_ai_version"]
        or importlib.metadata.version("inspect-evals")!=base["inspect_evals_version"]):
        raise RuntimeError("Original upstream Inspect distributions not pinned")
    root=Path(directory)
    if (root.is_absolute() or ".." in root.parts
        or root.name!="inspect-react-coding-logs" or not root.is_dir()):
        raise ValueError("Missing original bounded agent transcript directory")
    found=list_eval_logs(log_dir=str(root))
    if len(found)!=1:
        raise ValueError("Expected exactly one official ReAct coding task")
    log=read_eval_log(found[0].name)
    if (log.status!="success" or log.error
        or not str(log.eval.task).endswith(TASK_NAME)
        or log.eval.model!="hf/local"):
        raise ValueError("Original ReAct agent/task/model did not complete")
    cfg=log.eval.model_args or {}
    if (not str(cfg.get("model_path","")).endswith(REVISION)
        or cfg.get("device")!="cpu"
        or str(cfg.get("enable_thinking")).lower()!="false"):
        raise ValueError("Agent model provenance changed")
    samples=log.samples or []
    if len(samples)!=1 or str(samples[0].id)!="HumanEval/0":
        raise ValueError("Wrong or repeated original coding question")
    sample=samples[0]
    values=list((sample.scores or {}).values())
    if len(values)!=1 or values[0].value not in (CORRECT,INCORRECT):
        raise ValueError("Original HumanEval independent scorer missing")
    if not (getattr(sample,"metadata",{}) or {}).get("test"):
        raise ValueError("Original hidden unit test was unavailable")
    messages=sample.messages or []
    calls,returned=count_actual_tools(messages)
    return {
        **plan(),
        "inference_executed":True,
        "agent_loop_verified":True,
        "official_functional_test_scored":True,
        "attempted":1,
        "correct":int(values[0].value==CORRECT),
        "actual_model_tool_calls":calls,
        "actual_tool_results":returned,
        "model_tool_execution_verified":returned>0,
        "independent_original_test_id":str(sample.id),
        "original_test_sha256":sha256(str(sample.metadata["test"]).encode()).hexdigest(),
        "local_generation_calls":"multiple_bounded_not_independently_counted",
        "paid_api_calls":0,
        "automated_deployment":False,
        "AGI_demonstrated":False
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--audit-dir")
    parser.add_argument("--out",default="reports/inspect-react-coding-plan.json")
    args=parser.parse_args()
    destination=permitted_report(args.out)
    result=audit(args.audit_dir) if args.audit_dir else plan()
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2)+"\n")
    print("Real Inspect ReAct coding:",result.get("correct","not run"),
          "tool calls:",result["actual_model_tool_calls"],
          "AGI:",result["AGI_demonstrated"])


if __name__=="__main__":
    main()
