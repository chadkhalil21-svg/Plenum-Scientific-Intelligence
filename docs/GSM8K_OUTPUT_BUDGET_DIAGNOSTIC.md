# GSM8K 128-versus-256 token budget diagnostic

In a successfully completed official Inspect Evals benchmark on immutable
Qwen3-0.6B (run 42341668858), only 6/24 GSM8K math answers were correct.
Independent inspection of all original .eval responses found that **10 of 24
hit the 128-token output cap and zero of these 10 were graded correct**.

That is diagnostic evidence, not proof that extra tokens will fix reasoning.
To test the hypothesis rather than merely speculate, this follow-up compares
the **same 24 official GSM8K questions**, fixed benchmark data/revisions,
same Qwen3-0.6B model, no fewshot, greedy decoding, thinking disabled,
no tools, CPU and Inspect Evals original numeric-match scorer.

**Only changed variable:** generation maximum rises from 128 to 256 tokens.
The reference comes from the previously audited and archived original .eval
files and SHA256 fingerprints. A new explicit run obtains 256-token outputs.
The auditor refuses altered source checkpoints, unmatched question IDs,
missing original binary scores, skipped questions, inconsistent token counts,
incompatible Inspect versions, or absence of the original benchmark archive.
Correct answers, regressions, counts in the original 128-token-cap subgroup,
and original raw logs are preserved even if the new configuration performs
worse. Zero paid model APIs or training; the experiment uses bounded local
GitHub CPU inference and downloads the one reviewed checkpoint only on an
explicitly titled release or direct manual dispatch.

This diagnostic is post hoc, prompted by an observed failure. It uses
historical public math questions, which may overlap model pretraining, and
does NOT demonstrate general intelligence, mathematical discovery or
recursive self-improvement. The base model is not automatically promoted.

Operational issue: Existing 96-question released summary originally reports
model_calls=0 inherited from its **preflight plan** despite real local
model inference. That is a reporting error: 96 sample-generation requests
were made in the original four-domain benchmark, even though **paid API
calls were zero**. Correct subsequent evidence accounting without rewriting
original immutable evaluation logs, and keep these categories separate.
