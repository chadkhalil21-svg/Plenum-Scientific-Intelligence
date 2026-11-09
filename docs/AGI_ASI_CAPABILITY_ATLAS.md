# Plenum Prometheus | AGI / ASI Capability Atlas and Reuse-First Execution Decision

**Recorded:** 2026-11-08 ET. **Evidence source:** inspected live `main` repository and canonical `research-memory/state/AGI_PROGRAM.json`, compared with maintained, original upstream repositories / documentation as listed below. **Scope:** all disciplines, physical simulations and digital twins, synthetic worlds, experimentation engines, scientific knowledge, engineering agents, model inference/training, evaluation, causal models, measurements, governance and AGI/ASI progress. This atlas supersedes indiscriminate lists of "install everything." Actual package versions, licenses, API terms and hardware must be checked when first selected; external links do not establish Plenum installation or scientific capability.

## Executive decision

**NO, the configuration is not yet optimal.** The building blocks are sensible, but the main constraint is insufficient independently demonstrated *generalizable reasoning, planning, multimodal understanding, reliable long-horizon autonomous work, empirically grounded scientific discovery and continual learning*. It is **not** a lack of generic simulator brands or another browser stack. As of this review the public repo contains **103 GitHub Actions workflow files**, **89 `src/plenum_ai` Python modules**, **71 `docs` files** and **33 service files**. This is not evidence of AGI; it suggests a high maintenance and CI-trigger surface. Do not refactor the entire repository merely to reduce counts; consolidate workflows **only after** a measured recurring cost or failure justifies a narrowly scoped change.

**Default decision in all future chats:**
1. Read live `AGENTS.md`, `docs/LEDGER.md`, `docs/CONTINUITY_AND_REUSE.md`, this atlas, `docs/SCIENTIFIC_DIGITAL_TWINS.md`, and the canonical `research-memory/state/AGI_PROGRAM.json`. **Prior results take precedence over older prose.** The repo cannot automatically inject this knowledge into a new chat without being retrieved.
2. **Reuse existing Plenum component -> adopt exact upstream release/checkpoint/API -> smallest adapter -> develop missing core only as a last resort.** Prefer one incumbent per functional role, not hundreds of installations. No blanket cloning, copying, plugin installation or downloading weights.
3. **Inherit published upstream validation**. Never redo an original regression suite just to prove an established tool works. On first use: check package provenance, terms and one import/ABI/interface contract if required. Only *new Plenum scientific claims*, novel species/geographies, data transformation, model customization or consequential deployment demand independently observed evidence and fresh tests. Synthetic simulated observations must be explicitly labeled.
4. Before any run, name the **unanswered capability**, exact existing implementation, task, outcome metric, budget, success criterion, privacy/license boundary, and fallback. Do **not** treat imported tool count, generated articles, simulated benchmark wins, agent count or green CI as AGI progress.
5. Keep the public GitHub repo free of unpublished founder IP, personally identifying data, credentials, private sessions and proprietary measurements. Approve spending / production changes / physical actuation separately.

## A. Inventory: already integrated vs not yet

Status vocabulary: **executed** = actual narrow upstream/software run evidenced; **partial** = limited upstream/import/adapter capability, not general tool autonomy; **declared** = optional dependency listed but not installed on deployed runtime; **reference** = research/design candidate, not installed or executed.

| Layer | Present Plenum components | Evidence-grade boundary |
|---|---|---|
| Language reasoning | Frozen small **Qwen3** checkpoints with scored original Inspect/LM Harness benchmarks; larger Qwen3.6-27B/Kaggle intended | Narrow public tasks, performance mixed. 27B inference not verified; no AGI |
| Planning & continuity | **LangGraph**, SQLite checkpoints, evidence ledger, research-memory branch | Narrow graph/checkpoint recovery, not persistent independent research agent spanning arbitrary contexts |
| Coding | **OpenHands SDK** editor tools and **Inspect ReAct**, sandbox and SWE-bench integration planning | Real editor operations and tiny original coding problems; not generalized autonomous repository engineer |
| Research/knowledge | OpenAlex, Europe PMC, arXiv, OSTI, Semantic Scholar adapter, public research radar, indexed evidence; PaperQA2 partial | Actual provider availability varies; PaperQA retrieval showed misses; retrieved paper title does not imply verified finding |
| Web operation | Official **Playwright / Playwright MCP**; public chat->GitHub browser; one user-approved signed restored **demo** login ([issue 259](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/259)) | One exact owner-approved public demo is verified; arbitrary authenticated sites/changes/files and Work/TinyFish parity NOT verified |
| Numerical/physical science | **NumPy, SciPy**, fixed numerical solvers, **OpenMDAO, NASA Aviary, OpenMM, PyBaMM, Astropy, RDKit**, optional isolated **PySCF** | Reference cases and bounded scientific computations, **not** validated aerospace aircraft, biomedicine, industrial twins, or original theoretical advances |
| Mathematics | **Lean 4** compiler kernel accepts reference proofs and rejects intentionally false proof | Not original autonomous theorem discovery; do not use unverified axioms or sorry |
| World-model research | SciPy/scikit-learn action-conditioned synthetic ODE and controlled action reversal | Synthetic transfer tests only; V-JEPA 2.1 or action-conditioned vision model not run |
| Environmental twins | NOAA [historical shadow-state replay](NOAA_SHADOW_TWIN.md), two real observed gauge series, frozen harmonics, past-data residual updates | **Verified historical observation-linked shadow** only; neither live sensor sync, calibrated spatial twin, nor operational flood warning |
| Plant/forage | Official **PCSE 6.0.13** optional `plant` extra includes LINGRA, WOFOST, LINTUL | **Declared, not installed/executed by Plenum**. Inherit upstream ryegrass/Belgian/Dutch validations, don't rerun them |
| Other interfaces | LiveKit Agents optional import, creative studio, model/skills catalog | Voice and creative interfaces are not independent evidence of intelligence |
| Self improvement | Controlled model/scoring/algorithm experiments and negative outcomes | No open-ended safe, measured, cross-task reliable self-improvement, automatic architecture evolution, or AGI |

## B. Comprehensive reusable scientific engine and modeling landscape

Each entry below is a **choice for a specific future problem**, NOT an instruction to install the whole collection. Models supplied in other packages are not physical evidence for a different species, climate, materials design or experiment.

| Question family | Preferred tested incumbent / targeted original upstream alternatives | Adoption gate |
|---|---|---|
| Ordinary differential equations, stochastic / hybrid systems | **Already SciPy**; optional [SciML DifferentialEquations.jl](https://github.com/SciML/DifferentialEquations.jl) for proven unsupported scale/solver type | Only add Julia engine if a real numerical gap exists |
| PDEs, elasticity, thermal, stress | [FEniCSx/DOLFINx](https://github.com/FEniCS/dolfinx); [OpenFOAM](https://openfoam.org/) for specialized CFD | Reference/field-scale physical question, mesh, boundary conditions and terms |
| Fluid, air, water, MHD flow and spacecraft aerodynamics | Existing Aviary/OpenMDAO for aircraft sizing; [SU2](https://github.com/su2code/SU2) or [OpenFOAM](https://openfoam.org/) for CFD | Choose one by flow regime, hardware and validation requirements; no claim MHD flight possible from toy solver |
| Coupled mechanical/electrical/thermal industrial systems | [OpenModelica](https://openmodelica.org/) and Modelica/FMI for exchanging established subsystems | Only when a specific cross-domain physical twin needs co-simulation; do not invent another coupling format |
| Robotics rigid-body/control and biomechanics | [MuJoCo](https://github.com/google-deepmind/mujoco) first; [Robotics Toolbox](https://github.com/petercorke/robotics-toolbox-python) for kinematics; [Isaac Lab](https://github.com/isaac-sim/IsaacLab) for justified GPU-scale use | No robot pilot without tasks, valid geometries and sensor/actuation constraints |
| Agent-driven virtual environments | [Gymnasium](https://github.com/Farama-Foundation/Gymnasium), [PettingZoo](https://github.com/Farama-Foundation/PettingZoo), [Mesa](https://github.com/mesa/mesa), SimPy | Adopt one environment format only if policy learning / multiagent / discrete-event questions demand it |
| Plant growth, forage, crop/soil and plant architecture | **Existing optional PCSE/LINGRA/WOFOST**; [BioCro](https://github.com/biocro/biocro), [OpenAlea](https://openalea.readthedocs.io/), [APSIM](https://github.com/APSIMInitiative/ApsimX), DSSAT | Upstream published experiments inherited; new bahiagrass/soil/biochemical or Florida-conditions claims require real own observations |
| Metabolism and biochemical reaction networks | [COBRApy](https://github.com/opencobra/cobrapy), [COPASI](https://copasi.org/), Tellurium/libRoadRunner | Select flux-balance vs reaction-kinetics solver based on mechanism and data; native SBML where supported |
| Cell/tissue, microbiomes, physiology | [PhysiCell](https://github.com/MathCancer/PhysiCell); OpenSim for measured human biomechanics as appropriate | Literature and model examples inherited; not clinical efficacy or new human outcomes |
| Molecular dynamics and electronic chemistry | **Existing OpenMM, RDKit, PySCF**; only add specialized [DiffDock](https://github.com/gcorso/DiffDock), [OpenFold](https://github.com/aqlaboratory/openfold), [Boltz-2](https://github.com/jwohlwend/boltz) for defined structure/affinity task | Separate model-code license, checkpoint rights and actual assay/structural validation |
| Materials, atomistic and manufacturing | **Existing RDKit/PySCF/OpenMDAO**; [pymatgen](https://github.com/materialsproject/pymatgen), ASE, LAMMPS, FEniCSx | No claim of validated material properties without appropriate experiments |
| Batteries, grids and thermodynamics | **Existing PyBaMM**; [pandapower](https://github.com/e2nIEE/pandapower), EnergyPlus | Physics/reference cases do not equal tested product aging or whole-grid deployment |
| Photonics, electromagnetics, wave/optical design | [Meep](https://github.com/NanoComp/meep) FDTD, other established solvers depending on wavelength/regime | Establish optical geometry and physical detector measurements; check GPL and component terms |
| Space, celestial mechanics and Earth observation | **Existing Astropy, NOAA/USGS, NASA Aviary**; NASA [GMAT](https://github.com/nasa/GMAT), NASA Earthdata CMR | Use real ephemeris and satellite/ground observational data; no warp-drive physics proof |
| Quantum algorithm simulations and noise | [Qiskit](https://github.com/Qiskit/qiskit), [PennyLane](https://github.com/PennyLaneAI/pennylane), [Mitiq](https://github.com/unitaryfoundation/mitiq) | Test actual quantum algorithm only if objective calls for it; solver simulation is not quantum advantage |
| 3D geometry, sensors, photogrammetry | [Open3D](https://github.com/isl-org/Open3D), native computer-vision models | Need sensor input, calibration, reconstruction accuracy, not merely generated 3D scenes |
| Live IoT state of a real counterpart | [Eclipse Ditto](https://eclipse.dev/ditto/) (digital-twin **state middleware**, not a scientific simulation engine) | **Deferred** until multiple physical devices/observations require bidirectional state and policy sync; NOAA shadow does not need new IoT stack |

**Source review:** authoritative upstream links above. A mature solver's original validation is inherited **only within its published domain and conditions**. Codes and the checkpoints or datasets they consume may have distinct usage/redistribution terms.

## C. Other critical engines: testing, synthetic experiments and scientific reasoning

These matter as much as the simulations. **Synthetic data are not new ground truth.** Separate upstream reliability from verification of *Plenum's new capability*.

| Function | Reusable mature original source | Current decision |
|---|---|---|
| Agent/model evaluation runner | **Existing [Inspect AI](https://inspect.aisi.org.uk/)** / Inspect Evals; previously used lm-evaluation-harness | **KEEP** one scorer; do not add HELM as duplicate. HELM has been in maintenance mode since June 2026 |
| Scientific coding and independent research replication | [SciCode](https://github.com/scicode-bench/SciCode), [CORE-Bench via Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals), [FutureHouse Aviary](https://github.com/Future-House/aviary) | **HIGH PRIORITY**: choose one difficult, unfamiliar original task to measure ability; use upstream scoring, not rebuild grader |
| Real repository-level software engineering | [SWE-bench](https://github.com/SWE-bench/SWE-bench), OpenHands SDK | **HIGH PRIORITY**: a held-out issue and original repository tests, not a toy coding demo |
| Autonomous ML engineering | [MLE-bench](https://github.com/openai/mle-bench), [AutoResearch](https://github.com/karpathy/autoresearch) as research methodology | **CONDITIONAL**, GPU/time limited; use existing grader; do not train huge models before a real need |
| Interactive browser and desktop tasks | [BrowserGym/AgentLab](https://github.com/ServiceNow/BrowserGym), [OSWorld](https://github.com/xlang-ai/OSWorld) | **CONDITIONAL evaluator**. Do not reimplement Playwright or auth; full benchmarks are heavier than an initial bounded task |
| Multi-agent environments and planning | [Gymnasium](https://github.com/Farama-Foundation/Gymnasium), [PettingZoo](https://github.com/Farama-Foundation/PettingZoo), FutureHouse Aviary | Controlled task environments **when needed**, not evidence that 100,000 cloned agents are useful |
| Experimental design and optimization | [Ax](https://ax.dev/), [BoTorch](https://github.com/pytorch/botorch), [Optuna](https://github.com/optuna/optuna) | **Candidate for next actual experimental optimization task**. Prefer existing OpenMDAO where already functional |
| Causal analysis, interventions and counterfactuals | [DoWhy](https://github.com/py-why/dowhy) | **High intellectual value**, but useful only with explicit causal assumptions/measurement, not just simulation |
| Sensitivity and uncertainty quantification | [SALib](https://github.com/SALib/SALib); [PyMC](https://github.com/pymc-devs/pymc), [Pyro](https://github.com/pyro-ppl/pyro) for probabilistic modeling | **HIGH priority method** in a new empirical twin; select smallest numerical method per real outcome |
| Synthetic tabular-data generation | [SDV](https://github.com/sdv-dev/SDV) (Business Source License), simple NumPy synthetic fixtures | **DEFER** SDV until a specific privacy/synthetic-data use case and license review; synthetic data cannot substitute for lab/field validation |
| Dataset/model artifact provenance | Existing Git SHA, immutable reports, public evidence, checksum archive; [DVC](https://github.com/iterative/dvc) / [MLflow](https://github.com/mlflow/mlflow) | **REUSE EXISTING** provenance unless actual scale/experimentation requires versioned large external artifacts |
| Agent-program/prompt optimization | [DSPy](https://github.com/stanfordnlp/dspy) | **OPTIONAL** only after frozen, independently scored objective with stable budget; avoid prompt overfitting to public tests |
| Formal math and symbolic proofs | **Existing Lean 4**, native SciPy/symbolic solvers by task; [SymPy](https://github.com/sympy/sympy) for symbolic algebra | Use original exact solvers first; proof generation is distinct from proof checking |
| Research literature and knowledge | Existing OpenAlex, Europe PMC, arXiv, OSTI, Semantic Scholar; existing PaperQA2 has incomplete retrieval | Improve source verification and citation tracing for a real unknown question; do not download all papers or replace existing federation |
| Long-horizon reliability measurement | [METR task-completion time horizon methodology](https://metr.org/time-horizons/) | Adapt an externally defined outcome metric to actual authorized tasks; don't infer AGI from token context length or elapsed uptime |

## D. Underused scientific data and interoperability, not more modeling algorithms

Use **official data endpoints when a relevant research question arises**, not all as daily polling feeds. The user should not need to manually upload public scientific databases. Do not ingest restricted licensed full text or personal health/private patents into public GitHub.

- **Existing:** NOAA CO-OPS observed water levels, USGS gauges, NASA astrophysics/exoplanets; OpenAlex, Semantic Scholar (availability failures reported), Europe PMC, arXiv, DOE OSTI and global lab/institutional radar.
- **Molecular and biological:** [RCSB PDB APIs](https://www.rcsb.org/docs/programmatic-access/web-apis-overview) (experimental structures and models), [UniProt](https://rest.uniprot.org/) (protein sequence/annotation), [ChEMBL](https://www.ebi.ac.uk/chembl/) (bioactivity), PubChem and [NCBI Datasets](https://www.ncbi.nlm.nih.gov/datasets/) for actual described genomes/compounds. Match database ID, provenance, license and evidence quality per query.
- **Plants and ecology:** [USDA NASS Quick Stats](https://data.nass.usda.gov/Quick_Stats/), official soil datasets, field phenotyping and meteorology. **SoilGrids REST API currently reports paused service**: [ISRIC status](https://isric.org/explore/soilgrids/); select their bulk/download alternatives rather than building on a disabled live API.
- **Planetary Earth:** [NASA Earthdata CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html), NOAA and USGS, satellite sensor archives. Model source latency and measurement quality explicitly.
- **Research-model exchange:** SBML/EnzymeML (biology), Modelica/FMI (physical co-simulation), experiment metadata/units and immutable instrument calibration. Reuse community formats, not a proprietary Plenum universal-model language.

## E. AGI and ASI capability map

There is **no scientifically agreed numerical AGI/ASI completion percentage**. This is an evidence ladder, **not** a prediction of distance, timeline or proof of conscious experience.

| Capability | Plenum state | Required original evidence to progress |
|---|---|---|
| 1. Deterministic domain tool use | **Narrow demonstrated** | Already adequate for selected scientific reference tasks; preserve and stop repeating |
| 2. Language, reasoning and coding | **Limited, mixed Qwen original scores** | Run larger, stronger suitable model on an unfamiliar multi-domain externally scored suite; record real compute, reliability and baseline |
| 3. General agent control/long-horizon memory | **Early graphs and restricted browser task** | Complete unknown multi-step tasks with safe self-correction, interrupts, resumption and authenticated boundaries on heldout tasks |
| 4. Vision/audio/embodied world understanding | **Not broadly demonstrated** | Video representation+action prediction in genuinely unfamiliar real measured environments; pretrained V-JEPA 2.1 small is a candidate, V-JEPA 2-AC a separate action-conditioned path |
| 5. Robust cross-domain scientific investigation | **Tool-based research and narrow prospective protocols** | Independently scored new hypotheses, correctly cited sources, design and analyze simulations and prospective experiments, compare with strong scientific baselines |
| 6. Continuous learning and transfer | **Not established** | Measurable held-out improvement on **new**, unrelated tasks without losing old skills; checkpoint, rollback, no test contamination |
| 7. Scientific/engineering originality and reliable agency | **Not established** | Independently replicated genuinely useful new designs/discoveries beyond memorized/published examples, with human-domain experts where necessary |
| 8. Broad independent AGI | **Not established** | Consistent general competence across unfamiliar domains, modalities, tools and long-horizon real-world settings; independent expert audit, well-stated operational definition |
| 9. ASI | **Not established; no defensible distance estimate** | Would require demonstrating reliably and broadly superhuman performance across essentially all relevant cognitive domains; the existence of many tools or agents is not enough |

**Current decision:** Plenum has an **early, multi-tool scientific research prototype** (rungs 1–3 only in bounded examples), not AGI and not ASI. Avoid "75% to AGI" charts or fabricated performance forecasts. The number of GitHub workflows or code modules should never be used as an intelligence metric.

## F. Shortest path from here (no more generic integrations)

**Priority 0: stop duplicate support work.** Keep main working, use the browser's already verified one-use demo connection, the validated numerical engines, and existing LangGraph/Inspect. Do **not** rebuild solver, browser, evaluator, scheduler, global literature database or layer another framework for its own sake. Condense CI only upon measured actual slowdown/failure. Record errors as independent build failures, not reasons to retest every upstream solver.

**Priority 1: raise actual reasoning/agent capability.** Rather than write another wrapper, obtain real measured Qwen inference results for a stronger **existing** checkpoint (exact SHA, license, cost) and use the existing Inspect evaluator on **one unfamiliar externally scored multistep scientific-coding or research task**. Compare direct answer, tool use and verified task completion; record partial failures. Evidence must separate inference quality from formatting, short token budgets, ambiguous task grading and pretraining overlap.

**Priority 2: connect reasoning to a real scientific question.** Use existing NASA/NOAA/USGS and published specialist model/data sources to make a new immutable forecast or prediction **before** outcome arrives, with uncertainty and stronger original-domain baseline, then independently score real observations. Do not contaminate scheduled Nov 12–13 prospective measurements or interpret historical replay as a live twin.

**Priority 3: embodied and causal world understanding.** Use existing SciPy prototype as cheap baseline; only if rights-cleared real video/action dataset and capped GPU exist, load **official** pre-trained V-JEPA 2.1 ViT-B (80M) or select V-JEPA 2-AC for a genuine action task. Validate actual event prediction and out-of-distribution transfer, not published results re-creation. MuJoCo is only necessary for an action/robotics question that current cheap baseline cannot evaluate.

**Priority 4: scientific breadth, selectively.** Native PCSE LINGRA for an actual grassland question; COBRApy for actual metabolic-model question; OpenFOAM/SU2 for validated CFD geometry; Meep for a genuinely defined Plenum optical problem; no automatic installations. Inherit upstream scientific validity under its own original conditions. New Plenum Terra/AION/aerospace performance requires **separate actual physical evidence**.

**Priority 5: adaptive improvement with oversight.** Reuse existing Inspect, OpenHands, LangGraph and controlled training facilities; only after stable hidden evaluation and a clear resource ceiling, compare one self-revision or optimized planner versus frozen same-cost baseline. No unrestricted recursive self-modification, self-deployment or large independent agent army; maintain founder controls, audit trail and rollback.

**Stop rule:** Once the solution works for the defined need, stop extending infrastructure. Promote only outcomes measured on genuine new tasks with reproducible provenance. Nothing in this document authorizes spending, new private data access, physical experiment or model-promotion.

## Primary upstream inspection notes

- [Meta official V-JEPA 2.1 and V-JEPA 2-AC](https://github.com/facebookresearch/vjepa2) share a repository but **V-JEPA 2.1 80M is an encoder**, not complete controllable digital twin or stand-alone AGI.
- [MuJoCo](https://github.com/google-deepmind/mujoco) provides an established physics engine, [Gymnasium](https://github.com/Farama-Foundation/Gymnasium) and [PettingZoo](https://github.com/Farama-Foundation/PettingZoo) provide standard single/multiagent environments. Don't reimplement the environment API.
- [Eclipse Ditto](https://eclipse.dev/ditto/) supplies authenticated IoT state and synchronization, **not** physics; do not install without real device-state synchronization need.
- [SciCode](https://github.com/scicode-bench/SciCode), [FutureHouse Aviary](https://github.com/Future-House/aviary), [MLE-bench](https://github.com/openai/mle-bench), [CORE-Bench in Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals) provide task environments/scoring to reuse, not retrain or recreate.
- [SALib](https://github.com/SALib/SALib), [DoWhy](https://github.com/py-why/dowhy) and [Ax](https://ax.dev/) address sensitivity, causal inference and adaptive experiments that a generic simulator does not automatically solve.
- [SDV](https://github.com/sdv-dev/SDV) is **Business Source License**, not freely interchangeable with MIT packages.
- [Stanford HELM](https://github.com/stanford-crfm/helm) entered maintenance mode June 1, 2026; keep existing Inspect instead.
- [ISRIC SoilGrids](https://isric.org/explore/soilgrids/) official REST API status says temporarily paused; avoid assuming live availability.
- No broad claim that every upstream license is preapproved or that all external models, weights or data have been audited. Explicit test only when adoption is necessary.

**Cross references:** [LEDGER](LEDGER.md), [SCIENTIFIC_DIGITAL_TWINS](SCIENTIFIC_DIGITAL_TWINS.md), [JEPA_WORLD_MODELS_AND_SIMULATION](JEPA_WORLD_MODELS_AND_SIMULATION.md), [SCIENTIFIC_ECOSYSTEM](SCIENTIFIC_ECOSYSTEM.md), [CONTINUITY_AND_REUSE](CONTINUITY_AND_REUSE.md), canonical [AGI program state](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/blob/research-memory/state/AGI_PROGRAM.json).
