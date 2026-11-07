# Reasoning methods and model-size experiment (v1)

**Goal:** improve Plenum's measurable reasoning ability using verified, reusable systems rather than building new AI engines.

## What changes

Two frozen public model variants answer the SAME six questions generated from the existing AGI Capability Laboratory under two conditions:

- `baseline`: the original prompt unchanged.
- `verify`: the identical question with an instruction to check arithmetic, dimensions and program generalization internally, returning only the final requested JSON answer.

The models are Qwen3-1.7B (BF16, original checkpoint) and Qwen3-4B-Instruct-2507 (Unsloth Q4_K_M compressed GGUF derived from a reviewed Apache-2.0 Qwen checkpoint), each pinned to a specific public revision. The 4-bit model was chosen because standard GitHub CPU runners cannot reliably hold the complete 4B BF16 checkpoint in memory. **Precision, model generation and architecture differ**, so improvements cannot be attributed to parameter size alone.

An independent non-model auditor regenerates the same six numerical problems from the GitHub run seed. It reports:
- Strict original JSON format validity.
- Format-only recovered validity where the *entire* response is a single fenced JSON object.
- Strict and recovered actual task correctness, measured separately.
- Arithmetic program success on the existing 28 unrevealed input values.
- Per-family accuracy and inference seconds under each method.

No loose numerical extraction, self-claimed discovery, automatic model promotion, code execution or private data. The raw answers, including failures, are independently archived in `research-memory` and indexed through our existing public evidence reconciler.

## How to run

GitHub Actions > **Reasoning Improvement | Fresh Paired CPU Comparison** > Run workflow. The first reviewed main-branch merge runs one experiment. Subsequent evaluations require manually running the workflow, which generates a new seed each time.

The initial test has 24 total model calls (6 questions × 2 methods × 2 models), using temporary GitHub CPU workers and no hosted paid inference API. The samples are too small for a general ability or AGI conclusion; the public textbook task templates may have been encountered before in pretraining.

## Efficiency and next evidence

Do not interpret a better format score as improved reasoning. A model must improve **independently scored correctness on genuinely new inputs at justified incremental computation** to deserve further use. Before scaling up, compare with standardized ARC/HellaSwag tests via the already existing EleutherAI LM Evaluation Harness adapter. That is manual-only and does not need to be copied or replaced.

The canonical strategy remains `research-memory/state/AGI_PROGRAM.json`. No confidential corporate memorandum is copied into this public repository.
