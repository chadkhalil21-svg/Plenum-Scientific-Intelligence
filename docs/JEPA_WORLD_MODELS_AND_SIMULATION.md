# Plenum Prometheus: JEPA World Models, Simulators and Digital Twins

**Decision: November 8, 2026 (ET). Status: research architecture and first synthetic prediction probe; NOT a trained JEPA system, operational digital twin, AGI or ASI.**

## Founder's persistent engineering principle

Pursue **measurably more general intelligence and scientific discovery per compute dollar and hour**, not larger tool inventories or prolonged browser infrastructure. Before writing code, read AGENTS.md, the canonical research-memory AGI_PROGRAM.json, the main LEDGER, this document and actual GitHub workflow/PR evidence. Search trusted upstream. Reuse one working tool in each role. Write only the missing adapter/test. Require a held-out falsifier, license and cost gate. Record negative results and leave speculative work explicitly pending. Stop expanding support infrastructure once a useful acceptance case works. The browser is an interface for research, not the research objective.

## What LeCun and JEPA contribute

Yann LeCun, *A Path Towards Autonomous Machine Intelligence* (2022), proposes a multimodule architecture connecting **perception, world model, actor/planner, critic/cost, memory and configurator**. Intelligent behavior requires predicting changes in the environment at different temporal scales, often in **abstract representation space** instead of reconstructing all pixels.

JEPA (Joint-Embedding Predictive Architecture) learns by predicting a target representation from context:
- A **context encoder** represents observed context from images/video or other sensory states.
- A **target encoder** (commonly slowly updated/EMA, with no target gradient) represents withheld/future information.
- A **predictor** uses context and optional masks/temporal signals to predict the target's latent representation; a similarity/regression objective encourages informative representations rather than pixel-perfect reconstructions. Anti-collapse/training choices depend on the specific JEPA version.
- Passive pretraining from video primarily learns visual dynamics/representations. **Action-conditioned** adaptation and intervention/robot data are needed to evaluate the consequences of different actions and plan.
- Hierarchical, memory-guided closed-loop planning remains a research direction, **not guaranteed by fitting a representation**.

Meta FAIR published **V-JEPA 2 (2025)** with video understanding and robot planning experiments and **V-JEPA 2.1 (March 2026)** with dense predictive loss, multi-layer supervision and image/video tokenizers. The official [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) repository exposes training code and released checkpoints, including smaller 80M-parameter V-JEPA 2.1 ViT-B/16; pretrained V-JEPA 2 action-conditioned checkpoint is far larger. Review model/checkpoint license separately; repository code is MIT. No weights or model training have been installed or run at Plenum yet.

**Correction to popular summaries:** A learned representation is not automatically an accurate physical simulator or a causal model. Correlations, temporally ordered video and abstract embeddings are not sufficient to verify intervention-based causal reasoning. JEPA is also **not inherently a replacement for an LLM**: Plenum can combine language-based reasoning and tools with learned physical representations and action-conditioned planning. LeCun's view that LLM-only scaling is insufficient for general physical intelligence is a research position, not an established proof that all LLM research is a dead end.

Primary sources:
- Yann LeCun's original paper: https://openreview.net/pdf/315d43ba26f55357a84cec9a7ed15a6610094f79.pdf
- Author's page: https://yann.lecun.com/
- V-JEPA 2 paper and robot adaptation: https://ai.meta.com/research/publications/v-jepa-2-self-supervised-video-models-enable-understanding-prediction-and-planning/
- Official implementation: https://github.com/facebookresearch/vjepa2
- V-JEPA 2.1: https://arxiv.org/abs/2603.14482

## Existing Plenum capabilities, accurately classified

| Component | Current evidence | Decision |
|---|---|---|
| `src/plenum_ai/science.py` 1-D heat diffusion | Deterministic conservation fixture; no identified material calibrated | Reuse for testing; not a validated digital twin |
| `src/plenum_ai/lab.py` SciPy differential equations | Orbital, chemistry, materials and electronics controlled equations; independent numerical reference checks | Reuse reference physics + simulation environment |
| OpenMM / PyBaMM / OpenMDAO / Aviary / RDKit / PySCF | Existing optional adapters and bounded scientific functionality, individual validation varies | Reuse only on domain-matched experiments; no new general solver |
| LangGraph / Inspect AI | Limited existing orchestration and independent model evaluation | Reuse; do not invent another agent manager or evaluator |
| Video world model/JEPA checkpoint | **Not installed, trained, executed or independently benchmarked** | Stage one reproducible upstream checkpoint experiment, no auto-download |
| Integrated, reality-calibrated digital twin | **Not verified** | Require physical data, calibration, uncertainty and prospective validation |

## Deliberate upstream choices: do not clone all repositories

1. **Perception/latent world model:** Meta's original `facebookresearch/vjepa2` (MIT code, checkpoint rights reviewed independently). First target only smallest released V-JEPA 2.1 ViT-B (~80M parameters). Run inference/embedding consistency on a small, rights-cleared video corpus using a separately approved accelerator and published preprocessing. Freeze encoder; baseline against simpler encoders. Do not retrain billion-parameter models without evidence and budget.
2. **Low-cost dynamics:** Continue existing **SciPy** + scikit-learn, already optional dependencies. The world-model probe `plenum_ai.world_model_probe` fits a small action-conditioned statistical transition model on **synthetic nonlinear mass-spring motion** generated with SciPy DOP853; evaluates separately seeded unseen action sequences and parameter-shifted physics against action-blind and persistence baselines at 1/8/32-step horizons. This is **not JEPA**, a real twin or real-world generalization, and should be reported only with original metrics and failure cases.
3. **Robot/world interactions when needed:** Google's open-source **MuJoCo** (Apache-2.0) and NVIDIA **Isaac Lab** (BSD-3-Clause framework) are established physics/robot-learning engines. Choose MuJoCo for lightweight articulated-body/control tasks; choose Isaac Lab only when high-fidelity sensors, photorealism or massive parallel GPU simulation are justified by an experiment. **No physical robot, paid GPU job or simulator integration is live**.
4. **Future high-fidelity simulation:** NVIDIA/DeepMind/Disney **Newton** is an open-source extensible robot physics project; domain-specific engines from Plenum's existing science toolkit are preferable for molecular, electrochemical, engineering, climate and orbital questions. A synthetic rendering or pre-programmed simulation is not evidence of a calibrated environment.
5. **Optional research comparators:** Dreamer-style learned latent dynamics/model-based RL and 2026 literature on limits of latent planning are useful as *benchmarks/reference*. License, evaluation data, publication and compute feasibility must be reviewed before adopting, not auto-imported.

Original upstream:
- https://github.com/google-deepmind/mujoco
- https://developer.nvidia.com/isaac/lab
- https://developer.nvidia.com/newton-physics
- https://arxiv.org/abs/2609.39235 (planning horizon limitations; independently recheck before treating as consensus)

## First measured gate: action-conditioned prediction, not new infrastructure

**Question:** Can a small fitted transition predictor anticipate a nonlinear environment under new action sequences better than two fixed, action-free baselines? Does prediction degrade if the environment's mass, spring stiffness and damping change?

**What runs:** Existing SciPy `solve_ivp` generates 14 training trajectories and disjoint six-trajectory evaluation sets. Existing scikit-learn Ridge fits an observed-state transition. The test scores frozen predictors on unseen sequences and shifted dynamics at 1, 8 and 32 steps. Report actual continuous RMSE, error growth and all ablations. Source/test: `src/plenum_ai/world_model_probe.py`, `tests/test_world_model_probe.py`; added to the **existing** scientific-lab workflow, without a new simulator engine or workflow.

**Limit:** All labels come from the same stated synthetic ODE, so this is **not external empirical validation or learned visual abstraction**; even a pass is a bounded engineering/experimental result. An actual twin requires rights-cleared measurements, known calibration uncertainty, out-of-sample and prospective physical tests. Neither source simulations nor predictions should cause unapproved real-world actuation.

## Next meaningful experiment, only after the first gate

Use one upstream pretrained V-JEPA 2.1 model (smallest viable checkpoint, pinned weights/checksum and reviewed terms) to evaluate **future feature prediction and physical event ordering**, with no training as the initial condition. Compare a frozen encoder plus bounded predictor with simpler/cheap features and a nonvisual action-state baseline, reporting latency, RAM/VRAM, one-step/multistep error, occlusions, OOD shifts, and intervention prediction. Where actions are available, evaluate planning using rolling feedback rather than assuming long-horizon fidelity. Use a real-world calibrated domain only after the synthetic benchmark and licensed observations are credible.

**Stop/go rule:** If the model does not improve on simpler baselines with held-out data at tolerable compute cost, do **not** scale to multiple agents, sensors, simulations or training. Record the failure in research-memory/AGI_PROGRAM.json, and change only the validated bottleneck. A new module, green CI workflow or pretrained checkpoint is not progress toward AGI unless an independent test demonstrates an actual capability gain.
