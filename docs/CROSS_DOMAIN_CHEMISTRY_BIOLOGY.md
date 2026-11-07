# Plenum Cross-Domain Research-Methode Benchmark

**Status:** bounded public historical research benchmark, not AGI, scientific invention, clinical validation or autonomous self-improvement.

## Why this matters

Plenum already has experiments in NOAA coastal-water-level forecasting and USGS river-discharge forecasting. Chemistry and biology require different targets and numerical models, providing a more substantive transfer test than another environmental station.

This study evaluates the narrow question: can independently trained AI models select bounded statistical-method parameters that generalize to separately held-out public experimental observations better than strong fixed references?

## Two real datasets, source-checked

1. **Chemistry:** Delaney ESOL, 1,128 molecules with **measured** log water solubility. Pinned to a specific DeepChem Git commit and SHA-1 blob. Only six predeclared molecular features are used. The existing column containing ESOL **predicted** solubility is EXCLUDED to prevent circular prediction leakage. RDKit Bemis-Murcko scaffold grouping separates molecules into 790 train, 170 development and 168 holdout examples. Exact acyclic molecular structures are grouped to prevent simple repeated-molecule leakage. This reduces, but does not eliminate, chemical similarity leakage.
2. **Biology:** The public UCI Wisconsin Diagnostic research dataset distributed with scikit-learn, 569 examples and 30 historical measured nuclear morphology features. A seeded, class-stratified split yields 364 training, 91 development and 114 holdout examples. The labels and features are used only in a scientific evaluation. There is **no medical decision system, clinical use, patient advice, or diagnostic validation**.

The datasets are historical and publicly known. They may have appeared in model pretraining, and this experiment is NOT a truly prospectively blinded or unmemorized AGI examination.

## Model-directed research cycle

The existing Qwen3-1.7B scientist and different-family SmolLM2-1.7B-Instruct critic each propose bounded values:

- `linear_strength` (0.02 to 25): ridge penalty in chemistry, logistic-regression inverse penalty in biology;
- `forest_leaf` (integer 1 to 12): the random forest's minimum samples per leaf;
- `mix` (0 to 1): linear-model weight in a fixed blend with random forest;
- A text hypothesis and falsification criterion, explicitly *unverified*.

The underlying algorithms are prewritten. Generated code is never executed.

Fixed references: standardized linear model and a 60-tree random forest. Chemistry uses mean absolute solubility error (log mol/L); biology uses binary log-loss. Lower is better. Models must improve on the strongest development reference by at least 2% to be selected; otherwise the stronger reference remains selected.

Independent jobs reproduce the pinned source fingerprints, splits, reference errors and selection logic before using hidden test labels. The final auditor refits each model on training plus development observations, then scores chemistry and biology holdouts and records wins, losses, invalid responses and extra computation. The public evidence is archived to Plenum's separate research-memory branch.

## Production and privacy constraints

No paid model API, persistent GPU, private Plenum patents, live clinical data, medical deployment, arbitrary model-generated Python execution or automatic self-modification is enabled. The workflow runs on temporary GitHub CPU runners with conservative timeouts. Green engineering tests never establish scientific accuracy or AGI.

The setup is **not a proof of a new chemical law, new biological discovery, generalized scientific intelligence, or recursive self-improvement**. It is a method-selection benchmark on two different disciplines with independent numerical scoring.

## Next required evidence

To approach a true AGI milestone, the system needs *unseen, newly collected* science cases, experimental design, unfamiliar mathematical formalisms, an independent verifier for real-world laboratory claims, multimodal perception, robust long-running reasoning, authenticated private memory, and repeated gains on challenging hidden evaluations. Public old datasets are only early instruments.

From an iPad: GitHub > Actions > Independently Audited Chemistry and Biology Model Challenge > Run workflow. Its output must be judged by the archived independent audit, not its language-model narrative.
