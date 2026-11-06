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
**Open-Weight AI Model Demonstration** is a GitHub Actions CPU workflow using the downloadable, Apache-2.0 **SmolLM2-135M-Instruct** model from Hugging Face. It requires neither a commercial AI subscription nor your iPad's processor; each run downloads model and Python dependencies to a temporary runner. It is a tiny proof-of-inference, **not an AGI** and not yet a high-quality scientist. Open the Actions tab to view its run and artifact. It runs automatically on first addition of its workflow and manually thereafter.

You can alternatively run a capable open-weight model through Ollama on your own computer, e.g. `plenum mission --query "..." --model YOUR_OLLAMA_MODEL`. Local Ollama does not run on GitHub's short-lived CPU runners unless separately installed.
