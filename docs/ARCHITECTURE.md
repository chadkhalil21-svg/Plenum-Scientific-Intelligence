# Architecture

Founder objective -> task planner -> literature and data -> proposer -> independent critic -> tool/simulator -> verification -> ledger -> human-approved release.

## Phase 1 (present)
Standard Python, bounded OpenAlex search, optional local Ollama language model, deterministic calculation, toy ranker benchmark, read-only CI and public research artifacts.

## Phase 2
Persistent state, model/router interface, reproducible scientific tool registry, research citations, benchmark suites, branch-only code proposals and independent human-approved integration.

## Phase 3
Validated solver adapters (Lean 4, NASA GMAT, OpenMDAO, SU2, OpenMM, PySCF, PyBaMM); scientific retrieval index and experiment storage. Larger agent groups after measuring quality and resources.

## Phase 4
Local and distributed model training/finetuning, hardware-performance research, robotics, generalization testing, bounded self-improvement proposals.

## Costs
GitHub Actions standard runners are free for public repositories but not an unlimited GPU datacenter. Hosted inference, GPU training, storage and experiments may cost money. Free local models require physical hardware and electricity.

## Hardware research
Hot memory: electronic SRAM/HBM; warm: SSD; cold archival: experimental DNA/protein storage. None of the proposed molecular archives can currently replace GPU working memory.

## v0.2 implementation
A bounded mission produces a source inventory (OpenAlex or clearly marked offline fixture), optional separately prompted proposer and critic, a known-physics heat/orbit numerical check, and a JSON audit record. A passing simulation benchmark only demonstrates expected operation of that small model: it does not validate the model-generated scientific claims.

An optional CPU model run executes HuggingFaceTB/SmolLM2-135M-Instruct (Apache-2.0) on a temporary GitHub Actions runner. The model weights are not committed to GitHub. Larger models can be run through local Ollama on an owner-controlled always-on computer. Automatic public deployment and self-modifying main-branch writes remain disabled.

## v0.3 research memory
Public run artifacts are transferred to the research-memory branch via a separately permissioned GitHub Actions job after checksum validation. Prior stored paper metadata can be recalled as clearly labeled historical context. New hypotheses, unsupported references, secrets, and proprietary patent material are excluded from persisted records. Ranker-improvement proposals receive a second independent deterministic benchmark computation and cannot deploy themselves.

## v0.4 Scientific research toolchains

- Specialist router: allowlisted task dispatch across five disciplines, with explicit bounds on domain selection and input size.
- Literature workflow: existing OpenAlex metadata retrieval and persistent public evidence branch.
- Reasoning workflow: optional open-weight Qwen3 or local Ollama model, with proposer and critic roles. Role separation does not establish independent models or scientific accuracy.
- Scientific lab: SciPy solve_ivp for orbital, reaction, thermal and electrical ODE fixtures; RDKit for parsing an established public molecule and computing descriptors.
- Deterministic verifier: comparison against analytical known solutions, physical conservation where specified, and fixed structure reference values. Passing the checks establishes narrow numerical performance only.
- Adversarial evidence supervisor: refuses to label a numerical fixture a discovery and refuses silent self-modification.
- Benchmark: compare RK45, DOP853 and Radau across four domains. Recommend the method with fewest solver function evaluations only **for these fixtures**; record without deploying or changing model weights.

Remaining: real external datasets, task-specific scientific model adapters, multi-agent model scaling, robust domain coverage, safe execution sandboxes, expert verification and independently established generalization. GitHub Actions is a transient CPU runner and does not represent permanent autonomous AGI hosting.

## v0.5 Verified model-training pipeline
Allowlisted data sources → disjoint train/development/holdout partitions → two actual model families trained per task → candidate choice based solely on validation → independent replay and isolated holdout audit → JSON evidence artifact → human review. Test data and results are never supplied to the model-choice procedure. Demonstrates training of task-specific small models, **not** ongoing autonomous improvement of the underlying language model.

A future foundation-model optimization service will require model-weight license checks, suitable GPU compute, reproducible training dataset provenance, safety and privacy controls, unseen interdisciplinary evaluations, checkpoint signatures, rollback and human approval. No automatic fine-tuning, deployment or production promotion is enabled.
