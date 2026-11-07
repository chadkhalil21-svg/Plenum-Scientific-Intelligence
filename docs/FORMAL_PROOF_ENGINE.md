# Plenum: real mathematical proof engine, first bounded release

The accompanying image set identifies Lean 4 as a specialist formal-methods engine. We have adopted the existing **Lean 4** kernel rather than building a new theorem prover.

- Upstream: https://github.com/leanprover/lean4 (Apache-2.0)
- Installed by `leanprover/lean-action@v1` in a separate isolated GitHub Actions job.
- Exact engine toolchain: `leanprover/lean4:v4.35.0`.
- Source: `formal/PlenumFormal/ResearchAccounting.lean`.
- Negative control: `formal/negative/FalseClaim.lean` intentionally asserts `n + 1 = n`, and the real Lean compiler MUST reject it.
- The positive statements check an elementary, general fact about research accounting: accepted results never exceed accepted + rejected results, and the total is order-independent. They are genuine kernel-checked mathematical statements for all natural-number inputs, **not** numerical simulation or invented language-model reasoning.
- The proof engine does **not** discover the theorems itself; they were manually selected and written. No AGI, scientific novelty, consciousness, physical experiment, end-to-end autonomous research or model learning is demonstrated.

## Reuse-first steps to expand

1. Use Lean 4/mathlib on externally selected public mathematical verification tasks, with pinned upstream revisions and cached artifacts rather than a new proof engine.
2. For an approved open-weight model, let it propose a proof as **inert text in a disposable worker**, never as a trusted shell command. Feed exact proposal to a constrained Lean compiler job and preserve positive and negative original logs.
3. Compare correct proof rates with baseline model and human-written control on frozen unfamiliar problem sets. Do not accept `sorry`/`admit` or unchecked axioms.
4. Connect proof-checking output to Plenum's LangGraph scientific orchestration and canonical evidence ledger with source provenance and rollback.
5. Distinguish formal theorem validity (in a stated axiomatic system) from a claim that a physical model represents the real world. Empirical testing remains necessary.

This component is one narrow scientific tool in the broader full-AGI roadmap. It is not an alternative objective to AGI.
