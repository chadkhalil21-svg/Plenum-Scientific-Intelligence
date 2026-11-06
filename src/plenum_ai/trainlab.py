"""Reproducible *small ML* training across scientific datasets and physics.

All candidates are trained only on training examples, selected solely on a
validation split, and judged on a held-out test split not used for selection.
This trains new small sklearn models, NOT a foundation model, AGI, or Qwen3.
"""
from hashlib import sha256
from json import dumps
import numpy as np

TASKS = ("botany", "chemistry", "handwriting", "gravity")
SEED = 20261105
G = 6.67430e-11
EARTH_KG = 5.9722e24


def _dataset(task):
    from sklearn.datasets import load_iris, load_wine, load_digits
    from sklearn.model_selection import train_test_split

    if task not in TASKS:
        raise ValueError("Unapproved research benchmark")
    if task == "gravity":
        rng = np.random.default_rng(SEED)
        # Training and selection occur at lower orbital distances.
        train_domain = rng.uniform(6.8e6, 12.0e6, size=(260, 1))
        # Extrapolation test is created independently beyond train/validation range.
        test_domain = rng.uniform(14.0e6, 22.0e6, size=(100, 1))
        X = np.vstack((train_domain, test_domain))
        y = (G * EARTH_KG / X[:, 0] ** 2)
        train, dev = train_test_split(
            np.arange(260), test_size=0.25, random_state=SEED
        )
        holdout = np.arange(260, 360)
        kind = "regression"
        provenance = "synthetic Newtonian inverse-square gravity, out-of-range holdout"
    else:
        bundle = {
            "botany": load_iris,
            "chemistry": load_wine,
            "handwriting": load_digits,
        }[task]()
        X = np.asarray(bundle.data, dtype=float)
        y = np.asarray(bundle.target)
        indexes = np.arange(len(y))
        fit, holdout = train_test_split(
            indexes, test_size=0.25, stratify=y, random_state=SEED
        )
        train, dev = train_test_split(
            fit, test_size=0.25, stratify=y[fit], random_state=SEED + 1
        )
        kind = "classification"
        provenance = "scikit-learn public reference dataset; held-out stratified examples"
    if len(set(train) & set(dev)) or len(set(train) & set(holdout)) or len(set(dev) & set(holdout)):
        raise AssertionError("Benchmark split leakage")
    manifest = {
        "task": task, "seed": SEED, "type": kind, "source": provenance,
        "train_size": len(train), "selection_size": len(dev),
        "holdout_size": len(holdout),
        "split_sha256": sha256(dumps(
            {"train": train.tolist(), "selection": dev.tolist(),
             "holdout": holdout.tolist()}, sort_keys=True
        ).encode()).hexdigest(),
    }
    return X, y, train, dev, holdout, manifest


def _model(task, name):
    from sklearn.dummy import DummyClassifier, DummyRegressor
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler, FunctionTransformer

    if task == "gravity":
        if name == "baseline":
            return DummyRegressor(strategy="mean")
        if name == "inverse_square_linear":
            # The known physics transform is supplied by humans: not AI discovery.
            def inverse_square(x):
                return (8.0e6 / x) ** 2
            return make_pipeline(FunctionTransformer(inverse_square, validate=True),
                                 LinearRegression())
        if name == "random_forest":
            return RandomForestRegressor(
                n_estimators=50, max_depth=10, random_state=SEED, n_jobs=1
            )
    else:
        if name == "baseline":
            return DummyClassifier(strategy="most_frequent")
        if name == "scaled_logistic":
            return make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=1000, random_state=SEED)
            )
        if name == "random_forest":
            return RandomForestClassifier(
                n_estimators=50, max_depth=14, random_state=SEED, n_jobs=1
            )
    raise ValueError("Unapproved model family")


def _candidates(task):
    return ["inverse_square_linear", "random_forest"] if task == "gravity" else [
        "scaled_logistic", "random_forest"
    ]


def _metric(task, actual, predicted):
    from sklearn.metrics import accuracy_score, mean_absolute_error
    if task == "gravity":
        return float(mean_absolute_error(actual, predicted))
    return float(accuracy_score(actual, predicted))


def propose(task):
    """Model selection sees training and development examples, never holdout."""
    X, y, train, dev, _hidden, metadata = _dataset(task)
    scores = {}
    for name in _candidates(task):
        model = _model(task, name)
        model.fit(X[train], y[train])
        scores[name] = _metric(task, y[dev], model.predict(X[dev]))
    minimize = task == "gravity"
    selected = min(scores, key=lambda k: (scores[k], k)) if minimize else max(
        scores, key=lambda k: (scores[k], k)
    )
    return {
        "manifest": metadata, "candidates": scores, "selected": selected,
        "selection_metric": "validation_MAE_lower_better" if minimize
        else "validation_accuracy_higher_better",
        "test_results": "sealed_until_independent_audit",
        "deployment_authorized": False,
    }


def audit(task, proposal):
    """Independently rebuild the split and evaluate *one* frozen selection."""
    X, y, train, dev, holdout, manifest = _dataset(task)
    if proposal.get("manifest") != manifest:
        raise ValueError("Benchmark provenance mismatch")
    if proposal.get("selected") not in _candidates(task):
        raise ValueError("Model outside candidate allowlist")
    if proposal.get("test_results") != "sealed_until_independent_audit":
        raise ValueError("Holdout was disclosed prematurely")
    # Independently reproduce the development split comparison, but never
    # use holdout data for model or prompt selection.
    independently_selected = propose(task)["selected"]
    if independently_selected != proposal["selected"]:
        raise ValueError("Candidate failed independent selection replay")
    fit = np.concatenate([train, dev])
    candidate = _model(task, proposal["selected"])
    baseline = _model(task, "baseline")
    candidate.fit(X[fit], y[fit])
    baseline.fit(X[fit], y[fit])
    prediction = candidate.predict(X[holdout])
    baseline_prediction = baseline.predict(X[holdout])
    candidate_metric = _metric(task, y[holdout], prediction)
    baseline_metric = _metric(task, y[holdout], baseline_prediction)
    improved = (candidate_metric < baseline_metric) if task == "gravity" else (
        candidate_metric > baseline_metric
    )
    from sklearn import __version__ as sklearn_version
    from sklearn.metrics import balanced_accuracy_score
    return {
        "task": task, "manifest": manifest, "selected_model": proposal["selected"],
        "baseline_holdout_metric": baseline_metric,
        "candidate_holdout_metric": candidate_metric,
        "metric": "mean_absolute_error" if task == "gravity" else "accuracy",
        "balanced_accuracy": (
            float(balanced_accuracy_score(y[holdout], prediction))
            if task != "gravity" else None
        ),
        "beats_baseline_on_held_out_examples": bool(improved),
        "holdout_used_for_selection": False,
        "independent_selection_reproduced": True,
        "sklearn_version": sklearn_version,
        "trained_weights_persisted": False,
        "deployment_authorized": False,
        "scientific_discovery_verified": False,
    }


def run_training_lab(tasks=TASKS):
    """Engineer-proposed models get a separate holdout audit and evidence report."""
    tasks = tuple(tasks)
    if not tasks or len(tasks) > 4 or len(set(tasks)) != len(tasks):
        raise ValueError("Choose 1..4 distinct benchmark tasks")
    if any(task not in TASKS for task in tasks):
        raise ValueError("Unapproved benchmark task")
    findings = []
    for task in tasks:
        proposal = propose(task)
        verdict = audit(task, proposal)
        findings.append({"task": task, "proposal": proposal, "audit": verdict})
    return {
        "experiment": "plenum-scientific-ml-training-v0.5",
        "type": "small_trainable_models_not_frontier_language_model",
        "tasks": findings, "evaluated_tasks": len(findings),
        "candidate_beats_dummy_in_all_tasks": all(
            row["audit"]["beats_baseline_on_held_out_examples"] for row in findings
        ),
        "deployment_authorized": False,
        "automatic_model_promotion": False,
        "AGI_demonstrated": False,
        "scientific_discovery_verified": False,
        "limitations": [
            "Iris, wine and digits are small public benchmarks, not unseen scientific research.",
            "Gravity dataset is synthetic and derived from a known physical equation.",
            "Test labels are excluded from model choice, not guaranteed unseen by humanity.",
            "Performance against dummy baselines does not imply general intelligence.",
            "Learned model weights are trained in the run but not deployed or preserved.",
        ],
    }
