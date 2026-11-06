# Scientific Tool Registry and External Sources

**Policy:** link to upstream projects, install pinned reviewed packages as dependencies, and build narrow tested adapters. Do not copy bulk repositories or execute unreviewed skill instructions.

## Verified executable integrations
| Integration | What is actually executable | Status |
|---|---|---|
| SciPy | Newtonian orbit, thermal, first-order kinetics and RC numerical fixtures | Tested |
| RDKit | Known ethanol molecular structure descriptors | Tested |
| LangGraph 1.2.20 | Parallel per-tool workers (dynamic Send), fan-in, dependent stages | Tested in multi-tool Actions |
| OpenMDAO 3.45.2 | Constrained cooling-area optimization depending on verified SciPy thermal result | Tested |
| OpenAlex | Bounded scientific metadata | Live checked earlier |
| NASA Aviary 1.0.1 | Aircraft package official check plus bounded public Advanced Single Aisle CLI mission | Verified commands (runs 42159140408 and 42159565273), independent aircraft performance validation **not** established |

## Public sources and curated references
- Federated metadata (OpenAlex, Europe PMC, Semantic Scholar): concurrent bounded requests, DOI-level deduplication, explicit provider failure reporting. Do not claim full-text access or bibliographic truth. Actual live provider success is established only by an Actions report.
- K-Dense [scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills): curated read-only skill catalog. Pinned upstream SHA `a25cf9ec00e2745d03f8704acf6f6919694ccd9a`. Skills are **untrusted Markdown** requiring individual license, security and dependency review before any installation.
- NASA [Aviary](https://github.com/OpenMDAO/Aviary): source SHA `c005ea797e6f67ba4098ed9624b9c8fa08961ff3` and installed published version `1.0.1`.
- NASA [GMAT](https://github.com/NASA/GMAT): mission-design engine; not installed or integrated in Plenum.
- [AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2): reference only pending custom-license and generated-code security review.
- [Stanford Biomni](https://github.com/snap-stanford/Biomni): candidate biomedical tools, not installed.
- [Karpathy AutoResearch](https://github.com/karpathy/autoresearch): architectural reference only; verify permission to reuse before copying.
- [Lean 4](https://github.com/leanprover/lean4): mathematical proofs, planned.
- [SU2](https://github.com/su2code/SU2): CFD, planned.
- [OpenMM](https://github.com/openmm/openmm): molecular dynamics, planned.
- [PySCF](https://github.com/pyscf/pyscf): quantum chemistry, planned.
- [PyBaMM](https://github.com/pybamm-team/PyBaMM): battery simulation, planned.
- [pymatgen](https://github.com/materialsproject/pymatgen): materials simulation, planned.
- [Astropy](https://github.com/astropy/astropy): astronomy, planned.
- [ToolUniverse](https://github.com/mims-harvard/ToolUniverse): biomedicine tools, planned.

## Reproducibility and permissions
- PyPI executable dependency pins: LangGraph 1.2.20 and OpenMDAO 3.45.2; check transitive versions from the workflow artifact.
- Upstream source revisions for auditing: LangGraph `5847733bcb186c26b32da5cc822eaf8a89deffeb`, OpenMDAO `c36ee430b71d6918daa5418bdaf1df70cef04102`. These are **source references**, not proof PyPI wheels correspond to those exact commits.
- No unrestricted dynamic Python, shell, privileged network operations, or self-deployment.
- Tests demonstrate fixed scientific examples, not validated novel inventions, clinical efficacy, general-purpose science modeling or AGI.
- Github Actions uses temporary public CPU environments; scale beyond these examples requires job scheduling, quotas and computing budgets.

## v0.8 Additional verified scientific integrations

- **Astropy + NASA Exoplanet Archive:** unit-aware Keplerian calculations on NASA Planetary Systems records (run 42160359555). Code is in `src/plenum_ai/nasa_exoplanets.py`. Astropy is an optional package, installed using `.[astronomy]`. The sample is not a proof of independent physical validation because some archive orbital parameters are mathematically derived.
- **PyBaMM 26.10.1.1:** two working default electrochemical lithium-ion simulations, SPM and SPMe (run 42160642565). Code is in `src/plenum_ai/battery_model.py`; install using `.[battery]`. Currently a verified isolated workflow, not a general parallel-worker tool; no measured cell validation or patented battery implementation.
- Both integrations retain explicit scientific-evidence and provenance boundaries, work without paid AI inference subscriptions, and use public GitHub Actions runners.

## v0.9 NOAA empirical coastal data
- NOAA CO-OPS observed `hourly_height` station archive, fixed training and
  holdout dates, bounded read-only HTTP response and strict timestamp checks.
- NumPy fixed-harmonic least-squares fit, first compared against a proper
  same-hour previous-day persistence baseline on entirely withheld observed
  water levels. No model training on the held-out period.
- Independent GitHub workflow
  [42161428637](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42161428637)
  passed. The method won at Boston and Virginia Key for the one predeclared
  historical day. It is registered as `noaa.tides` in a **separate
  controlled workflow**, not authorized for unrestricted agent execution.
- Full evidence, caveats and permanent compact data source fingerprints:
  [Empirical Forecasting](EMPIRICAL_FORECASTING.md) and
  [Noaa evidence](../evidence/noaa/2025-06-17.json).

## Persistent knowledge, public article rights and standardized evaluation
- LangGraph checkpointer `langgraph-checkpoint-sqlite==3.1.3` with a
  strictly validated thread ID, local SQLite file and second-process recovery.
  The checkpoint is a lightweight local feature, not a horizontal cloud store.
- Local SQLite FTS5 bibliography retrieval and rehydration from approved
  checksum-verified public `research-memory` branch entries.
- Europe PMC single-article JATS XML, exact Creative Commons license parsing,
  article title, DOI and bounded paragraph extraction; no restricted
  publisher crawling or uncontrolled bulk ingestion.
- EleutherAI `lm-eval==0.4.13` standardized comparison of explicit
  Qwen3-0.6B and Qwen3-1.7B public models, separate read-only CPU workflow.
  Eight items per task are a smoke benchmark, not evidence for production.
- PaperQA2 can be installed later as the main grounded scientific-document
  reasoning interface when a suitable explicitly configured LLM service,
  licensing policy and document storage exist.

## 2026-11 pictured-resource expansion
All referenced engines and international knowledge sources are inventoried in
[Scientific Ecosystem](SCIENTIFIC_ECOSYSTEM.md). The new combined metadata
worker queries five public providers with separate bounded failures.
arXiv and DOE OSTI returned three live metadata records each in run
42167088294. Material Project credentials remain unconfigured.
OpenMM v8.6.1 passed a bounded Reference CPU synthetic bond simulation in
run 42167232309; no real biomolecular modeling claims are warranted.
