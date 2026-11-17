# Optional EvoScientist score aggregation (v0.4.3)

**Status:** original upstream code incorporated as an optional, isolated
offline evaluator for historical public native GPQA receipts. Not the full
EvoScientist harness. No model runtime, API key, download, paid service,
autonomous skill-writing or background scheduling is enabled.

- Upstream repository: https://github.com/EvoScientist/EvoScientist
- Immutable release: v0.4.3, commit `b1ca788ae9c6e78f5b66df56cc770c3d0bbf55e1`.
- Original path: `EvoScientist/skills/skill-creator/scripts/aggregate_benchmark.py`
- Unmodified upstream blob: `70c548e81b67bb85858056087e642d80b408f2a5`
- SHA-256: `540d0ee42b894428350eaf1337e436376e2429185b5ce69485434216f2d0b386`
- Apache-2.0 license retained in `LICENSE.txt`; the upstream license identifies
  its derivation from the Anthropic skill-creator skill.

With Python 3.11+, from the Plenum repository root:

```sh
python integrations/upstream/evoscientist-v0.4.3/aggregate_gpqa.py
```

This validates the original script and two fixed public receipt hashes and
prints a read-only plan. Explicitly add `--execute` to convert the six native
grades to an upstream-compatible folder layout, invoke the isolated
standard-library-only evaluator in a temporary folder, and write the raw,
unmodified upstream reports to `reports/evoscientist-gpqa`. Existing output is
never overwritten. No external endpoints, credentials, model weights, or
custom inputs are used.

The actual first execution is preserved in
`evidence/evoscientist/2026-11-17-gpqa/`. It aggregated the existing native
three-question GPQA grades, candidate Qwen3.5-4B 0/3 vs reference Qwen3-0.6B
1/3. It did not rerun either model or rescore any answer. Do not infer general
model ranking or AGI from three historical public items.

**Critical interpretation:** Raw upstream reports use zero when timing,
tokens, tool calls, or errors are missing. Those fields are not comparable
paired measurements and must never be read as measured zeros. Only pass-rate
aggregation is supported here.

Existing Plenum Inspect and LM Evaluation Harness adapters remain authoritative
for original grading. This standalone third-party summary adds reproducible
statistics and explicit comparison while preserving the original graders.
