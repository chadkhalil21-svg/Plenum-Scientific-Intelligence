"""Separate implementation audits a frozen synthetic phrase-ranking benchmark."""
import hashlib
import json
import re


def independent_accuracy(cases, weight):
    if not cases:
        raise ValueError("Empty evaluation split")
    correct = 0
    for case in cases:
        question = case["query"].casefold()
        query_words = set(re.findall(r"[a-z0-9]+", question))
        values = []
        for title in case["titles"]:
            title_lower = title.casefold()
            common = len(query_words & set(re.findall(r"[a-z0-9]+", title_lower)))
            values.append(common + (weight if question in title_lower else 0))
        chosen = max(range(len(values)), key=values.__getitem__)
        correct += chosen == case["best_index"]
    return correct / len(cases)


def independent_audit(data, evaluation):
    train, holdout = data["train"], data["holdout"]
    train_queries = {x["query"].casefold() for x in train}
    holdout_queries = {x["query"].casefold() for x in holdout}
    if len(train) < 8 or len(holdout) < 8 or train_queries & holdout_queries:
        return {"passed": False, "reason": "splits_too_small_or_overlapping"}
    baseline, candidate = evaluation["baseline"], evaluation["candidate"]
    measurements = {
        "baseline_train": independent_accuracy(train, baseline["weight"]),
        "baseline_holdout": independent_accuracy(holdout, baseline["weight"]),
        "candidate_train": independent_accuracy(train, candidate["weight"]),
        "candidate_holdout": independent_accuracy(holdout, candidate["weight"])
    }
    expected = (baseline["train_accuracy"], baseline["holdout_accuracy"],
                candidate["train_accuracy"], candidate["holdout_accuracy"])
    same = all(abs(a-b) < 1e-12 for a,b in zip(measurements.values(), expected))
    passed = same and measurements["candidate_train"] > measurements["baseline_train"] and measurements["candidate_holdout"] > measurements["baseline_holdout"] and evaluation.get("accepted_for_proposal") is True and evaluation.get("deployed") is False
    return {
        "passed": passed, "matches_claimed_metrics": same,
        "train_n": len(train), "holdout_n": len(holdout),
        "benchmark_sha256": hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
        "recomputed": measurements,
        "scope": "synthetic_text_ranker_only_not_general_A_I_improvement",
        "deployment_authorized": False
    }
