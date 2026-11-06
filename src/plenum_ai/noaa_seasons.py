"""Predeclared multi-season NOAA holdout evaluation of the *same* tidal model.

Uses unchanged harmonic periods, least-squares fit, observation parsing and
previous-day persistence baseline. The original June 17 run was already
observed; the three additional holdout dates were chosen in advance of
their first evaluation. Never tune on these outcomes.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from math import isfinite
from statistics import mean
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import numpy as np

from .noaa_empirical import (
    API, STATIONS, MAX_DOWNLOAD, MIN_TRAIN, MIN_TEST,
    design, parse_observations, _mae, _rmse,
)

PREDECLARED_HOLDOUT_DAYS = (
    datetime(2025, 3, 17, tzinfo=timezone.utc),
    datetime(2025, 9, 17, tzinfo=timezone.utc),
    datetime(2025, 12, 17, tzinfo=timezone.utc),
)


def range_query(station, cutoff):
    if station not in STATIONS or cutoff not in PREDECLARED_HOLDOUT_DAYS:
        raise ValueError("Only predeclared station/date pairs allowed")
    first = cutoff - timedelta(days=16)
    return API + "?" + urlencode({
        "begin_date": first.strftime("%Y%m%d"),
        "end_date": cutoff.strftime("%Y%m%d"),
        "station": station, "product": "hourly_height", "datum": "MLLW",
        "time_zone": "gmt", "units": "metric", "format": "json",
        "application": "plenum_scientific_intelligence_independent_seasonal_test",
    })


def fetch_range(station, cutoff, opener=urlopen):
    request = Request(range_query(station, cutoff), headers={
        "User-Agent": "PlenumScientificIntelligence/0.9 measured coastal validation",
        "Accept": "application/json",
    })
    with opener(request, timeout=25) as stream:
        data = stream.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError("NOAA response too large")
    payload = json.loads(data)
    if payload.get("error") or not isinstance(payload.get("data"), list):
        raise ValueError("NOAA unavailable or invalid data; never invent observations")
    return payload["data"], sha256(data).hexdigest()


def evaluate_predeclared_window(station, cutoff, rows, digest):
    if station not in STATIONS or cutoff not in PREDECLARED_HOLDOUT_DAYS:
        raise ValueError("Unreviewed station/date pair")
    observed = parse_observations(rows)
    start = cutoff - timedelta(days=16)
    finish = cutoff + timedelta(days=1)
    train = sorted(t for t in observed if start <= t < cutoff)
    test = sorted(t for t in observed if cutoff <= t < finish
                  and t - timedelta(days=1) in observed)
    if len(train) < MIN_TRAIN or len(test) < MIN_TEST:
        raise ValueError("Insufficient verified NOAA observations")
    xtrain = design(train)
    ytrain = np.asarray([observed[t] for t in train], dtype=np.float64)
    coefficients, _resid, rank, _sing = np.linalg.lstsq(xtrain, ytrain, rcond=None)
    if rank < 9 or not np.all(np.isfinite(coefficients)):
        raise ValueError("Nonidentifiable harmonic fit")
    forecasts = list(map(float, design(test) @ coefficients))
    observed_future = [observed[t] for t in test]
    baseline = [observed[t - timedelta(days=1)] for t in test]
    harmonic_mae, baseline_mae = (_mae(observed_future, x) for x in
                                  (forecasts, baseline))
    if not all(isfinite(x) for x in (harmonic_mae, baseline_mae)):
        raise ValueError("Nonfinite forecast error")
    return {
        "station": station,
        "name": STATIONS[station],
        "holdout_utc": cutoff.strftime("%Y-%m-%d"),
        "train_start_utc": start.strftime("%Y-%m-%d"),
        "forecast_horizon_hours": 24,
        "train_observations": len(train),
        "test_observations": len(test),
        "raw_noaa_sha256": digest,
        "noaa_source_url": range_query(station, cutoff),
        "observed_not_noaa_predictions": True,
        "baseline_only_uses_pre_holdout_data": True,
        "algorithm_changed_since_june_17": False,
        "harmonic_mae_m": harmonic_mae,
        "persistence_mae_m": baseline_mae,
        "harmonic_rmse_m": _rmse(observed_future, forecasts),
        "persistence_rmse_m": _rmse(observed_future, baseline),
        "harmonic_better": harmonic_mae < baseline_mae,
        "test_actuals_used_for_fitting": False,
    }


def run_seasonal_validation(opener=urlopen):
    reports = []
    # Every precommitted station and date is included, with no cherry-picking.
    for date in PREDECLARED_HOLDOUT_DAYS:
        for station in STATIONS:
            rows, digest = fetch_range(station, date, opener=opener)
            reports.append(evaluate_predeclared_window(station, date, rows, digest))
    total = sum(r["test_observations"] for r in reports)
    avg_model = sum(r["harmonic_mae_m"] * r["test_observations"] for r in reports) / total
    avg_naive = sum(r["persistence_mae_m"] * r["test_observations"] for r in reports) / total
    wins = sum(r["harmonic_better"] for r in reports)
    return {
        "experiment": "Plenum measured NOAA holdout seasonal generalization v0.9b",
        "hypothesis": "The fixed four-period harmonic tide forecast beats 24h persistence on the average of all six precommitted season-station holdouts.",
        "predeclared_test_days": [x.strftime("%Y-%m-%d") for x in PREDECLARED_HOLDOUT_DAYS],
        "number_of_station_day_tests": len(reports),
        "number_of_independent_heldout_hourly_readings": total,
        "model_method_same_as_initial_june_17": True,
        "comparison": "identical 24h measured targets, no held-out fitting",
        "station_day_results": reports,
        "weighted_harmonic_mae_m": avg_model,
        "weighted_persistence_mae_m": avg_naive,
        "wins": wins,
        "hypothesis_supported": avg_model < avg_naive,
        "all_station_days_win": wins == len(reports),
        "AI_devised_the_hypothesis": False,
        "operational_forecasting_approved": False,
        "scientific_discovery_verified": False,
        "caveats": [
            "The 2025 periods and stations are limited and not independent geographic samples.",
            "Three season-days (plus the earlier June day) are insufficient for broad tide-model validation.",
            "Atmospheric pressure, storm surges and boundary forcing may cause forecasting errors.",
            "No post-hoc tuning, exclusion of failures or model promotion is permitted.",
            "This is an out-of-time observational test of an established physical model, not AGI.",
        ],
    }
