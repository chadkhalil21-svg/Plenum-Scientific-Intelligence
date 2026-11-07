# First actual upstream-model benchmark: ARC Easy and ARC Challenge

## November 7 protocol correction

The original first prospective CI run 42340268831 executed 12 ARC Easy
and 12 ARC Challenge tasks on pinned Qwen3-0.6B. Inspect's original
multiple-choice scorer marked **all 24 invalid response format** because
the 48-token budget was consumed by the model's initial thinking text.
The separate Plenum post-processing auditor also rejected correctly
qualified task names: inspect_evals/arc_easy and
inspect_evals/arc_challenge. The original failed run is preserved
in the canonical AGI ledger and GitHub .eval log artifacts.

Protocol v2 is **a separate follow-up designed after examining this
failure**, not an unseen replication. It passes enable_thinking=false
through the officially supported Inspect Hugging Face model argument,
normalizes allowlisted qualified task names, and audits only the
pinned checkpoint's official scorer results. Original tasks, question
counts and response-length limits remain unchanged. The new run
cannot be compared as proof of learning or general intelligence.

**Goal:** stop treating SDK installation as evidence of intelligence. Use the
established UK AISI Inspect Evals 0.27.0 benchmark implementations and
Inspect AI 0.3.287 scoring to evaluate real frozen Qwen3-0.6B CPU responses.

The model checkpoint is already allowlisted and pinned in
src/plenum_ai/hf_model.py. Two official public historical science tasks
run with 12 questions each, at most 48 generated tokens per sample, one
active model connection, CPU-only, and zero paid APIs. The model must not
see gold answers. Official Inspect task scorers grade the responses.

This experiment runs automatically once on a specially named main
release commit, or by deliberate manual workflow dispatch. Normal PR/CI
runs do cheap no-inference tests and emit the execution plan.
There is no automatic model promotion, unrestricted shell execution of
LLM output, proprietary data, model training or production deployment.
Original Inspect logs and independently scored summaries are archived.
Successful runs append evidence to research-memory, preserving failures.

**Limitations:** ARC is a well-known public school-science benchmark.
The models may have encountered the questions during pretraining. A 12-item
sample per task is an engineering measurement, not statistically precise
model superiority, unseen AGI generalization, novel research, or scientific
discovery. If either task fails, preserve logs and do not claim the audit
passed. Compare stronger frozen models, program-coding tasks and genuine
prospective research only after the baseline runs successfully.

Sources:
- https://github.com/UKGovernmentBEIS/inspect_ai
- https://github.com/UKGovernmentBEIS/inspect_evals
- https://ukgovernmentbeis.github.io/inspect_evals/evals/arc/index.html

Next proof-of-value experiments:
1. OpenHands in a disposable coding sandbox on a reviewed public task
   with explicit bounded inference, no secrets, manual review and tests.
2. PaperQA2 on rights-cleared public scientific documents with approved
   embeddings and an independently checked citation rubric.
3. Expand standard evals toward mathematically diverse, hidden,
   multi-step problems and prospectively sealed experiments.
