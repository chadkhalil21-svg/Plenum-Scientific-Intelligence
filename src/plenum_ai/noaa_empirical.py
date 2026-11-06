"""NOAA measured sea-level forecast benchmark with a precommitted blind final day.

Data are *observed hourly water levels*, not NOAA's prediction product.
A fixed four-constituent harmonic model is fit only on earlier measurements,
then scored on a chronologically held-out 24-hour day versus a 24-hour
persistence forecast. No auto-tuning or repeated selection on test labels.
"""
from datetime import datetime, timezone
from hashlib import sha256
from math import cos, sin, pi, sqrt, isfinite
from pathlib import Path
from statistics import mean
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import numpy as np

API = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
STATIONS = {"8443970": "Boston, MA", "8723214": "Virginia Key, FL"}
BEGIN, END = "20250601", "20250617"
CUTOFF = datetime(2025, 6, 17, tzinfo=timezone.utc)
START = datetime(2025, 6, 1, tzinfo=timezone.utc)
HARMONIC_PERIODS_HOURS = (12.4206, 12.0, 23.9345, 25.8193)
MAX_DOWNLOAD = 240000
MIN_TRAIN = 280
MIN_TEST = 18


def data_url(station):
    if station not in STATIONS:
        raise ValueError("Only reviewed NOAA station IDs are permitted")
    return API + "?" + urlencode({
        "begin_date": BEGIN, "end_date": END, "station": station,
        "product": "hourly_height", "datum": "MLLW", "time_zone": "gmt",
        "units": "metric", "format": "json",
        "application": "plenum_scientific_intelligence_public_research",
    })


def fetch_data(station, opener=urlopen):
    request = Request(data_url(station), headers={
        "User-Agent": "PlenumScientificIntelligence/0.9 NOAA public observation evaluation",
        "Accept": "application/json",
    })
    with opener(request, timeout=22) as stream:
        raw = stream.read(MAX_DOWNLOAD + 1)
    if len(raw) > MAX_DOWNLOAD:
        raise ValueError("NOAA response exceeds maximum bytes")
    payload = json.loads(raw)
    if payload.get("error"):
        raise ValueError("NOAA returned an error; no observations invented")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("Unexpected NOAA response schema")
    return rows, sha256(raw).hexdigest()


def parse_observations(rows):
    """Strict observed, timestamped hourly readings, no prediction products."""
    found = {}
    for item in rows:
        try:
            dt = datetime.strptime(item["t"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            water = float(item["v"])
            if not (isfinite(water) and -5 < water < 15 and dt.minute == 0):
                continue
            if dt in found:
                raise ValueError("Duplicate NOAA hourly timestamp")
            found[dt] = water
        except (KeyError, TypeError, ValueError) as e:
            if str(e) == "Duplicate NOAA hourly timestamp":
                raise
            continue
    return found


def _hours(dt):
    return (dt - START).total_seconds() / 3600


def design(timestamps):
    cols = []
    for time in timestamps:
        h = _hours(time)
        row = [1.0]
        for period in HARMONIC_PERIODS_HOURS:
            row.extend((sin(2*pi*h/period), cos(2*pi*h/period)))
        cols.append(row)
    return np.asarray(cols, dtype=np.float64)


def _mae(true, pred):
    return float(mean(abs(float(a)-float(b)) for a,b in zip(true,pred)))


def _rmse(true, pred):
    return float(sqrt(mean((float(a)-float(b))**2 for a,b in zip(true,pred))))


def score_station(station, rows, raw_sha256):
    if station not in STATIONS:
        raise ValueError("Unknown station")
    obs = parse_observations(rows)
    if not obs:
        raise ValueError("No valid measured water levels")
    training = sorted(t for t in obs if START <= t < CUTOFF)
    # Fixed final day. Never select favorable dates based on measured test error.
    test = sorted(t for t in obs if CUTOFF <= t < CUTOFF.replace(day=18))
    # The persistence comparison is a forecast issued at cutoff, using only
    # measurements from the preceding 24 hours. It never uses holdout values.
    shared_test = [t for t in test if (t.replace(day=16)) in obs]
    if len(training) < MIN_TRAIN or len(shared_test) < MIN_TEST:
        raise ValueError("NOAA training/holdout coverage insufficient")
    xtrain, ytrain = design(training), np.asarray([obs[t] for t in training])
    xhold = design(shared_test)
    coeff, residuals, rank, singular = np.linalg.lstsq(xtrain, ytrain, rcond=None)
    if rank < len(coeff) or not np.all(np.isfinite(coeff)):
        raise ValueError("Harmonic fit rank deficient or nonfinite")
    measured = [obs[t] for t in shared_test]
    predicted = list(map(float, xhold @ coeff))
    naive = [obs[t.replace(day=16)] for t in shared_test]
    model_mae = _mae(measured, predicted)
    naive_mae = _mae(measured, naive)
    if not all(isfinite(v) for v in (model_mae, naive_mae)):
        raise ValueError("Nonfinite forecast error")
    train_times = set(training)
    test_times = set(shared_test)
    if train_times & test_times:
        raise AssertionError("Temporal leakage")
    return {
        "station": station, "station_name": STATIONS[station],
        "source": "NOAA CO-OPS observed verified hourly water level",
        "source_query": data_url(station),
        "raw_payload_sha256": raw_sha256,
        "fixed_training_start_utc": "2025-06-01T00:00:00Z",
        "fixed_training_end_exclusive_utc": "2025-06-17T00:00:00Z",
        "fixed_holdout_day_utc": "2025-06-17",
        "training_observations": len(training),
        "holdout_observations": len(shared_test),
        "selected_after_examining_holdout": False,
        "feature_set": "Intercept and fixed 12.4206, 12.0, 23.9345, 25.8193 h sin/cos constituents",
        "fit_algorithm": "numpy.linalg.lstsq; train-only harmonic coefficients",
        "baseline": "same-hour reading exactly 24 hours earlier, entirely in training data",
        "model_mae_m": model_mae,
        "baseline_mae_m": naive_mae,
        "model_rmse_m": _rmse(measured, predicted),
        "baseline_rmse_m": _rmse(measured, naive),
        "model_beats_baseline": bool(model_mae < naive_mae),
        "observations_from_independent_measured_future_day": True,
        "scientific_discovery_verified": False,
        "validated_operational_tide_forecast": False,
        "sample_forecasts": [
            {"time_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
             "measured_m": obs[t], "harmonic_predicted_m": pred,
             "prior_day_baseline_m": base}
            for t, pred, base in zip(shared_test, predicted, naive)
        ],
    }


def run_empirical_forecast(opener=urlopen):
    reports = []
    for station in STATIONS:
        rows, raw_digest = fetch_data(station, opener=opener)
        reports.append(score_station(station, rows, raw_digest))
    passed = all(row["model_beats_baseline"] for row in reports)
    return {
        "experiment": "Plenum v0.9 precommitted NOAA observed water-level forecast",
        "hypothesis": "A fixed four-constituent harmonic model, fitted only on June 1-16 2025 observed hourly water levels, beats 24-hour persistence on June 17 for Boston and Virginia Key.",
        "precommitted_before_first_test_run": True,
        "model_and_baseline_fixed_before_holdout": True,
        "stations": reports,
        "hypothesis_supported_at_both_stations": passed,
        "hypothesis_refuted_or_inconclusive_if_false": not passed,
        "is_independent_future_observation_holdout": True,
        "model_parameters_fit_on_test_data": False,
        "new_scientific_discovery_verified": False,
        "AI_self_improvement_proven": False,
        "limitations": [
            "The observed NOAA hourly heights are empirical data, not the NOAA prediction product.",
            "This is a retrospective one-day out-of-time test, not live deployed forecasting.",
            "Constituent periods come from established physical science, not discovered by AI.",
            "Weather surge, changing river discharge and harmonic constituents omitted from the model can dominate errors.",
            "One test day at two stations is far too small to establish robust forecasting skill; test across seasons and independent regions before operational use.",
            "If the harmonic model fails to improve, retain the failure without adapting the hypothesis to this test day.",
        ],
    }
