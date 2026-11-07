# Next genuine autonomy gate: original Inspect ReAct on executable coding

## Do not rebuild

Use original Inspect AI 0.3.287 react() agent, python(timeout=20)
tool, original Inspect Evals 0.27.0 HumanEval public dataset and
unchanged functional verify() scorer. Reuse the existing Docker isolation,
source fingerprints, frozen Qwen3-1.7B public revision and CI evidence ledger.
No custom planning engine, code validator or grader is necessary.

## Exact bounded experiment

The real model is given the FIRST original public HumanEval specification.
The built-in ReAct agent may choose to call its Python tool, see feedback
and submit a final candidate code implementation. The original HumanEval
independent functional scorer grades the answer. Maximum six model turns,
fourteen transcript messages, one sample, one concurrent sandbox, at most
256 tokens per model turn, twenty seconds per Python tool call and strictly
bounded wall-clock budget. The sandbox is Docker, whose Inspect-generated
default configuration disables container networking.

This is distinct from:
1. A static file-editor import smoke, which uses no model or autonomy.
2. A single model-generated function, which is code synthesis, not agentic.
3. A genuine ReAct tool trace, which may or may not use tools or fix errors.
The auditor separately records official program test pass/fail, actual
tool calls and tool responses. A ReAct run with zero observed tool responses
is not evidence of actual model tool use.

The regular PR performs upstream API integration testing only, without
inference. Real bounded model execution requires an explicit release and
the prior original three-case HumanEval benchmark to have archived true
independent scorer logs. No new model choice or automatic promotion.

Safety: no secrets, private Plenum material, external paid model provider,
production repo writes or deployment. Untrusted model-generated Python
is allowed ONLY inside disposable Docker on an ephemeral CI runner.
All original raw evals, negative results, and failed runs are preserved.

LIMITATIONS: One historical public question could be memorized; even
perfect completion cannot demonstrate autonomous software engineering
across real repositories, safe long-horizon planning, scientific discovery
or artificial general intelligence.

After the tool loop is actually verified, prefer upstream OpenHands or
mini-SWE-agent and original SWE-bench Verified/Terminal-Bench on an
independently solved public software issue. For research, prefer PaperBench
with openly licensed material and a blinded prospective holdout.
