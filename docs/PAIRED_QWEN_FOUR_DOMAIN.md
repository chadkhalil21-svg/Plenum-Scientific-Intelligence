# Paired Qwen3-1.7B vs Qwen3-0.6B: frozen cross-domain comparison

This is an evidence-controlled **reuse** of UK AISI Inspect AI and Inspect
Evals, NOT a new benchmark framework, an AGI metric, or model training.

Reference: exact GitHub release 42341668858 using Qwen/Qwen3-0.6B pinned
at c1899de289a04d12100db370d81485cdf75e47ca, four original
Inspect task families, 24 public questions per family. An independent
archive of all 96 true Inspect grades and four original raw log files,
with SHA-256 hashes, must exist on research-memory **before** model inference.

Candidate: previously reviewed public Qwen/Qwen3-1.7B, immutable revision
70d244cc86ccca08cf5af4e1e306ecf908b1ad5e, 12 examples from each
of the same four official dataset tasks, 48 total. Same Greedy CPU model,
nonthinking, answer conventions, max 128 tokens, and one active request.
All four families use official Inspect Evals independent scorers:
ARC Challenge, GSM8K zero-shot, HellaSwag and MMLU zero-shot.

Crucial **pairing control:** The auditor reads the raw baseline 0.6B
Inspect .eval files rather than the advertised summary alone. It requires
all 12 candidate example IDs to match the **first 12** baseline IDs in
their respective original task. It rejects changed baselines, checkpoints,
model settings, task family, sample count, scorer outputs or corrupted
raw-log fingerprints. Report baseline accuracy, candidate accuracy,
paired fixes/regressions, failure IDs and absolute difference. No model
promotions on 48 potentially pretraining-contaminated examples.

CI policy: ordinary PR/push tests only create the offline plan. The
full CPU inference job is activated ONLY after the original baseline is
archived and a specially named main release merge or an explicitly
requested workflow dispatch. If the baseline failed, the comparison is
blocked before downloading the candidate model. No secrets, proprietary
Plenum material, arbitrary generated executable code, paid APIs or GPU
resources. GitHub Actions CPU and model-download bandwidth are finite.

A genuine future AGI milestone requires independent unfamiliar-domain
benchmarks, reliable program synthesis and autonomous long-horizon
completion, memory-based repeat performance, reproducible real-world
science and safety. An improvement on published tests does not satisfy
that bar.
