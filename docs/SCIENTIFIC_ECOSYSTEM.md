# Scientific Ecosystem: Screenshot Inventory and Integration Plan

## Current adoption judgment (November 8, 2026)

This is an inventory of distinct execution states, **not a shopping list**. Keep the working stack: Qwen benchmark baselines; LangGraph checkpoints; official Playwright/Playwright MCP public browse route; independently tested Inspect AI; optional bounded OpenHands SDK; verified numerical solvers and public scholarly sources. Browser Use remains optional for LLM-guided public tasks; no configured provider key or general authenticated agent parity. BrowserGym/AgentLab are external benchmark candidates, not browser execution/authorization replacements. Meta V-JEPA 2.1 ViT-B (~80M) is an upstream frozen *visual representation* research option; V-JEPA 2-AC is a **separate larger action-conditioned robot system**. Neither has been inferred by Plenum. Evaluate one model and benchmark only after rights, baseline, hardware/budget and independent holdout have been established.

The current [engineering ledger](LEDGER.md) and [research-memory canonical state](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/blob/research-memory/state/AGI_PROGRAM.json) supersede earlier rows or narrative when new tests prove a more advanced *but limited* capability. Actual source and run evidence take precedence over historical screenshots. Do not install or fork an entire science-agent index when a narrow maintained upstream package solves the named task. No software installation or model change was made by this reconciliation.


Updated 2026-11-08 (current-status reconciliation; original inventory established November 6). This document incorporates the scientific engines, knowledge sources, agent frameworks and learning systems in the founder's screenshots. A repository or web link is **not** an installed, validated or authorized execution capability.

## Engineering principle

**Plenum is the coordinating intelligence, not a new copy of every solver.**
Its durable LangGraph graph and checksum-verified research memory connect
specialized executables, external literature and independent evaluators.
Each tool is separate, versioned, resource-bounded and independently audited.
A prompt cannot authorize third-party code or confidential-data access.

The broad objective is general-purpose autonomous science, engineering and
learning, not merely tide prediction. Current work is a narrower prototype
with proven pieces. AGI, subjective consciousness and recursive model
self-improvement remain unestablished.

## Scientific engines from the screenshots

| Domain | Engine | Current state | Verification and boundary |
|---|---|---|---|
| Mathematics | [Lean 4](https://github.com/leanprover/lean4) | **Verified isolated real Lean 4 CI** | Three predefined general proofs compiled; deliberate false proof rejected in run 42402969343; no autonomous theorem discovery |
| Drug discovery | [DiffDock](https://github.com/gcorso/DiffDock) | Registry: planned, license/weights review | No drug binding or efficacy claims |
| Molecular dynamics | [OpenMM 8.6.1](https://github.com/openmm/openmm) | **Verified isolated CPU engine** | Two-particle harmonic reference, not protein folding |
| Chemistry | [PySCF 2.15.0](https://github.com/pyscf/pyscf) | **Verified isolated real CPU H2 Hartree-Fock reference workflow** | One conventional known reference and stretched-bond control, not chemistry discovery; see [PySCF evidence](PYSCF_QUANTUM_CHEMISTRY.md) |
| Materials science | [pymatgen](https://github.com/materialsproject/pymatgen) | Registry: planned | Distinct from Materials Project data API |
| Aerodynamics | [SU2](https://github.com/su2code/SU2) | Registry: planned | Turbulence/mesh/geometry validation not done |
| Batteries | [PyBaMM 26.10.1.1](https://github.com/pybamm-team/PyBaMM) | **Verified isolated workflow** | Default lithium-ion SPM/SPMe, no experimental validation of Plenum technology |
| Astronomy | [Astropy](https://github.com/astropy/astropy) | **Verified NASA catalog calculation** | Orbital fields may be mathematically dependent |
| Biomedicine | [ToolUniverse](https://github.com/mims-harvard/ToolUniverse) | Registry: planned | Individual API, license, privacy and safety review |
| Multidisciplinary optimization | [NASA-origin OpenMDAO](https://github.com/OpenMDAO/OpenMDAO) | **Verified executable** | Toy heat-rejection constraint and numerical fixtures |
| Aviation | [NASA Aviary](https://github.com/OpenMDAO/Aviary) | **Verified isolated bundled example** | Not aircraft certification or A380 performance |
| Spaceflight | [NASA GMAT](https://github.com/NASA/GMAT) | Registry: planned | Separate large spacecraft solver, not a Python drop-in |
| Molecules | [RDKit](https://github.com/rdkit/rdkit) | **Verified reference calculations** | Molecular descriptors, not protein pharmacology |
| General numerical mechanics | [SciPy](https://github.com/scipy/scipy) | **Verified reference calculations** | Known gravitational, thermal, kinetic and circuit examples |

OpenMM isolated verification:
https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42167232309

OpenMM's independent harmonic-energy check began at 1.25 kJ/mol and completed
100 one-femtosecond CPU integration steps with a relative energy drift of
approximately 0.00000718. These are numerical solver checks, not measured
physical or biological results.

## Worldwide scientific knowledge sources

| Source | Interface and status | Access policy |
|---|---|---|
| [OpenAlex](https://openalex.org/) | Verified public metadata | Scholarly index, not automatically complete licensed full text |
| [Europe PMC](https://europepmc.org/) | Verified metadata + one-license-checked JATS full-text retrieval | Download/index only CC-approved article text |
| [Semantic Scholar](https://www.semanticscholar.org/) | Existing adapter; variable API availability | HTTP failures preserved, never invent results |
| [arXiv](https://arxiv.org/) | **New Atom API, verified live** | Metadata only; respect upstream terms |
| [DOE OSTI](https://www.osti.gov/) | **New v1 records API, verified live** | Public federal research metadata |
| [Materials Project](https://materialsproject.org/) | **Not connected: normally requires MP_API_KEY** | Owner-specific private credential and appropriate license |
| Broader [AI for Science software index](https://github.com/search?q=AI+for+Science+repository&type=repositories) | Reference discovery, not one combined install | Select reviewed and maintained repositories separately |

All five bibliographic adapters are in
`src/plenum_ai/global_sources.py` and `federated_sources.py`.
The global search composes the existing three-provider concurrent requests
with separate arXiv and OSTI requests. It also merges DOI-duplicate items
with original attribution; provider errors remain visible.

Live 2026-11-06 global test: **12 distinct records** returned (3 each from
OpenAlex, Europe PMC, arXiv and OSTI). Semantic Scholar returned an HTTP
error, which was reported rather than hidden. Thus **four of five** providers
were available in that run, not five of five. Complete artifact:
https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42167088294

To run from GitHub Actions, choose
**Plenum Research Control Center → knowledge**, or
**Global Public Scientific Sources Verification**.
The knowledge operation stores metadata in a local, searchable SQLite
index and can reload verified older public research memory entries.

## AI science, autonomy, research and self-improvement

| System | Role | Current Plenum relationship |
|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Concurrent agents and resumable state | **Active**, local SQLite checkpoint tested |
| [K-Dense Scientific Skills](https://github.com/K-Dense-AI/scientific-agent-skills) | Large specialized skills catalog | Pinned and curated **read-only** |
| [Stanford Biomni](https://github.com/snap-stanford/Biomni) | Biomedical research AI | Architecture candidate, not installed |
| [Sakana AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) | Hypothesis/search/experiment research architecture | License-reviewed **reference only**, not arbitrary-code executor |
| [Karpathy AutoResearch](https://github.com/karpathy/autoresearch) | Iterative automated ML training experiments | **Reference only**; no general model self-improvement loop; existing bounded experiments with negative tests should be reused before adoption |
| [PaperQA2](https://github.com/Future-House/paper-qa) | Scientific document retrieval and eventual grounded QA | **Upstream SDK and actual offline retrieval verified but insufficient** (1/2 initial top-1 public examples; exploratory 5/8 and 6/8 settings), no reliable model-generated citation reasoning yet |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | Independent model and agent audits | **Real framework and Qwen model scoring verified**, including 17/24 bounded original ARC non-thinking evaluation (run [42340974100](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42340974100)); no broad AGI validity |
| [EleutherAI LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) | Official external model benchmark | **Verified** on Qwen3 0.6B and 1.7B; eight cases per task |
| [Hugging Face TRL](https://github.com/huggingface/trl) | Candidate model training and preference methods | Later, after larger blind benchmarks and resource budget |
| [vLLM](https://github.com/vllm-project/vllm) | Efficient high-throughput model serving | Later; requires suitable inference hardware |

The independent benchmark finished successfully on CPU:
https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42165601852

| Model | ARC-Challenge raw / normalized accuracy | PIQA accuracy | Caveat |
|---|---|---|---|
| Qwen3-0.6B | 2/8 and 2/8 | 5/8 | Existing small CPU model |
| Qwen3-1.7B | 2/8 and 3/8 | 6/8 | Stronger on some metrics, **not proven superior** on 8-question samples |

There is **no automatic model promotion**: both are publicly available
models and this small benchmark may include pretraining-exposed questions.
A stronger model needs more genuinely unseen and multidisciplinary tasks,
accuracy intervals, resource/cost analysis and explicit approval.

## Founder control center

In GitHub, open **Actions → Plenum Research Control Center → Run workflow**.
Available operations include:

- `science`: bounded domain scientific graph and verified numerical examples
- `knowledge`: five public scholarly sources plus local index and archived memory
- `licensed-article`: explicit permitted JATS text indexed locally
- `durable-investigation`: local checkpoint created and recovered
- `molecular-dynamics`: OpenMM isolated two-particle Reference CPU example
- `ecosystem`: current machine-readable registry with package versions and
  active/blocked statuses, without invoking any third-party engine
- `verify`: independent engineering regression tests

There is no mechanism here to install arbitrary external repositories
automatically. The allowed choices are explicitly enumerated. A given run
may use multiple independent tools and their dependencies; it does not
need to choose one engine for the whole scientific problem.

## Remaining architecture and external requirements

1. Expand high-quality scientific reasoning/evaluation on genuinely unseen
   interdisciplinary tasks. The 1.7B result is **not** an AGI achievement.
2. Add the next scientific solver in a separate bounded environment,
   with a domain-specific reference benchmark (e.g., Lean proofs or PySCF
   electronic energy), never merely count installed packages.
3. Implement citation following, retractions and independent source-quality
   evidence rather than trusting bibliography titles alone.
4. Set up a permanent private research environment with encrypted storage
   and owner-approved computing budgets for unpublished patents and original
   research. The GitHub Actions runners and repository are public/ephemeral.
5. Add a durable multi-machine job queue and explicit capability permissions.
6. Demonstrate independently verified useful scientific invention and
   generalizable improvement before claiming autonomy or intelligence gains.

**No API credentials, payment services, private patent texts or deployable
unreviewed agents were added by this integration.**
