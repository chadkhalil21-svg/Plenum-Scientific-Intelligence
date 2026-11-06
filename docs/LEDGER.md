# Engineering and Scientific Ledger
Established: 2026-11-05

| ID | Work | Status |
|---|---|---|
| 001 | Public GitHub repository and constitution | Implemented |
| 002 | OpenAlex bounded literature search | Implemented; live network verified, run 42150258387 |
| 003 | Optional local LLM proposer / independent critic roles | Qwen3 CPU inference verified; no always-on model deployed |
| 004 | Deterministic orbital-mechanics example | Implemented; unit tests included |
| 005 | Narrow benchmark-driven ranker improvement proposal | Implemented; no automatic deployment |
| 006 | CI, daily and manual research Actions | Verified; memory archival job has branch-write permission |
| 007 | Persistent research memory and evaluation records | Verified for two runs; advanced orchestration remains planned |
| 008 | Integrated NASA, mathematics, fluid, chemistry and materials solvers | Planned |
| 009 | Self-modification proposals with independent review and rollback | Planned |
| 010 | Local model fine-tuning and generalized capability evaluation | Planned |
| 011 | Verified AGI | Unsolved research goal |
| 012 | Machine consciousness | Unsolved research goal |

## Working rules
A passing test only proves what it actually exercised. Each improvement must be compared with a baseline and unseen evaluation cases. Unverified hypotheses must never be labeled discoveries.

## Priority workstreams
A. AI foundation and reliable autonomous workflow.
B. Mathematical and physical verification systems.
C. Science literature and reproducible experiments.
D. AI memory/hardware architecture: electronic, photonic, molecular and protein concepts.
E. Scientific simulation adapters and ultimately robotic validation.

## Autonomous mission and model extension (2026-11-05)
- [x] Add bounded multi-role mission orchestration and evidence-labeled output.
- [x] Add deterministic one-dimensional insulated heat equation simulator with conservation validation.
- [x] Wire mission to the unattended research workflow.
- [x] Add optional CPU open-weight model adapter and GitHub Actions demonstration.
- [x] Verify CPU model inference, simulation and artifact on GitHub run 42149615125 (135M model). The artifact showed prompt repetition: inference worked but content quality failed human inspection.
- [x] Verify Qwen3-0.6B inference and a basic output-quality gate, run 42150718097; passing a syntactic gate does not demonstrate scientific validity.
- [ ] Establish substantial independent model evaluations, sandbox tool use and reproducible scientific agent tests.
- [ ] Build on-demand local Ollama daemon for genuine persistent autonomy (requires an always-on machine).
- [ ] Integrate real scientific solvers and independently validate their predictions.

- [x] Live OpenAlex retrieval and deterministic simulator verified in GitHub workflow 42150258387, with five publication metadata records.
- [x] Qwen3-0.6B CPU inference generated substantive text and passed an initial echo screen (run 42150086623), but human inspection detected fabricated bibliographic citations. This output is NOT scientifically acceptable.
- [ ] Re-run Qwen3 against actual public literature; forbid free-form citations and fail the content gate when it invents unsupported references. Any passing syntactic gate still requires expert scientific review.

## v0.3 Public memory and measured improvement
- [x] Research-memory branch created.
- [x] Bounded SHA-256 content-addressed scientific metadata and search code.
- [x] Separate benchmark implementation audits frozen 12 train and 12 holdout examples.
- [x] Research workflow reads archive, produces records and attempts to persist only public data through a dedicated scoped job.
- [x] Verify live public memory publication (workflow 42151821047; archive entry 8eb8532d9833c41f4a23cd76).
- [x] Verify subsequent memory recall: workflow 42151928822 archived record 514586158143c8315a33dcfa, which references prior record 8eb8532d9833c41f4a23cd76.
- [ ] Improve beyond synthetic text-ranking tests using external, out-of-domain benchmarks.
- [ ] Human-reviewable candidate code/weights and rollback, no unattended deployment.

## 2026-11-05 v0.3 verification note
Two successive live public research runs independently returned five publication metadata records each, appended SHA-256-addressed records on `research-memory`, and reported a passing narrow synthetic ranker audit. The second record explicitly references the first. This verifies cross-run memory retrieval and controlled archival, not scientifically sound autonomous invention, broad self-improvement, retraining, consciousness, or AGI. No paid AI service was enabled.

## v0.4 Scientific simulation and agent research
- [x] Implement real SciPy ODE simulations for orbital mechanics, reaction kinetics, material cooling and electronic RC discharge.
- [x] Integrate RDKit chemical structure descriptors, fixed publicly known ethanol fixture.
- [x] Add an allowlisted specialist router and research workflow combining literature, optional open-weight model proposer/critic, scientific tool execution, and an independent evidence supervisor.
- [x] Add method comparison for RK45, DOP853 and Radau across four known-equation scientific domains; no source code or model weights are automatically modified.
- [x] GitHub scientific lab verification: run 42152625695 passed all tests and five domain fixtures.
- [x] Complete updated Qwen3 model-driven investigation pipeline with live literature, science tools and text-quality gate, run 42152898614. This is not evidence of autonomous scientific discovery.
- [ ] Replace small known analytical fixtures with independently validated simulations and empirical benchmark data for each subject.
- [ ] Evaluate model reasoning on unseen interdisciplinary research tasks before claiming genuine improvement.
- [ ] Integrate extended open-source scientific solvers and add memory-based experimental selection, subject to budget and safety controls.

### v0.4 measured numerical efficiency (GitHub run 42152625695)
Across four known-equation fixtures, DOP853 required 1,256 solver function evaluations, RK45 required 2,930, and Radau required 12,903. Every method passed its narrow analytic reference checks. This is an *evaluation-count* comparison for the specified tolerances and models, not a wall-time comparison, hardware energy measurement, validated scientific innovation, or universal algorithm ranking. The results remain proposals only; no code or weights were changed automatically.

## v0.5 Small model training, validation and independent test
- [x] Train standard logistic-regression and random-forest candidates on public botany, wine-chemistry and handwriting datasets, with frozen train/validation/test splits.
- [x] Train a simple physics-informed model for known Newtonian gravity and evaluate on held-out radii outside the training range.
- [x] Reproduce model choice in a separate evaluator and reject altered splits, unapproved models and prematurely disclosed test results.
- [x] Free GitHub Actions run 42154005299 passed and produced the test report; candidates exceeded dummy baselines in all four tasks.
- [x] Held-out accuracy: botany 97.37% versus 31.58% dummy; wine 100% versus 40% dummy; digits 96.67% versus 10.22% dummy. Physics synthetic MAE: 8.32e-16 versus 3.60 m/s² dummy.
- [ ] Persist and verify model artifacts securely for optional manual deployment, without loading untrusted serialized code.
- [ ] Evaluate the foundation language model against genuinely independent scientific reasoning benchmarks, rather than just public reference datasets.
- [ ] Set up bounded, parameter-efficient training of open-weight language models once appropriate GPU capacity is available.
- [ ] Run qualified expert review of any proposed new scientific invention. This result does not establish AGI, consciousness or general self-improvement.

## v0.6 Foundation-model reasoning and self-improvement experiment
- [x] Pinned baseline model Qwen/Qwen3-0.6B to revision c1899de289a04d12100db370d81485cdf75e47ca.
- [x] Pinned external ARC-Challenge benchmark to dataset revision 210d026faf9955653af8916fad021475a3f00453 (CC-BY-SA-4.0).
- [x] Verified CPU science evaluation run 42156895644: 2/12 correct (16.67%). Chance baseline 25%, substantial uncertainty and possible pretraining exposure.
- [x] Implemented and executed bounded Qwen3 PEFT LoRA training with original training examples and no test-data gradient updates.
- [x] Verified Qwen3 candidate training run 42157269113: 286,720 trainable adapter parameters, two optimizer steps, 2/8 correct before and 2/8 after, **0 percentage-point improvement** on paired sample. Candidate SHA-256: 9d9a3e6105f4f340cfa10ca76584919f2fd8bf2c537c5e04ae1f32f099a173be.
- [x] Saved research-only, checksum-verified safetensors candidate and manifest as GitHub artifact; 14-day retention, no automatic model deployment.
- [ ] Expand independent benchmark size and test answer-scoring calibration to avoid overinterpretation of small logit-based multiple-choice samples.
- [ ] Use qualified science training examples with documented provenance, larger and more varied evaluations, and fixed predeclared improvement criteria.
- [ ] Establish durable restricted checkpoint storage before training proprietary models or unpublished research; the public repository is not suitable.
- [ ] Demonstrate measured, statistically supported improvements in generalizable scientific reasoning. No such improvement has been shown.

## v0.7 Multi-tool orchestration and scientific integration
- [x] Build a typed scientific tool registry with licenses, versions, dependency declarations and executable versus reference-only states.
- [x] Run four scientific tools concurrently through LangGraph and verify their results.
- [x] Feed SciPy material-cooling output into a dependent OpenMDAO constrained heat-rejection optimization. The numerical result is a **toy thermal design**, not empirical engineering validation.
- [x] Verify the multi-tool GitHub Actions pipeline (run 42158954548).
- [x] Create read-only curated K-Dense scientific skill catalog pinned to a published commit; no unreviewed instructions executed.
- [x] Verify installation and official environment check for NASA Aviary 1.0.1 (run 42159140408). No aircraft mission results claimed.
- [x] Implement bounded concurrent metadata search for OpenAlex, Europe PMC and Semantic Scholar, including deduplication and per-provider errors.
- [x] Live federated provider verification: GitHub run 42159408960 returned 3 metadata records each from OpenAlex, Europe PMC, and Semantic Scholar (9 distinct records). API availability may vary.
- [x] Bounded NASA Aviary Advanced Single Aisle demonstration command completed (run 42159565273); do not treat command success as optimizer convergence or aircraft validation.
- [ ] Independently verify Aviary optimizer convergence, trace variables and compare against external published aircraft benchmarks before claiming design capability.
- [ ] Connect NASA GMAT, Lean 4, PyBaMM, OpenMM, PySCF, SU2, Astropy and domain-specialist software individually, with tests, licensing checks and bounded operating environments.
- [ ] Add persistent multi-machine graph execution, isolated scientific environments, resource quotas and model/tool capability benchmarks.
- [ ] Prove a complete question-specific hypothesis-to-validated-evidence workflow on external experimental data. Not yet achieved.
- [ ] Achieve measurable, reproducible generalizable AI improvement. AGI and consciousness remain unsolved.

## v0.7 Additional verification and automatic tool selection
- [x] Read-only pinned K-Dense RDKit skill retrieved, SHA-256 recorded and no instructions executed (run 42159591148).
- [x] Implement rule-based automatic routing by research-question terms across mechanics, thermal modeling, kinetics, circuit dynamics, RDKit and literature metadata; dependent optimization requires a thermal result.
- [ ] Replace keyword routing with independently benchmarked, resource-aware model planning. The current router is not a general AI planner.
- [ ] Implement persistent multi-job DAG scheduling with durable checkpoints, timeouts, quota accounting and isolation for expensive scientific tools.

## v0.8 NASA evidence pipeline and electrochemical battery engine

- [x] Implement Astropy calculations for stellar-mass and orbital-semimajor-axis based Keplerian period predictions with explicit physical units.
- [x] Fetch a bounded set of NASA Exoplanet Archive public Planetary Systems parameters through TAP. Successfully analyzed 80 catalog records, with 73/80 within 10% and 0.159% median absolute fractional discrepancy (GitHub run 42160359555).
- [x] Label the NASA result as catalog consistency only; independent empirical validation is **false** because orbital semimajor axes can be derived from the same law.
- [x] Add NASA evidence tool to the approved scientific registry and allowlisted multi-tool graph; maintain offline-no-fabrication behavior.
- [x] Install PyBaMM v26.10.1.1 in a separate bounded workflow and execute two ten-minute default lithium-ion battery simulations (run 42160642565).
- [x] PyBaMM SPM 3.7801 V to 3.7104 V; SPMe 3.7708 V to 3.6914 V. Models completed and passed bounded output checks; **no real battery data or proprietary parameters used**.
- [x] Updated full regression and parallel-tool integration tests to include NASA tool selection without granting new privileges.
- [ ] Identify independent measured astronomical quantities, their uncertainties and data provenance to avoid circular model comparisons.
- [ ] Compare PyBaMM models against a suitably licensed measured battery dataset with out-of-sample evaluation before suggesting real cell performance.
- [ ] Extend the persistent scientific-evidence ledger beyond bibliographic metadata and small demonstration artifacts, without disclosing proprietary research.
- [ ] Demonstrate reliable AI-directed selection of models, falsifiable hypotheses and verified improvements on truly novel interdisciplinary tasks. Not yet AGI or scientific invention.

## v0.9 First observational forecast on independently held-out measurements

- [x] Implement a fixed four-harmonic tidal-water-level hypothesis and precommit to two NOAA gauges (Boston 8443970 and Virginia Key 8723214), sixteen historical training days, and a final unseen 24-hour observation window.
- [x] Retrieve actual verified hourly water levels from NOAA's public CO-OPS API, not its tide prediction endpoint; refuse missing/duplicated measurements rather than fabricating data.
- [x] Fit sine/cosine coefficients on 384 prior observations per station, without holdout leakage. Preserve raw-source SHA-256 digests, model details and 24 measured-versus-predicted records per station in the run artifact.
- [x] Use a fixed previous-day same-hour baseline, with identical 24 held-out measurement targets for both models.
- [x] GitHub workflow 42161428637 passed: Boston MAE 0.323731 m vs 0.340083 m baseline (4.81% reduction); Virginia Key MAE 0.065938 m vs 0.086875 m baseline (24.10% reduction). Both station-specific hypotheses supported **only on this fixed retrospective day**.
- [x] Archive exact quantitative summary, input data SHA-256 and GitHub revision permanently at `evidence/noaa/2025-06-17.json`.
- [x] Record the failure and correction of an overly strong synthetic unit-test assumption. The fixed prediction algorithm, stations, NOAA date window and scoring were unchanged.
- [ ] Extend to predeclared unseen dates, weather regimes, multiple seasons, and additional gauges with honest failures and uncertainty intervals.
- [ ] Compare to strong external tide-forecast products and proper operational skill metrics on independent periods.
- [ ] Build a genuine AI planner that proposes and tests experiments beyond predefined analytical models, with scientist oversight. **The present hypothesis was authored by the developer, not autonomously discovered by the foundation model.**
- [ ] Demonstrate reliable generalized AI improvement. Better retrospective coastal predictions are not proof of AGI, novel physics or a new invention.

## v0.9b Seasonal generalization audit (same frozen model)

- [x] Commit three additional predeclared 2025 seasonal holdouts (March 17, September 17, December 17) at each of Boston and Virginia Key, with no change to the original four-harmonic forecasting model.
- [x] Keep raw NOAA hourly observation fingerprints, fixed station IDs, dates, physical periods, training/test sizes and failure outcomes.
- [x] Run independent time-split evaluation on 384 training observations and 24 held-out future observations **per station/day**; total 144 fresh target observations across six cases.
- [x] GitHub workflow 42161902806 passed. Harmonic forecast MAE (weighted across all cases) **0.17205 m**, persistence baseline **0.21878 m** (21.36% lower). Model beat baseline in **four of six** station-days.
- [x] Preserve failures at Virginia Key in March and Boston in December, without reselecting dates, removing cases, or claiming all contexts improved.
- [x] Permanently archive exact metrics and observation SHA-256 digests at `evidence/noaa/2025-seasonal-independent.json`.
- [ ] Expand to at least several dozen independently chosen station-days and report confidence intervals, strong baselines and weather/surge subgroups before asserting operational skill.
- [ ] Test generalization to genuinely novel scientific research tasks proposed by the AI. This model was manually specified and verified through code, **not** autonomously invented or improved by the foundation model.

## v1.0–v1.1 Autonomous scientific hypothesis-selection and evidence gate

- [x] Qwen3-0.6B selects from four approved testable tide-forecast hypotheses using development-only historical data; the proposer has no access to held-out observations.
- [x] A separate independent GitHub Actions job measures those decisions on observed NOAA water levels, retains failures, and archives public audit evidence to the separate `research-memory` branch.
- [x] Ungated Qwen3 run 42162579029: all four choices were persistence, producing **0/4 wins** over that baseline, and losing to the fixed four-harmonic model in every case.
- [x] Engineer a deterministic minimum-development-error evidence gate without viewing future-day measurements. Original 2026 July/October proposals were unavailable at NOAA; no outcomes observed. Substitute predeclared previously untested 2025 January/November dates.
- [x] Evidence-gated run 42163393864: **2/4 wins against ungated Qwen, 2/4 ties**. Mean MAE gate 0.18613 m, ungated 0.22366 m, four-harmonic reference 0.17501 m. The gate **did not beat the fixed scientific reference overall**.
- [x] Confirm all three run jobs passed, including write-restricted evidence archival, under `research-memory/evidence/agent-experiments/run-42163393864.json`.
- [x] Repair CLI auditor import-name collision and verify complete engineering test suite.
- [ ] Evaluate on much larger independently held-out research datasets and compare against stronger physical references, not only weak baselines.
- [ ] Test unbiased prompt/choice calibration and larger independent language models; the current Qwen3 choices all favored persistence.
- [ ] Connect hypothesis proposal to more real scientific solvers and properly independent empirical measurements, with human-reviewed permissions and compute budgets.
- [ ] Demonstrate generalized AI learning or improvement of foundation-model weights. **Not yet achieved.**

## Persistent intelligence infrastructure, scientific-library rights, and benchmark foundations

- [x] Add a real LangGraph SQLite checkpointer and save/reopen verified scientific worker outcomes across separate processes. Bounded investigations cannot accidentally be rerun under the same thread ID.
- [x] Add a searchable local SQLite FTS5 bibliography and excerpt index, with DOI, provenance, explicit license and content hashes.
- [x] Rebuild indexed source metadata from checksum-verified existing `research-memory` entries; the public memory Git branch remains a persistent cross-run knowledge source.
- [x] Retrieve a single full-text article through Europe PMC and verify the article's machine-readable Creative Commons license before indexing a bounded excerpt. Refuse unlicensed or unknown-content rights.
- [x] Verify the local checkpoint and open-license retrieval on GitHub Actions run 42165442498. All jobs succeeded.
- [x] Optimize five specialist science workflows so a shared `pyproject.toml` change does not rerun expensive isolated simulations unnecessarily.
- [x] Add manual owner-controlled **Plenum Research Control Center** for science, public knowledge, licensed articles, durable checkpoints and verification.
- [x] Add independent EleutherAI LM Evaluation Harness workflow with public Qwen3 0.6B and 1.7B candidates on ARC-Challenge and PIQA. No automatic model promotion.
- [ ] Evaluate considerably larger, more diverse and truly unexposed scientific tasks before interpreting model-comparison accuracy as a general reasoning improvement.
- [ ] Add a configured, trusted language-model backend for PaperQA2-class multi-document reasoning; no hosted LLM or paid API was activated.
- [ ] Add a long-lived, permissioned worker/queue and production-quality persistence. Local SQLite checkpoints alone are not cloud continuity or horizontal scaling.
- [ ] Keep proprietary patent material and research in a separate private environment with encryption, private backups and authorized access.
- [ ] Establish experimentally reproduced new scientific discoveries and generalizable model self-improvement. Neither has been demonstrated.

## Verified operator console, cross-run retrieval and first external model score

- [x] Live founder console on GitHub Actions: run 42166252075; approved public science question selected two numerical tools, reported two worker results and passed known-model checks.
- [x] Daily autonomous public research + memory integration: run 42166035006; research and isolated-memory archival jobs both passed. The public research-memory branch can be re-indexed on future runs.
- [x] Independent official EleutherAI benchmark for Qwen3-0.6B: run 42165601852, ARC-Challenge 2/8 (25%) and PIQA 5/8 (62.5%), zero-shot, eight public samples each. Not enough for a production choice.
- [x] Reduce unnecessary CPU usage: five specialist workflows no longer rerun on general dependency edits; central CI skips documentation-only changes but still runs for source, test and dependency edits.
- [ ] Require a larger independent scientific/agent benchmark before model promotion. The larger Qwen3-1.7B CPU candidate is being evaluated separately; no outcome is assumed until its workflow finishes.
- [ ] Configure dedicated always-on computing, durable off-runner database and private researcher-controlled storage only with founder-approved resources and budget.

## Expanded pictured-science ecosystem and reproducible verification

- [x] Inventory every scientific engine shown in the founder's screenshots,
  with upstream links, execution permissions, scientific boundaries and
  planned/credential-gated/verified statuses. See `docs/SCIENTIFIC_ECOSYSTEM.md`.
- [x] Implement additional read-only arXiv Atom and US DOE OSTI JSON adapters,
  composed with three existing worldwide scholarly indexes for five-source
  concurrent search and DOI-based provenance deduplication.
- [x] Five-source live GitHub test 42167088294 passed with 12 distinct records:
  OpenAlex 3, Europe PMC 3, arXiv 3, OSTI 3; Semantic Scholar returned an
  HTTP error. The provider outage remains explicit, not concealed.
- [x] Keep Materials Project API credential-gated and not connected. The
  personal key is not published, inferred or requested in this public repo.
- [x] Install isolated pinned OpenMM 8.6.1 on free GitHub CPU hardware,
  execute 100 reference molecular-dynamics steps and verify independent
  harmonic initial energy (1.25 kJ/mol) with relative conservation error
  approximately 7.18×10^-6 (run 42167232309).
- [x] Expose worldwide scholarly search, the audited full ecosystem registry
  and isolated OpenMM engine from the founder's iPad GitHub control center.
- [x] Complete EleutherAI Qwen3 0.6B versus 1.7B external model-comparison
  workflow (run 42165601852); accuracy sample too small for promotion.
- [x] Preserve all uninstalled Lean4, DiffDock, PySCF, pymatgen, SU2, ToolUniverse,
  GMAT and other ambitious integrations as **staged**, not falsely operational.
- [ ] Install and independently validate the next high-value scientific
  engines, their scientific data, licensing and resource budgets one at a
  time. No general drug-design, protein-folding, formal-proof or advanced
  aircraft-design system is yet validated.
- [ ] Improve foundational reasoning with larger genuine scientific
  benchmarks, independent agents and more capable persistent compute before
  claiming AGI or recursive model improvement.
