# ARC science benchmark v2: Qwen non-thinking comparison

Original run 42340268831 used pinned Qwen3-0.6B with 48 generated
tokens and its default thinking chat template. Both original upstream
Inspect tasks ran and produced official scores of **0/12** on ARC Easy and
**0/12** on ARC Challenge. Numerous replies contained truncated <think>
text instead of the required ANSWER: LETTER. The original raw eval logs
are retained as immutable artifacts; do not reinterpret or delete them.

The Plenum-specific post-run audit incorrectly expected the unqualified
task identifiers arc_easy and arc_challenge, whereas the third-party
logs use inspect_evals/arc_easy and inspect_evals/arc_challenge. That
audit error was separate from the model's independently produced score.

This v2 release explicitly passes the upstream Hugging Face model argument
enable_thinking=false and keeps the same checkpoint, 12+12 official
historical public questions, fixed 48-token cutoff, and independent
Inspect scorer. Versioned v2 JSON evidence labels the protocol variant
rather than overwriting any v1 artifact. A strict canonical task ID
normalizer refuses unexpected tasks.

The result remains an exploratory model configuration comparison on
well-known public benchmarks. ARC questions may have appeared in
pretraining. It does not establish AGI, unseen transfer, causal
scientific discovery, or reliable long-horizon planning. No paid
model provider, GPU, private Plenum research or automatic promotion.
