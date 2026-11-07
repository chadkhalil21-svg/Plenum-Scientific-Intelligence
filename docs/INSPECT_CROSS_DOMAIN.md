# Inspect cross-domain v1: third-party 96-question baseline

## Precommitted execution

The project already owns a verified UK AISI Inspect AI 0.3.287 and official
Inspect Evals 0.27.0 integration. Reuse **their original tasks, prompts,
dataset revisions and independent scorers**. Do not create a new evaluation
engine or grade model responses with a second LLM.

Use one immutable Qwen3-0.6B checkpoint: 
Qwen/Qwen3-0.6B at c1899de289a04d12100db370d81485cdf75e47ca.
Single local CPU connection. Disable thinking mode as verified in earlier
ARC repair, turn off sampling and model training. Zero paid API calls.

The fixed set below is **published historical data** rather than an unseen
blinded prospective holdout.

| Task | Independent target | N |
|-----|----|---:|
| inspect_evals/arc_challenge | More difficult school science reasoning | 24 |
| inspect_evals/gsm8k | Arithmetic word problems, zero few-shot prompts | 24 |
| inspect_evals/hellaswag | Commonsense event completion | 24 |
| inspect_evals/mmlu_0_shot | Multidisciplinary factual/mathematical knowledge | 24 |
| **Total** | Four distinct public task families | **96** |

Use 128 maximum new tokens per sample, one inference call at a time.
The actual CPU run requires a specially named release commit or deliberate
workflow dispatch. Normal pull-request checks only perform offline tests and
print the fixed plan. The workflow aborts on incomplete or inconsistent logs.

Each family must have exactly 24 independently scored samples, preserved
stable example IDs, original success/failure grades, raw Inspect .eval
logs, pinned upstream sources, and measured execution status.
The archival workflow commits the summary and raw original .eval files
to the public research-memory branch append-only. It never rewrites
historical errors. No external model API, untrusted code execution, private
Plenum patents, automatic model promotion, or production deployment.

## What it can and cannot prove

This baseline can show four-domain *measured responses* and where the small
model fails. It cannot establish an AGI percentage, new scientific discovery,
unseen generalization, self-improvement, or performance of larger models.
All four benchmarks are published and potentially present in pretraining.
The GSM8K answer template uses numerical matching; incorrect or
unparseable answers are scored as failures under the official grader.
24 questions per family are insufficient for a precise capability ranking.

Next: compare preregistered stronger frozen models, novel data and
independently tested code creation under strict compute and safety limits.
Do not conflate improving format or engineering harness reliability with
increased base-model intelligence.

Earlier original ARC baseline: run 42340268831 failed 24/24 in formatting.
Repaired ARC baseline: run 42340974100 scored 9/12 easy and 8/12
challenge. Both remain archived without rewriting.
