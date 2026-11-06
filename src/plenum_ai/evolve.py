"""Reproducible narrow software improvement proposal with a holdout; never self-deploy."""
import json
import re
from pathlib import Path

WORDS = re.compile(r"[a-z0-9]+")


def tokens(text):
    return set(WORDS.findall(text.casefold()))


def score(query, title, phrase_weight):
    overlap = len(tokens(query) & tokens(title))
    exact = int(query.casefold() in title.casefold())
    return overlap + phrase_weight * exact


def accuracy(cases, weight):
    correct = 0
    for case in cases:
        predictions = [score(case["query"], title, weight) for title in case["titles"]]
        best = max(range(len(predictions)), key=lambda i: predictions[i])
        correct += int(best == case["best_index"])
    return correct / len(cases)


def evaluate_evolution(cases):
    train, holdout = cases["train"], cases["holdout"]
    baseline_weight = 0.0
    candidate_weights = [0.0, 0.5, 1.0, 2.0]
    best_weight = max(candidate_weights, key=lambda w: (accuracy(train, w), -w))
    baseline_train = accuracy(train, baseline_weight)
    baseline_holdout = accuracy(holdout, baseline_weight)
    candidate_train = accuracy(train, best_weight)
    candidate_holdout = accuracy(holdout, best_weight)
    accepted = candidate_train > baseline_train and candidate_holdout > baseline_holdout
    return {
        "component": "toy_literature_ranker_exact_phrase_weight",
        "baseline": {
            "weight": baseline_weight, "train_accuracy": baseline_train,
            "holdout_accuracy": baseline_holdout,
        },
        "candidate": {
            "weight": best_weight, "train_accuracy": candidate_train,
            "holdout_accuracy": candidate_holdout,
        },
        "accepted_for_proposal": accepted,
        "deployed": False,
        "limits": "A narrow synthetic benchmark gain does not establish AGI or general scientific ability.",
    }


def default_benchmarks():
    path = Path(__file__).resolve().parents[2] / "data" / "benchmarks.json"
    return json.loads(path.read_text(encoding="utf-8"))
