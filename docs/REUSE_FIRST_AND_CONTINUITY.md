# Plenum: Reuse-First Engineering and Continuity

**Core objective:** improve verified research intelligence, not merely increase agent or tool count. There is no demonstrated AGI, autonomous invention or consciousness.

## The existing record

The separate public `research-memory` Git branch already contains dated experiment JSON, original model responses, and failures. Its old `docs/LEDGER.md` had not yet been reconciled with newer experiments, so it was NOT an adequate sole source of current status.

- `research-memory/state/mission_status.json`: public founder-aligned goals, present capability claims, evidence links and explicit outstanding milestones. Human-reviewed strategic decisions remain separate from model-generated suggestions.
- `research-memory/docs/LEDGER.md`: concise current public status followed by the preserved historical November 5 snapshot.
- `research-memory/evidence/`: original experiment records, including negative results.
- `research-memory/state/evidence_index.json`: an automatically regenerated list of the **actual** public evidence files, their SHA-256 content hashes and research tracks. It is not a truth evaluator or a substitute for independent experimental audits.

The lightweight `python -m plenum_ai.evidence_index --root ledger/evidence --out ledger/state/evidence_index.json` command verifies existing JSON structure, stores no paper content and never asserts discovery. The reconciliation workflow checks the public branch daily and after changes to its own code. If a file cannot be indexed, the job fails instead of claiming completeness. It never edits existing experimental outcomes.

**Confidentiality:** The original Plenum Prometheus technical memorandum is confidential and is **not imported, copied, summarized or committed** into this public repository or its public ledger. Only already-public strategic principles are represented.

## What to reuse, and what to build

| Function | Preferred established component | Plenum-specific work |
|---|---|---|
| Language-model benchmarking | **EleutherAI lm-evaluation-harness**, MIT licensed, version `0.4.13`, source commit `ddd67220430a2470529f25fd5c05a576ca1057a0` | Short allowlisted launcher, evidence retention and result interpretation |
| Scientific calculation | Existing SciPy, RDKit, scikit-learn, OpenMDAO, PyBaMM, Astropy adapters when needed | Domain validation, source checking, falsifiable tests |
| Agent orchestration | Existing pinned LangGraph package already listed in optional dependencies | Task policy, measured completion and checkpoint semantics |
| Reusable scientific skills | Existing pinned read-only K-Dense catalog | License/dependency/security review before enabling anything |
| Memory | Git files and reproducible indexed JSON, with optional existing checkpoint storage | Durable goals, episodic decisions, versioning, evidence provenance |
| Research citations | OpenAlex and original authoritative research sources | Claim-level citation matching, uncertainty and contradiction tracking |

Import reviewed packages, do not bulk-copy repositories or claim they can be safely executed unreviewed. Maintain package/license/version review and avoid adding another framework when the existing one performs the job.

## Optional upstream benchmark use

This repository has a **thin, default-dry-run** interface to EleutherAI's established evaluator, `src/plenum_ai/standard_benchmarks.py`. It does not recreate HellaSwag/ARC questions or scoring.

It allows only two reviewed public model revisions and the published `arc_easy` and `hellaswag` tasks, with a maximum of 16 examples per task. This is an inexpensive **diagnostic sample**, not a credible general intelligence score. The source is MIT-licensed; the optional dependency `lm-eval[hf]==0.4.13` is NOT installed during ordinary tasks.

For actual optional model inference, the owner must dispatch **Upstream Standard Benchmarks | Manual, Reviewed** from GitHub Actions on `main`. The workflow installs upstream code, checks its version, downloads only the selected public model and benchmark, and invokes the upstream CLI. No paid hosted inference, arbitrary model-supplied code or automatic promotion occurs. Runtime and model performance remain unverified until the first actual upstream run is completed.

## AGI research priorities and image interpretation

Larger models can acquire capabilities not observed in smaller models, but score thresholds can create the appearance of sudden emergence. Do not infer that a particular parameter count guarantees AGI.

Step-by-step reasoning prompts can improve performance on some problems, especially with appropriate model capacity, but a prompt is not a substitute for independent evaluation, secure tools and valid planning.

For the next research milestone:
1. Retain authentic open-model evaluation and correctness evidence, including failed answers.
2. Compare stronger reasoning models on new multi-step tasks with independently checked results and measured compute cost.
3. Add bounded multi-stage task execution with durable state, interruption recovery and falsification.
4. Require repeatable wins on *new, independent* tasks before changing models or permitting greater autonomy.

**Engineering principle:** reuse proven software infrastructure; invest original effort in the missing reasoning, continuity, verification and domain-specific research questions.
