# Plenum Scientific Intelligence

Open foundation for autonomous scientific research, independent critique, simulation tools, and experimentally evaluated AI improvement. **AGI and artificial consciousness are research ambitions, not implemented capabilities.**

## Version 0.1

- Free OpenAlex literature-search adapter with source identifiers.
- Optional local Ollama model for hypothesis generation and separate critical review.
- Small deterministic orbital-mechanics solver.
- Reproducible narrow algorithm-improvement benchmark, with held-out testing and no automatic code deployment.
- Bounded daily or manually dispatched GitHub Actions research reports.

## Run locally

Python 3.11+ required.

    python -m pip install -e .
    python -m unittest discover -s tests -v
    plenum research --query "photonic computing" --out reports/research.json
    plenum improve --out reports/improvement.json
    plenum physics --radius-m 6771000

Optional: install and run an Ollama model on your own computer, then:

    plenum research --query "materials science" --model YOUR_LOCAL_MODEL

This has no required paid API or subscription. Local model inference still needs capable computing hardware.

## Run from an iPad/iPhone

On GitHub, open **Actions > Autonomous Research > Run workflow**, enter a public research question, and inspect the resulting artifact. This workflow does not run a large AI model, train an AGI, or perform advanced simulation.

## Project documents

- docs/CONSTITUTION.md: authority and research principles
- docs/LEDGER.md: completed, proposed, and unverified milestones
- docs/ARCHITECTURE.md: modular architecture and costs
- docs/INTEGRATIONS.md: external open-source projects to connect
- docs/SECURITY.md: privacy and sandboxing

**PUBLIC REPOSITORY NOTICE:** Do not add patents, unpublished inventions, credentials, proprietary data, or private records. No model self-deployment or external side effects are enabled.

## Autonomous mission v0.2
The `plenum mission` command now runs a bounded sequence: planner, literature retrieval, optional model-driven hypothesis proposer and critic, numerical simulator, and independent deterministic physics check.

```sh
plenum mission --query "How can we improve photonic computing?" --simulation heat --out reports/mission.json
plenum mission --query "Test an orbital model" --offline --simulation orbit --out reports/orbit.json
```

### Actual open-weight model (optional)
**Open-Weight AI Model Demonstration** is a GitHub Actions CPU workflow using the downloadable, Apache-2.0 **Qwen3-0.6B** model from Hugging Face. It requires neither a commercial AI subscription nor your iPad's processor; each run downloads model and Python dependencies to a temporary runner. It is a tiny proof-of-inference, **not an AGI** and not yet a high-quality scientist. Open the Actions tab to view its run and artifact. It runs automatically on first addition of its workflow and manually thereafter.

You can alternatively run a capable open-weight model through Ollama on your own computer, e.g. `plenum mission --query "..." --model YOUR_OLLAMA_MODEL`. Local Ollama does not run on GitHub's short-lived CPU runners unless separately installed.

The initial 135M model benchmark completed, but its text echoed instructions. The improved model workflow now uses Qwen3-0.6B, disables thinking mode to avoid spending CPU on hidden reasoning tokens, and checks for obvious prompt repetition. This is a basic text-quality filter, not scientific verification.


## Evidence persistence and improvement audit (v0.3)
Research-memory is a separate public branch for checksum-addressed scientific paper metadata, verification status, and synthetic ranker benchmark results. Run Actions > Autonomous Research to obtain a report and archive a vetted-format public record. The tool can consult matching past metadata on subsequent runs; it cannot treat prior model proposals as proven facts or automatically change source code. Read docs/MEMORY.md before entering queries, because public GitHub workflow inputs and archives are not confidential.

## Multidisciplinary scientific lab and agentic investigation (v0.4)

Validated known-equation fixtures now call real open-source libraries: SciPy for numerical differential equations and RDKit for chemical structure descriptors. The lab covers Earth-orbit mechanics, closed reaction kinetics, lumped material cooling, simple RC circuits, and ethanol molecular descriptors. Its verification compares calculations with analytical results or known formula/weight. These fixtures are **not** new scientific discoveries, validated medicine, a full drug simulator or a generalized physics engine.

To run the integrated tools locally:

    python -m pip install -e ".[science]"
    plenum lab --query "Test orbital, chemical and material models"
    plenum solver-benchmark
    plenum investigate --query "How should we test an orbital mechanics hypothesis?" --offline

For optional open-weight model-driven hypothesis proposer and independent critic:

    python -m pip install torch "transformers>=4.51,<5" safetensors
    plenum investigate --query "How might scientific numerical validation improve?" --hf-model

You can run **Verified Scientific Simulation Lab** using GitHub Actions from an iPad. The Qwen3 open-weight model test is separate and more expensive in CPU time, but uses no paid inference subscription. The source code never auto-deploys proposed changes.

Scientific tool references: https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html and https://rdkit.org/docs/. This repository depends on these packages; it does not copy their source trees.
