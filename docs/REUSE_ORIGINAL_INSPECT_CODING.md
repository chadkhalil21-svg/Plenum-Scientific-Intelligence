# Reuse original Inspect HumanEval for code synthesis, not another evaluator

Plenum already uses real UK AI Security Institute Inspect AI v0.3.287,
Inspect Evals 0.27.0, pinned public local models and independent scorers.
OpenHands SDK has already demonstrated constrained offline file editing.
The next missing empirical capability is whether a model can GENERATE
FUNCTIONAL CODE, and whether untrusted generated code stays inside a
disposable, networkless test environment.

We reuse the original Inspect Evals HumanEval task, original pinned
OpenAI HumanEval public dataset revision
7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544 and its own verify()
unit-test scorer. No custom grader, LLM judge or copy of upstream packages.
The frozen pretrained Qwen3-1.7B previously used in Plenum is unchanged.

The tightly bounded study uses exactly three original public coding
questions, one generation epoch, 256 output tokens, greedy temperature,
thinking disabled, local CPU, one concurrent task and one Docker sandbox.
The original upstream Docker sandbox disables networking by default.
Execution occurs on a disposable GitHub-hosted runner, not on Plenum
production. No model API credentials or private corporate material.
GitHub Actions runner time and model downloads do consume infrastructure
resources even though the external model API charge is zero.

The regular pull request only validates the no-inference plan and
negative integrity checks. A specifically named release or explicit
workflow dispatch runs the three real model-generated functions with
their original independent tests, then preserves all original .eval
logs, failed question IDs, source/response SHA256 and score totals
append-only in the independent research-memory branch. No generated
code is merged or deployed, and no model is automatically promoted.

LIMITATIONS: Published historical public tests may have appeared in
pretraining. Three samples are far too few for a meaningful ranking.
This is one-shot code synthesis, NOT independently repairing arbitrary
repositories, long-horizon agentic reasoning, scientific discovery,
generalization or AGI.

Next (without inventing more tools):
- Inspect's existing react agent, time/message limits and Docker tools
  for multi-turn file edits and test-driven repair.
- OpenHands/mini-SWE-agent on a reviewed public software issue and
  existing SWE-bench Verified/Terminal-Bench scorer.
- PaperQA2, original PaperBench and citation accuracy on rights-cleared
  scientific documents and later genuinely novel prospective tasks.
- A larger or better pretrained model only with verified budget,
  privacy, security and independent paired measurements.

Sources:
https://github.com/UKGovernmentBEIS/inspect_ai
https://github.com/UKGovernmentBEIS/inspect_evals
https://github.com/openai/human-eval
https://www.swebench.com/verified
https://openai.com/index/paperbench/
