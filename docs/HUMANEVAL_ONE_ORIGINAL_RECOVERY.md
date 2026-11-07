# Original HumanEval/1 ReAct result: independently incorrect, runner subsequently aborted

The original bounded real-model test was released through GitHub Actions
run 42350525122 from source commit
79fb08d03c62d99c6a89c04efbb8b8e722370b2c.

The original Inspect .eval file WAS written before the runner aborted with
exit code 134, after the evaluation had reached its independent scorer.
Its saved header explicitly says status success, eval error null. The one
HumanEval/1 sample has original official Inspect Evals verify score I,
meaning incorrect (0/1). It also contains one genuine model-requested
Python tool invocation and one sandbox response. No multi-step repair
succeeded on this problem. The fully patched original Qwen3 tokenizer
is recorded as a SINGLE string, confirming the earlier template
compatibility repair worked.

The GitHub job failed when the local process emitted
terminate called without an active exception, followed by Aborted
(core dumped), and shell exit code 134. This happened AFTER the scored
Inspect file was written. It is incorrect to report GitHub workflow
success or a 1/1 model score. It is equally incorrect to treat it as a
missing independent grade or rerun the model for a preferred result.

The exact genuine original .eval log fingerprint SHA256 is:
ecdb3f9e177534e5f04c8a17be9aae42a183d3a1c5547476b1ab45e8c8cb23dc

The recovery simply downloads that original GitHub artifact, checks the
sha, uses the preinstalled original pinned Inspect reader, requires
the actual HumanEval/1 grade I, one model tool call and one real sandbox
response, and appends the original raw log plus independent report
to research-memory. NO model load, new inference, paid APIs, or generated
code execution is performed by the recovery.

Earlier reference conditions are genuinely preserved:
- Frozen Qwen3-1.7B single-shot HumanEval/1: incorrect, within 2/3
  baseline across first three published tasks (run 42346922772).
- Frozen Qwen3-1.7B Inspect ReAct HumanEval/0: correct, with 4 real
  tool calls and 4 tool results, after error feedback (run 42349665865).
- Frozen Qwen3-1.7B Inspect ReAct HumanEval/1: incorrect, 1 real
  tool call and 1 result, with runner abort AFTER scoring.

A 1/2 original-public-task ReAct result is not statistically meaningful
and does not establish autonomous software engineering, reliable tool-use
repair, independent generalization, scientific discovery or AGI.
Avoid cheap benchmark retries. Next use carefully selected upstream
software-repair and scientific reproducibility benchmarks with appropriate
isolated execution and explicit budgets.
