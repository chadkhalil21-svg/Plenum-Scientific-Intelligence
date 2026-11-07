# Same Qwen3-1.7B math questions: 128 vs 256 output tokens

This study tests one confound found in an independently re-audited
model comparison, without generating another evaluation engine.

**Original results:** frozen public Qwen3-0.6B scored 18/48 and
Qwen3-1.7B scored 21/48 on precisely matched official Inspect Evals
questions. Both original .eval log sets are independently archived.
For the 12 identical GSM8K math problems:
- Qwen3-0.6B at 128 tokens scored 4/12; four outputs reached cap.
- Qwen3-1.7B at 128 tokens scored 1/12; **ten outputs reached cap**.
- Zero of those ten Qwen3-1.7B capped responses were scored correct.

Those observations suggest that verbosity and output truncation
contaminate any simple conclusion that 1.7B is mathematically weaker.
They do not prove extra output tokens will improve accuracy.

This separately versioned, post-hoc ablation reruns only the SAME
12 original public GSM8K questions with:
- The exact original Qwen/Qwen3-1.7B public revision
  70d244cc86ccca08cf5af4e1e306ecf908b1ad5e.
- Same Inspect AI 0.3.287, Inspect Evals 0.27.0, original numeric
  scorer, zero fewshots, CPU, greedy, and thinking disabled.
- Only one changed setting: maximum generated output tokens
  **128 becomes 256**.
- The exact previous 1.7B 12-case source from original run
  42342242561; original model data hashes archived in
  research-memory/evidence/paired-qwen.
- Every question ID, prompt, choice and reference answer must match.
- Preserve corrections, regressions, output-limit counts and original
  independent scores, even if the 256-token result is worse.

Only one bounded main-release CPU inference job; no paid inference API,
GPU, training, auto model selection, shell execution of generated code,
private Plenum material, or autonomous changes. The default PR only
checks the frozen plan and negative validation controls.

**Limits:** 12 public questions, potential pretraining overlap, one
comparison deliberately chosen *after* examining errors. No general
model-superiority claim, reliable mathematical competence, scientific
discovery or AGI proof follows from it.
