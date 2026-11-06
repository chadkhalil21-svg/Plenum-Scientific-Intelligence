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
