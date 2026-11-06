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

## v0.5: Actual model training and evaluation

Run **Scientific Model Training and Holdout Evaluation** in GitHub Actions. It trains small classification and physics-regression models with scikit-learn. Model families are selected from validation data, independently replayed, and evaluated on reserved held-out examples. No paid model API or GPU is required. The trained models are **not** Qwen3 weights, AGI, new inventions or scientific discoveries.

```sh
python -m pip install -e ".[ml]"
plenum train-models --out reports/model_training.json
```

Full measurements, limits and next steps: [docs/MODEL_TRAINING.md](docs/MODEL_TRAINING.md).

## v0.6 External science reasoning and Qwen3 fine-tuning

The Qwen3-0.6B model scored **2/12 (16.7%)** on the initial externally sourced ARC-Challenge science sample. This is a small public benchmark, not a robust AGI test.

Our CPU experiment then trained a real, tiny LoRA adapter with **286,720 trainable parameters** across **two gradient steps**, using original public instructional examples. Its reserved 8-question score was **2/8 before and 2/8 after**. This is **no demonstrated improvement**.

The SHA-256-verified adapter is available as a **14-day GitHub Actions artifact** from run 42157269113. It is an experimental candidate, not deployed or accepted into the base AI. Full methodology: [docs/SCIENTIFIC_REASONING.md](docs/SCIENTIFIC_REASONING.md).

## v0.7: Multi-tool research network, pinned scientific integrations

The scientific tool registry enables **several specialist tools concurrently**, followed by an explicit dependency-aware engineering optimization and independent numerical checks. [LangGraph](https://github.com/langchain-ai/langgraph) provides dynamic parallel fan-out and fan-in. [OpenMDAO](https://github.com/OpenMDAO/OpenMDAO), a NASA-origin multidisciplinary design framework, performs a constrained cooling-area optimization based on a prior verified SciPy thermal result.

```sh
python -m pip install -e ".[science,orchestration]"
plenum tool-registry
plenum parallel-research --query "Evaluate orbital, thermal, kinetic and molecular models"
plenum scientific-skills
plenum federated-literature --query "photonic memory" --online
```

From your iPad, open GitHub **Actions** to run **Parallel Scientific Tools and NASA OpenMDAO** or **Federated Scientific Literature**. These actions do not need a paid AI API. Independent tools execute concurrently, but use a bounded number of workers per batch.

Scientific retrieval uses **OpenAlex, Europe PMC and Semantic Scholar** concurrently, recording failures and separating paper metadata from experimentally verified facts. K-Dense scientific skills are accessible through a **pinned, read-only catalog for review**, not automatically installed/executed. NASA Aviary v1.0.1 passed its official installation check (run 42159140408); full aircraft mission verification remains future work.

No agent can execute arbitrary shell commands, grant permissions, install unreviewed skills or replace the deployed AI. See [integrations](docs/INTEGRATIONS.md) and [engineering architecture](docs/ARCHITECTURE.md).

### v0.7 automatic selection and live scientific sources

A public question can be routed to **several** approved tools automatically using explicit, auditable keyword rules (not yet an AI reasoner):

```sh
plenum parallel-research --auto --query "Optimize cooling and electrical circuits for orbital motion"
```

Real federated verification (GitHub run 42159408960): OpenAlex, Europe PMC and Semantic Scholar each returned 3 public publication metadata records, 9 distinct records in total. This is not full-text review or verification of the studies.

NASA Aviary 1.0.1 executed its bundled public Advanced Single Aisle mission example under a bounded SLSQP optimizer configuration (GitHub run 42159565273). Command completion was verified, but optimization convergence and actual aircraft performance have **not** been independently established.

K-Dense's pinned RDKit scientific skill document was safely retrieved as a read-only untrusted reference without executing any instructions (GitHub run 42159591148).

## v0.8: NASA observations and battery electrochemistry

Two additional public scientific integrations have now passed live GitHub tests:

- **NASA Exoplanet Archive + Astropy:** retrieved 80 public catalog records and calculated Keplerian orbital periods with astronomical units and physical constants. 73/80 records (91.25%) had predicted periods within 10% of catalog values, with a median absolute relative difference of 0.159%. **Not independent experimental proof:** some catalog semimajor axes may be derived from the periods themselves. [Methodology](docs/EXTERNAL_EVIDENCE.md).
- **PyBaMM:** ran actual default SPM and SPMe lithium-ion electrochemical discharge models for ten minutes. Both simulations completed with bounded voltage decreases. **Not a test of Plenum's solid-state battery or actual measured cell performance.** [Model evidence](docs/BATTERY_MODELS.md).

```sh
python -m pip install -e ".[astronomy]"
plenum nasa-exoplanets --out reports/nasa_exoplanet_consistency.json

python -m pip install -e ".[battery]"
plenum battery-simulation --minutes 10 --out reports/battery_simulation.json
```

Use the corresponding NASA and PyBaMM workflows in GitHub Actions to reproduce on free public CPU runners. PyBaMM remains an isolated science workflow until its dependency environment is reviewed for shared parallel-agent execution. Neither integration is an autonomous invention or proof of AGI.

## v0.9: Prediction evaluated on real, held-out NOAA measurements 🌊

Plenum now has a reproducible observational test that differs fundamentally
from our known-equation fixtures. A fixed four-constituent tidal model was fit
on sixteen days of **real NOAA hourly water-level measurements**, then
evaluated against a withheld 24-hour day at two stations.

- **Boston:** model MAE 0.324 m, previous-day persistence MAE 0.340 m.
- **Virginia Key:** model MAE 0.066 m, baseline MAE 0.087 m.
- **Both beat the baseline** on this single precommitted historical test day.

[Measured-data methodology](docs/EMPIRICAL_FORECASTING.md) |
[Permanent machine-readable results](evidence/noaa/2025-06-17.json) |
[Passing GitHub run](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42161428637)

```sh
python -m pip install -e ".[empirical]"
plenum empirical-tides --out reports/noaa_measured_tides.json
```

The observations are genuinely separate from the model-fitting data. This
does not demonstrate a newly discovered law, general scientific reasoning,
an operational coastal forecast, autonomous invention or AGI. Larger
precommitted multi-season evaluations are required before wider claims.

### v0.9b follow-on evidence across seasons

Without changing the model after the first successful day, Plenum evaluated
the same equations against **six previously untested seasonal NOAA datasets**.
The harmonic model beat prior-day persistence in 4 of 6 cases; pooled MAE
was **0.17205 m versus 0.21878 m** (21.36% reduction). Two failures are
explicitly retained. This is evidence of limited forecast skill on selected
historical days, **not** operational tide forecasting or artificial general
intelligence.

[Seasonal methodology](docs/EMPIRICAL_FORECASTING.md) |
[Complete permanent metric summary](evidence/noaa/2025-seasonal-independent.json) |
[Successful seasonal validation run](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42161902806).

## v1.0–v1.1: AI-selected scientific hypotheses with independent testing

Plenum has now run two independent, real-data experiments in which Qwen3-0.6B
chooses from four reviewed forecast hypotheses before the test day is
downloaded. An independent auditor then tests the choice against observed
NOAA water-level measurements, and a final permission-scoped job archives
all outcomes on the `research-memory` branch.

**First run:** Qwen3 chose 24h persistence in all four cases. None improved.

**Evidence-gated follow-up:** a fixed, engineer-designed development-data
gate overrode two weak suggestions, lowering mean absolute error from
0.22366 to 0.18613 m across four new cases, but the existing four-harmonic
reference was still stronger at 0.17501 m. No model weights changed.

[Protocol and full measured results](docs/AUTONOMY.md) |
[Independent blind evaluation run](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42163393864) |
[Full scientific ledger](docs/LEDGER.md)

This is **bounded, auditable scientific decision-making**, not general
autonomous invention, recursive self-improvement or AGI. No paid AI
subscription or unreviewed tool execution was activated.

## Foundational architecture upgrade: persistent research and independent model evaluation

A new [Operating Architecture and iPad Guide](docs/OPERATIONS_V2.md)
describes the founder-facing **Plenum Research Control Center** under GitHub
Actions. Its approved operations can run multidisciplinary scientific
investigations, index scholarly metadata, retrieve explicitly licensed
open-access papers, recover local scientific graph checkpoints, and verify
tests. No unrestricted self-deployment or paid model API is activated.

New working modules:

- `durable_graph.py`: LangGraph SQLite checkpoints and recovery, including
  refusing accidental duplicate research-thread execution.
- `knowledge_index.py`: FTS5 scientific-source search with DOI, origin,
  license and SHA-256 evidence, rehydrated from content-addressed public
  `research-memory` records.
- `open_access.py`: read-only Europe PMC JATS retrieval with exact
  Creative Commons license checks and bounded local indexing.
- Independent [EleutherAI LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness)
  workflow comparing public Qwen3-0.6B and Qwen3-1.7B on ARC-Challenge and
  PIQA. Each model is separately evaluated; neither is installed as a
  production intelligence by default.

Example usage:

```sh
python -m pip install -e ".[science,orchestration]"
plenum durable-research --query "Verify orbit and thermal benchmark models" --thread-id study-1
plenum durable-state --db reports/research_checkpoints.sqlite --thread-id study-1

plenum import-public-memory --dir prior-knowledge/memory/entries --db reports/research_index.sqlite
plenum index-literature --query "photonic computing" --online --db reports/research_index.sqlite
plenum index-open-article --pmcid PMC12247565 --db reports/research_index.sqlite
plenum search-knowledge --query "neuroscience and computing" --db reports/research_index.sqlite
```

The checkpoint and FTS5 databases live on the owner's retained disk or
in explicitly downloaded GitHub artifacts, **not** automatically across
temporary runners. The approved public research-memory Git branch is the
cross-run record source. A long-running cloud AI and stronger model serving
still require owner-approved computing resources and permissions.

## Screenshot-driven global scientific ecosystem expansion

The founder's complete scientific-engine, global-library and AI-research
reference screenshots have been incorporated into the reviewed
[Scientific Ecosystem Inventory](docs/SCIENTIFIC_ECOSYSTEM.md).

New, **tested** integrations include two public scholarly indexes (arXiv
and US DOE OSTI) alongside the existing OpenAlex, Europe PMC and
Semantic Scholar adapters, plus isolated **OpenMM 8.6.1** CPU molecular
dynamics. Their live GitHub workflows completed successfully:
[Five-source library](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42167088294)
and [OpenMM reference](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42167232309).
Semantic Scholar was unavailable during the latest five-source live call,
and that absence is retained in the report.

From GitHub Actions, the founder-facing **Plenum Research Control Center**
now includes `knowledge` (five-source search), `molecular-dynamics`
(isolated OpenMM CPU demonstration) and `ecosystem` (full status and
permissions registry). Other pictured engines remain visible as
license-/dependency-reviewed **planned integrations** until their genuine
numerical capabilities have passed separate tests. None is falsely treated
as an unrestricted plug-in, and no private patent screenshots were
uploaded to this public repository.

The independently maintained EleutherAI benchmark also completed for
Qwen3-0.6B and Qwen3-1.7B. Results favored 1.7B on some of the
eight-question public tasks, but are **too small for model promotion**.
[Protocol and actual scores](docs/SCIENTIFIC_ECOSYSTEM.md).
