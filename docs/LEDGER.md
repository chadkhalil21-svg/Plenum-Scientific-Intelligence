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
