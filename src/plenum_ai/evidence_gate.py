"""Review-gated scientific model choice on *new* blind NOAA dates.

Version 1.0 was evaluated on 2026-01-17 and 2026-04-17; these dates
are explicitly excluded here because their results are now known.
The version 1.1 protocol chooses two different dates before test retrieval.

Qwen3 can suggest a model using development-only scores. A deterministic
evidence guard selects the candidate with minimum development MAE,
rejecting unsupported suggestions. Both decisions and all negative
final-day results are archived without optimizing on held-out labels.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import math
import numpy as np

from .autonomous_hypothesis import (
    LETTERS, ORDER, PERIODS, MAX_RESPONSE, _forecast, _mae,
    selection_prompt, qwen_choose,
)
from .noaa_empirical import API, STATIONS, parse_observations

FRESH_TEST_DAYS = ("2026-07-17", "2026-10-17")
MIN_TRAIN, MIN_DEV, MIN_FINAL = 250, 85, 20
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"


def _date(day):
    if day not in FRESH_TEST_DAYS:
        raise ValueError("Not a predeclared new test date")
    return datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def query(station, day, reveal=False):
    if station not in STATIONS:
        raise ValueError("Station not allowed")
    date = _date(day)
    return API + "?" + urlencode({
        "begin_date": (date-timedelta(days=16)).strftime("%Y%m%d"),
        "end_date": (date if reveal else date-timedelta(days=1)).strftime("%Y%m%d"),
        "station": station, "product": "hourly_height",
        "datum": "MLLW", "time_zone": "gmt", "units": "metric",
        "format": "json", "application": "plenum_evidence_gated_science_v11",
    })


def fetch(station, day, reveal=False, opener=urlopen):
    url = query(station, day, reveal=reveal)
    req = Request(url, headers={"User-Agent": "PlenumScientificIntelligence/1.1 experimental science"})
    with opener(req, timeout=25) as response:
        body = response.read(MAX_RESPONSE+1)
    if len(body) > MAX_RESPONSE:
        raise ValueError("NOAA response too large")
    obj = json.loads(body)
    if not isinstance(obj, dict) or obj.get("error") or not isinstance(obj.get("data"), list):
        detail = str(obj.get("error", {}).get("message", "unexpected response schema"))[:160] if isinstance(obj, dict) else "unexpected response type"
        raise ValueError("NOAA observations unavailable: " + detail)
    return parse_observations(obj["data"]), sha256(body).hexdigest()


def development(obs, day):
    cutoff = _date(day)
    first = cutoff-timedelta(days=16)
    dev_start = cutoff-timedelta(days=4)
    fit = sorted(t for t in obs if first <= t < dev_start)
    validation = sorted(t for t in obs if dev_start <= t < cutoff
                        and t-timedelta(days=1) in obs)
    if len(fit) < MIN_TRAIN or len(validation) < MIN_DEV:
        raise ValueError("Insufficient historic train/validation coverage")
    if set(fit) & set(validation):
        raise AssertionError("Train/development overlap")
    scores = {
        name: _mae(obs, validation, _forecast(name, obs, fit, validation))
        for name in ORDER
    }
    if not all(math.isfinite(value) for value in scores.values()):
        raise ValueError("Nonfinite development score")
    return {
        "training_hours": len(fit), "validation_hours": len(validation),
        "validation_mae_m": scores, "test_data_seen": False,
    }


def evidence_guard(scores, model_suggestion):
    if model_suggestion not in ORDER or set(scores) != set(ORDER):
        raise ValueError("Unapproved selection")
    if not all(isinstance(v,(float,int)) and math.isfinite(v) and v>=0
               for v in scores.values()):
        raise ValueError("Invalid validation scores")
    # Predeclared evidence gate: exact minimum validation MAE.
    # Ties favor the simpler model by the fixed order.
    best = min(ORDER, key=lambda name: (scores[name], ORDER.index(name)))
    return {
        "model_suggestion": model_suggestion,
        "selected_for_blind_test": best,
        "suggestion_accepted": model_suggestion == best,
        "guard_rule": "minimum_prior_development_MAE_ties_choose_simpler_model",
        "guard_used_final_test_labels": False,
        "original_model_selection_override": best != model_suggestion,
    }


def propose_gated(chooser=qwen_choose, opener=urlopen):
    if not callable(chooser):
        raise ValueError("A model chooser is required")
    candidates = []
    for day in FRESH_TEST_DAYS:
        for station in STATIONS:
            observations, raw_hash = fetch(station, day, False, opener)
            dev = development(observations, day)
            prompt = selection_prompt(dev["validation_mae_m"], station, day)
            letter = chooser(prompt)
            if not isinstance(letter, str) or letter not in LETTERS:
                raise ValueError("Qwen3 failed to choose an approved option; do not substitute")
            suggestion = ORDER[LETTERS.index(letter)]
            gate = evidence_guard(dev["validation_mae_m"], suggestion)
            candidates.append({
                "station": station, "day": day,
                "train_only_sha256": raw_hash,
                "prompt_sha256": sha256(prompt.encode()).hexdigest(),
                "development": dev, "model_letter": letter,
                "gate": gate,
                "falsifiable_prediction": (
                    f"{gate['selected_for_blind_test']} will have lower mean "
                    f"absolute error than prior-day persistence on {day}"
                ),
                "falsifier": "Selected forecast MAE >= persistence forecast MAE on the unseen day",
            })
    return {
        "schema": "plenum-review-gated-hypotheses-v1",
        "protocol_version": "1.1",
        "fresh_dates": list(FRESH_TEST_DAYS),
        "sites": list(STATIONS),
        "reviewed_model_menu": list(ORDER),
        "frozen_evidence_gate": "minimum_development_mae",
        "base_model": "Qwen/Qwen3-0.6B",
        "base_revision": MODEL_REVISION,
        "proposals": candidates,
        "holdout_results_known_before_policy_committed": False,
        "AI_generated_novel_equations": False,
        "production_code_or_model_modified": False,
    }


def independent_audit(proposed, opener=urlopen):
    if proposed.get("schema") != "plenum-review-gated-hypotheses-v1":
        raise ValueError("Unrecognized proposal manifest")
    entries = proposed.get("proposals", [])
    needed = [(day, station) for day in FRESH_TEST_DAYS for station in STATIONS]
    if [(e.get("day"), e.get("station")) for e in entries] != needed:
        raise ValueError("Missing, unexpected or reordered evaluations")
    if proposed.get("reviewed_model_menu") != list(ORDER) or proposed.get("frozen_evidence_gate") != "minimum_development_mae":
        raise ValueError("Altered precommitted model policy")
    reports = []
    for entry in entries:
        station, day = entry["station"], entry["day"]
        if entry.get("model_letter") not in LETTERS:
            raise ValueError("Invalid AI suggestion")
        suggestion = ORDER[LETTERS.index(entry["model_letter"])]
        # Verify development calculations and guard *before requesting test data*.
        prior, prior_digest = fetch(station, day, False, opener)
        if prior_digest != entry["train_only_sha256"]:
            raise ValueError("Historical observations changed between proposer and auditor")
        verified_dev = development(prior, day)
        old = entry["development"]["validation_mae_m"]
        if any(abs(verified_dev["validation_mae_m"][k] - old[k]) > 1e-10 for k in ORDER):
            raise ValueError("Stored development scores cannot be reproduced")
        expected_gate = evidence_guard(verified_dev["validation_mae_m"], suggestion)
        if expected_gate != entry["gate"]:
            raise ValueError("AI decision or guard changed between jobs")
        # Only now retrieve the previously sealed 24-hour observed target.
        obs, raw_digest = fetch(station, day, True, opener)
        cutoff = _date(day)
        train = sorted(t for t in obs if cutoff-timedelta(days=16) <= t < cutoff)
        test = sorted(t for t in obs if cutoff <= t < cutoff+timedelta(days=1)
                      and t-timedelta(days=1) in obs)
        if len(train) < 350 or len(test) < MIN_FINAL or set(train) & set(test):
            raise ValueError("Insufficient independent NOAA test measurements")
        measured = {}
        for name in set((suggestion, expected_gate["selected_for_blind_test"],
                         "persistence_24h", "four_constituents")):
            measured[name] = _mae(obs, test, _forecast(name, obs, train, test))
        chosen = expected_gate["selected_for_blind_test"]
        reports.append({
            "station": station, "day": day, "qwen_suggested": suggestion,
            "evidence_guard_chose": chosen, "model_suggestion_accepted": expected_gate["suggestion_accepted"],
            "test_hours": len(test), "fit_hours": len(train),
            "observations_sha256": raw_digest,
            "qwen_suggestion_mae_m": measured[suggestion],
            "evidence_guard_mae_m": measured[chosen],
            "previous_day_baseline_mae_m": measured["persistence_24h"],
            "four_term_reference_mae_m": measured["four_constituents"],
            "guard_beats_persistence": measured[chosen] < measured["persistence_24h"],
            "guard_beats_qwen_suggestion": measured[chosen] < measured[suggestion],
            "test_data_seen_by_proposer_or_guard": False,
        })
    return {
        "schema": "plenum-review-gated-evidence-audit-v1",
        "trials": len(reports), "results": reports,
        "qwen_suggestion_overridden": sum(not r["model_suggestion_accepted"] for r in reports),
        "guard_wins_against_persistence": sum(r["guard_beats_persistence"] for r in reports),
        "guard_wins_against_qwen_suggestion": sum(r["guard_beats_qwen_suggestion"] for r in reports),
        "policy_changed_using_these_test_outcomes": False,
        "new_scientific_discovery": False,
        "model_weights_updated": False,
        "generalizable_AI_improvement_demonstrated": False,
        "deployment_authorized": False,
        "scientific_status": "small observational benchmark of a human-designed validation gate",
    }
