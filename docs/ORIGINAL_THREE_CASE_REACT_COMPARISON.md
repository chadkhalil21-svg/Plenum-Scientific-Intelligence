# Exact original three-case ReAct coding versus one-shot proof

Reuse ONLY the already proven components: original UK AISI Inspect AI
v0.3.287, original Inspect Evals HumanEval v0.27.0 independent
functional verifier, original Qwen3-1.7B frozen public weights, native
--model-config JSON tool chat-template correction, Inspect's upstream
react() agent plus Python tool in disposable networkless Docker.

## Why this is next

The original **single-shot** code-generation baseline completed
2/3 original HumanEval/0, /1, /2. Source run 42346922772, all original
unit-test logs and SHA256 archived. The **tool-using** ReAct agent passed
1/1 on HumanEval/0 and recorded four tool calls and four observed replies
in source run 42349665865. That proves use of one sandboxed programming
tool, NOT reliable autonomous software engineering or general intelligence.

We now compare the SAME three source questions, not unrelated tests:

- Model and tokenizer version unchanged; output max 256 tokens
  per generation, greedy, thinking disabled.
- ReAct may use at most 6 turns and 14 transcript messages per
  question with the same original built-in Python tool and 20-second
  per-tool limit, max one concurrent sandbox/task.
- Original HumanEval independent functional scorer, original source
  problem IDs, specification, target, and complete source tests must
  match precisely to the previously archived one-shot run.
- The auditor reads original .eval transcripts, not self-grading text,
  and counts actual tool calls AND actual tool response messages for
  every original problem. Repairs, regressions, passed tests and all
  failures are preserved, including complete raw logs and SHA256.
- No paid model API, no custom agent loop, no training, no confidential
  Plenum source or patent inputs, no production writes or deployments.
  GitHub CI uses bounded hosted CPU time and public model download
  bandwidth. Those resources are finite and may be billed according to
  the GitHub account's plan, so this is one gated study, not a loop.
- PR checks default to no inference. A specifically reviewed main
  release or manual dispatch launches real inference. Any failure
  stops the experiment, preserves its source artifact and prevents
  unearned functional claims.

Even a perfect 3/3 is an inadequate demonstration of AGI or ability
on new software repositories. The subsequent major step is a real
SWE-bench Verified or Terminal-Bench issue using upstream OpenHands
or mini-SWE-agent and independent hidden tests. Scientific autonomy
next uses PaperBench and PaperQA2 on rights-cleared sources with
prospective unseen tasks. Do not rebuild existing evaluation, orchestration,
isolated tool execution or literature retrieval software.

Original evidence:
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42346922772
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42349665865
