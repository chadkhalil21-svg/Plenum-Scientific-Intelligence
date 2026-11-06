# Scientific model-training laboratory (v0.5)

## Purpose
Train actual small machine-learning models from scratch or standard random initialization, select a model using *development data only*, and perform an independently replayed evaluation on test data that are not used for parameter fitting or model selection.

**This does not fine-tune Qwen3 or create an AGI.** It establishes reliable training and comparison infrastructure for future foundation-model experiments.

## Task-specific models
| Task | Dataset | Training approaches | Test |
|---|---|---|---|
| Botany | scikit-learn Iris | Standardized logistic regression; random forest | Stratified 25% held-out examples |
| Chemistry | scikit-learn Wine | Standardized logistic regression; random forest | Stratified 25% held-out examples |
| Handwriting | scikit-learn Digits | Standardized logistic regression; random forest | Stratified 25% held-out examples |
| Gravity | Deterministic synthetic Earth gravity, inverse-square equation | Physics-informed linear model; random forest | Fresh high-altitude examples beyond training range |

Each task also uses an elementary dummy baseline. The training/selection split is 75/25 of the non-test data. For the real reference datasets, 25% of all samples are reserved for final holdout; the physics test uses separately generated higher-radius points.

## Verified run 42154005299
- Botany: 38 held-out items; baseline accuracy 0.315789; selected trained model 0.973684.
- Wine chemistry: 45 held-out items; baseline accuracy 0.400000; selected trained model 1.000000.
- Handwriting: 450 held-out items; baseline accuracy 0.102222; selected trained model 0.966667.
- Gravity: 100 out-of-range synthetic items; baseline mean absolute error 3.599305 m/s²; physics-informed candidate 8.316e-16 m/s².

These numbers are reproducible test measurements, **not** claims that the underlying model is generally intelligent, newly discovered Newtonian gravity, or can invent drugs or new physics. The gravity candidate is explicitly provided the known inverse-square functional form.

## Integrity controls
1. All splits are disjoint, deterministic, and fingerprinted in the report.
2. The proposal stage sees train/development metrics and **does not report test metrics**.
3. A separate audit re-creates the split, reproduces model choice, and then evaluates once on the test split.
4. Candidate model family is fixed by an allowlist. Invalid selections, changed split IDs and early test disclosure are rejected.
5. No candidate is automatically deployed or used to alter source code or foundation-model weights.
6. Model weights are trained during each run but are not yet serialized or installed as long-lived inference services. Save and provenance-check them only after independent security and reproducibility review.

### Limitations
Public benchmark datasets may be familiar to existing AI models. These samples were unseen by the fitted sklearn candidates, **not genuinely novel scientific research questions**. Better-than-dummy performance on small, well-understood datasets is only a preliminary sanity check.

Next stages: establish third-party blind interdisciplinary evaluations, persist signed model packages, test adapters for stronger open-weight models and parameter-efficient fine-tuning, and require human approval before any production update.

### Execute
From the repository, using Python 3.11+:

    python -m pip install -e ".[ml]"
    plenum train-models --out reports/model_training.json

Or on GitHub, use **Actions → Scientific Model Training and Holdout Evaluation → Run workflow**. Inspect the downloadable report artifact.
