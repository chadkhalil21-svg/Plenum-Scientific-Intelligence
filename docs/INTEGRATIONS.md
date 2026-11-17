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

## Creative and current-research extension

- `discovery_watch.py`: 20-curated-journal Crossref roster, a whole-index topic query, recent bio/med preprints, institutional/publisher RSS feeds and public NASA YouTube video listings. Daily Actions preserve failure status and peer-review distinctions.
- `discovery_delta.py`: compare source DOI/link fingerprints against up to 120 prior archived daily reports. A record new to Plenum is **not** new to science or evidence of a breakthrough.
- `serendipity.py`: speculative research-linked art, architecture, music, agriculture, design and engineering idea prompts, with required source links and falsification reminders.
- `creative_studio.py`: original SVG geometry and MusicXML notation, with no audio playback or copied recordings.
- `creative_sources.py`: Openverse, Metropolitan Museum v1.1 and MusicBrainz public metadata only, rights labeled and independently retrievable.
- `youtube_api.py`: optional official v3 video metadata search with owner-supplied `YOUTUBE_API_KEY` secret, redacted errors and no captions/downloads.
- `docs/UNIVERSAL_DISCOVERY_AND_CREATIVITY.md`: consolidated connection requirements and status inventory for future creative/scientific resources.

## Nov 7, 2026: authenticated Kaggle and real isolated browser tests

- **Official Kaggle CLI, API authorization VERIFIED:** owner secret in GitHub `kaggle-access`, successful manual notebook-listing check ([run 42408852329](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42408852329)). Read/write code path exists but a remote Kaggle write and 27B trial have NOT yet been executed.
- **Microsoft Playwright 1.64.1 + Chromium, real CI:** public `https://example.com/` opened with HTTP 200 and a local web-page interaction typed a field and clicked a button with the expected DOM result ([run 42409395480](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42409395480)). Whitelisted public GET sites only, no accounts or site mutations, no LLM-controlled action yet. Review [Browser Autonomy](BROWSER_AUTONOMY.md) for staged website-control roadmap.
- **Service inventory:** [Connection Roadmap](CONNECTION_ROADMAP.md) marks working sources, optional owner credentials, security boundaries and expected costs. Do not install every third-party app, duplicate journal APIs, or confuse data adapters with AGI.

## 16 November 2026 — Founder-requested upstream scientific agents

The [existing reuse-first registry](../protocols/reuse_first_registry.json) and
[scientific tool registry](../src/plenum_ai/tool_registry.py) now pin all seven
requested upstream projects. Five bounded components are integrated in the original repository. No full scientist-agent runtime has been installed,
deployed, or authorized by these entries. The original **AI Scientist v2**
reference remains unchanged. The existing PaperQA2 and ToolUniverse references
are not counted as Robin or AutoScientists.

| Original project | Bounded evidence or gate |
|---|---|
| [Sakana v3](https://github.com/SakanaAI/AI-Scientist-v3/tree/de1cd267b8922faa31631fb397bbc202bf714d84) | Apache-2.0. Original fixed circle-packing evaluator, existing candidate, license, hash-verifying runner and original raw receipt now integrated ([#802](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/802)). Prior real baseline accepted (score 0.9597642169962064; two of 26 radii zero), not a Plenum-generated optimization. No agent startup, fallback API key, generated-code execution, or full runtime. |
| [Harvard AutoScientists](https://github.com/mims-harvard/AutoScientists/tree/c71a92343b9a488ed10134be805845b9473ad18f) | No license found at this revision: reference only, no copied code or installation. Reuse individually reviewed ToolUniverse endpoints already in the catalogue where appropriate. |
| [FutureHouse Robin](https://github.com/Future-House/robin/tree/4a5cce310f3bc7663a67117db88af43b84733ffe) | Apache-2.0. Bounded hypothesis-pair scheduling algorithm merged in existing upstream pilot ([#801](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/801)); no pairwise judgment, ranking, Edison, assays, or model agent. |
| [MIT ScienceClaw](https://github.com/lamm-mit/scienceclaw/tree/894598cd3a90891a077c254566276bd379038bad) | Apache-2.0. Bounded literal DNA statistics merged in existing upstream pilot ([#801](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/801)); optional Biopython 1.86. No external publication or model runtime. Separately tested upstream FEM script had an unresolved analytic 1.1–5.7 kHz vs finite-difference ~8.4 MHz discrepancy, so it is not adopted. |
| [FermiLink](https://github.com/TaoELi/FermiLink/tree/1677243532ca1631750d5a62db9763c68291fddb) | AGPL-3.0, v0.3.10. [#805](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/805) merges an optional isolated launch adapter for the pinned original laser-TLS template and separately supplied MaxwellLink v0.5.0 wheel (GPL-2.0). Original standalone 1,000-step result finite with zero conservation error; populations remain constant under orthogonal coupling. No upstream code, wheel or raw CSV redistributed, no full agent installed or model/API. New wrapper source/CI verified; original simulation was not rerun through it. |
| [Denario](https://github.com/Denario-AI/Denario/tree/f6cc751603f2caed7524cc22b31652243c7b7c97) | GPL-3.0, v1.0.1; isolated process and rights review; current analysis expects OpenAI API and that is not funded/authorized. |
| [EvoScientist](https://github.com/EvoScientist/EvoScientist/tree/b1ca788ae9c6e78f5b66df56cc770c3d0bbf55e1) | Apache-2.0, v0.4.3. Original isolated skill-creator aggregator, fixed-input runner, license and archived public GPQA aggregation merged ([#803](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/pull/803)). Existing grades aggregated without inference: 0/3 candidate vs 1/3 reference, no promotion. Raw missing-metric zero defaults are not measured observations. Full runtime requires separate dependency environment and approved local model. |

Execute the two bounded components through the original existing CLI
using only PUBLIC nonconfidential inputs:

```sh
python -m plenum_ai.upstream_pilots --provider robin --hypotheses 4 --games 6 --out reports/robin-pairs.json
python -m pip install -e '.[scienceclaw_sequences]'
python -m plenum_ai.upstream_pilots --provider scienceclaw --public-dna ACGCGTAA --out reports/scienceclaw-dna.json
```

The two existing-CLI functions were locally executed and tested and the original exact-head [upstream CI run](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/44009698260) succeeded with [bounded component receipts](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/44009698260/artifacts/14295159723), including unique pairs,
stable local random state and independently countable composition (A=3, T=1,
C=2, G=2; GC=50%). These are deterministic bounded utilities, not new scientific
results, models, or working autonomous scientists. The two new source components
cannot enter the general parallel agent graph; the original SDK check, focused
component tests and optional dependency path retain zero model and external API
calls. See [upstream attribution](../integrations/upstream/scientist-components/UPSTREAM.md).

The other two optional isolated runners preserve prior actual upstream results.
Verify without rerunning:

```sh
python integrations/upstream/sakana-ai-scientist-v3/run_fixed_baseline.py --verify-only
python integrations/upstream/evoscientist-v0.4.3/aggregate_gpqa.py
```

The archived [Sakana receipt](../integrations/upstream/sakana-ai-scientist-v3/baseline_receipt.json)
and [EvoScientist receipt](../evidence/evoscientist/2026-11-17-gpqa/receipt.json)
retain the original output identities and limitations. Sakana's adapter was
locally safety-tested; EvoScientist's [foundation CI](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/44009628593)
passed. Neither source merge establishes new model evaluation, agent execution,
general autonomy, or a discovery. Explicit run flags exist only for the fixed
reviewed inputs; do not repeat these jobs as demonstrations.

FermiLink/MaxwellLink's optional external adapter has a read-only default plan:

```sh
python integrations/upstream/fermilink-maxwelllink/run_tls.py
```

See [the exact input and execution boundary](../integrations/upstream/fermilink-maxwelllink/README.md),
the [prior original standalone execution receipt](../evidence/fermilink/2026-11-17-tls/receipt.json)
and [#805 foundation CI](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/44010597573). Explicit execution requires
separately supplied hash-pinned upstream assets and license compliance. No
automatic download, default invocation, new agent installation, model or
provider call. Constant populations establish baseline evolution only, not
driven excitation, novelty or AGI.
