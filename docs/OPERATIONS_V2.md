# Plenum Operating Architecture: Verified Foundation and Next Gates

Last engineering review: 2026-11-05 (U.S. Eastern).

## Executive design decision

Keep a single owner-directed intelligence and scientific investigation layer.
Reuse independently maintained scientific tools and evaluation software.
Do **not** merge all external repositories into this one, run untrusted
scientific skill instructions, or assume a passed software test proves
general intelligence or a scientific discovery.

## Current tested foundations

| Capability | Actual implementation | Evidence category |
|---|---|---|
| Concurrent scientific tools | LangGraph bounded fan-out with SciPy, RDKit and dependent NASA-origin OpenMDAO | Verified integration fixtures |
| Durability | LangGraph SQLite checkpointer; thread state reopened from a second process | Local filesystem checkpoint only |
| Cross-run public memory | Research-memory branch stores checksum-verified JSON and source links | GitHub public evidence branch |
| Searchable knowledge | SQLite FTS5 citation index; rebuilt from archived public memory | Local index, not web-scale knowledge graph |
| Open-access article | Europe PMC XML fetch with explicit article-level CC URL license, excerpt indexing and SHA-256 | One licensed source at a time |
| Scientific benchmark | EleutherAI LM Evaluation Harness ARC-Challenge and PIQA with CPU 0.6B/1.7B candidates | Public, small, not fully blind |
| Founder control | GitHub Actions Plenum Research Control Center | Manual selection; no autonomous remote execution |
| Improved AI | No generalizable capability gain or model promotion established | Research objective |

## Operate from iPad or iPhone

1. Open GitHub repository [Plenum Scientific Intelligence](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence).
2. Select **Actions → Plenum Research Control Center → Run workflow**.
3. Select a preapproved operation:
   - `science`: routes a public question to bounded concurrent scientific tools;
   - `knowledge`: rehydrates public memory records, retrieves fresh public research metadata from OpenAlex, Europe PMC and Semantic Scholar, and writes a local FTS5 search result;
   - `licensed-article`: verifies a specified Europe PMC article's declared open license and indexes a bounded local text excerpt;
   - `durable-investigation`: stores a graph checkpoint, reopens it in a second process, and produces evidence artifacts;
   - `verify`: runs independent engineering tests.
4. Download and inspect the resulting GitHub artifact. These files are retained **14 days**; it is the user's responsibility to preserve any required local checkpoint DB beyond that period.

Only use *public* questions, sources and research on this public repository.
Do not enter unpublished patents, confidential business plans, credentials,
personal information, or protected medical records.

### Persistent means what?

The SQLite checkpoint survives **process restarts on the same retained disk**.
It does not turn GitHub's temporary runner into an always-on server.

GitHub's `research-memory` branch persists approved public bibliographic
records and independent experiment evidence across workflow runs. The library
can be reconstructed each run from those verified records.

For concurrent long-running agents on multiple machines, migrate from SQLite
to a production database and task queue with access controls, encryption,
backups and cost limits. This change needs deployment resources, which this
repository does not silently activate.

## Scientific retrieval, copyright and citations

- Federated metadata from OpenAlex, Europe PMC, Semantic Scholar: search
  results must include provenance and never be confused with paper truth.
- The fulltext bridge fetches JATS XML using an exact PMC identifier and a
  single approved host. It requires an explicit CC0, CC BY 3/4 or CC BY-SA
  4 article license URI. Unlicensed/unknown/restricted text is refused.
- Only a bounded excerpt is indexed locally, with title, license, DOI,
  primary URL and content checksum. No bulk scraping or publisher bypass.
- PaperQA2 would supply stronger multi-paper retrieval and citation-grounded
  answering, but still **requires an explicitly configured language model
  backend**. That is not running continuously on our present CPU workflows.
- Publisher retractions, references and conflicting sources need further
  provenance and expert review before independent scientific conclusions.

## Independent intelligence evaluations

The official EleutherAI LM Evaluation Harness workflow tests two **open,
public foundation-model candidates**, Qwen3-0.6B and Qwen3-1.7B, on
ARC-Challenge and PIQA. Each task currently uses only eight samples to
bound runtime. The larger model's memory/runtime requirements can exceed a
free CPU runner; a failed run is not a score.

The model revision and evaluation framework version must be stored in the
artifact. **No automatic promotion, model switch, inference bill or silent
production deployment is authorized.**

Important: these questions may have appeared in the models' pretraining.
Public benchmark accuracy cannot establish original research ability, AGI,
self-evolution or consciousness. Before selecting a stronger model:
- Increase independent multi-domain evaluation sizes and confidence intervals.
- Test tool use, multi-step scientific planning, evidence citation,
  hallucination/refusal behavior and failure recovery.
- Evaluate with genuinely unexposed private tasks in a secure environment.
- Calculate inference cost per accepted, independently verified solution.

## External repositories and integration decisions

| Project | Decision | Why |
|---|---|---|
| LangGraph | Keep; SQLite checkpoint tested | Dependable bounded task graph |
| NASA OpenMDAO, Aviary | Keep | Mature validated engineering packages; model accuracy still domain-specific |
| PyBaMM, SciPy, RDKit, Astropy | Keep | Specialized physics, chemistry and numerical calculation |
| K-Dense scientific-agent-skills | Curated, pinned, read-only | Skill instructions are not trusted code |
| PaperQA2 | Add when LLM backend and privacy storage are ready | Avoid reimplementing scholarly RAG |
| Inspect AI | Next agent audit interface | Independent tool-use and behavioral evaluation |
| EleutherAI LM Evaluation Harness | Integrated as separate bounded workflow | Compare model accuracy with standardized tasks |
| Hugging Face TRL / Karpathy AutoResearch | Later, isolated | Requires training compute and independent promotion criteria |
| Stanford Biomni / ToolUniverse | Later, per-tool reviewed | Biomedical tools require extra safety and data governance |
| NASA GMAT, Lean 4, SU2, OpenMM, PySCF | Separate sandboxed adapters | Large specialized dependencies |
| vLLM | Later with dedicated GPU | Higher-throughput model serving; not suitable for a free CPU runner |
| Sakana AI Scientist v2 | License-reviewed reference only | Generated-code execution and nonstandard license |

## Efficiency changes

Five specialized scientific workflows no longer rerun merely because
`pyproject.toml` changed. The central CI test still checks each code push.
The founder-facing console consolidates the main actions while preserving
specialist workflows for debugging and reproducibility.

## Remaining work, not yet completed

- Select and deploy an accurate general reasoning model on cost-controlled,
  owner-approved compute.
- Make PaperQA2 (or equivalent) run against a permissioned, persistent paper
  collection and a configured inference server.
- Add robust long-term hybrid retrieval with retractions and source graph.
- Run Inspect AI tool-use evaluations against unseen tasks, failure cases,
  and multiple candidate models.
- Establish an always-on worker service, monitoring, backups, a production
  queue and private patent-safe research storage with human-approved funding.
- Demonstrate scientifically novel, independently reproduced hypotheses
  and proven AI capability improvement. Neither is established.

The governing objective is evidence-supported improvement, not maximizing
the count of integrated repositories.

## World Intelligence control and ongoing operation

The Control Center now exposes `world-intelligence`, `universities`,
`defense-public`, `foreign-affairs`, `business`, `environment`,
`world-news`, `journals`, `code-ecosystem` and `build-program`.
World source checks are read-only. All institution titles and links are
untrusted data and are not executed as prompts or code.

Daily worldwide source verification is configured on the GitHub
`world-horizon.yml` workflow (07:37 America/New_York). The pipeline can
archive its public snapshot on a write-restricted separate research branch.
The journal and university source endpoints may change or reject requests,
and data outages are not silent. Scheduled public GitHub workflows can
be disabled after 60 days of no repository activity.

For `build-program`, choose one of `research_cli`,
`data_validator` or `geometry_designer`, provide a **public** topic
and inspect the generated files, tests and manifest. These are original
starter programs and are not deployed or auto-merged. Proprietary coding
work should remain in a separate private environment.
