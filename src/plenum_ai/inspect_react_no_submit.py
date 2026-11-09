"""Single NEW public HumanEval/3 coding task with official Inspect react(submit=False).

This task is independent of previous HumanEval/0-2 original evidence.
No custom reasoning loop, grader, sandbox, or private code. Original Inspect's
no-submit agent stops on a plain final answer rather than needing a separate
structured submit() function. The functional scorer is the original HumanEval
author test. Whether the model uses the Python tool is observed, not assumed.
"""
from inspect_ai import Task, task
from inspect_ai.agent import react
from inspect_ai.tool import python
from inspect_evals.humaneval.humaneval import humaneval

from .inspect_react_coding import MAX_MESSAGES, MAX_TOOL_SECONDS

SAMPLE_ID="HumanEval/3"
PROMPT=(
    "Implement the public Python function specification provided. "
    "You may run Python in the isolated tool to test your code. "
    "When finished, output ONLY the complete Python source implementation "
    "and any needed imports. No Markdown, XML, JSON, explanations or "
    "literal tool-call markers. Never access networks or private files."
)


@task
def original_new_case_no_submit():
    upstream=humaneval()
    subset=[sample for sample in upstream.dataset if str(sample.id)==SAMPLE_ID]
    if len(subset)!=1:
        raise ValueError("Require exactly one new original HumanEval/3 case")
    return Task(
        dataset=subset,
        solver=react(
            prompt=PROMPT,
            tools=[python(timeout=MAX_TOOL_SECONDS)],
            submit=False,  # Supported by original Inspect, not custom code.
        ),
        scorer=upstream.scorer,  # Original unchanged HumanEval functional test.
        sandbox="docker",
        message_limit=MAX_MESSAGES,
    )
