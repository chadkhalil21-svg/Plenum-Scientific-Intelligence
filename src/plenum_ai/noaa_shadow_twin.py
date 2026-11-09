"""NOAA observational *shadow-twin* replay, reusing validated measured-tide code.

Research-only historical sensor replay: a frozen harmonic environmental model
receives each held-out hourly gauge reading, updates a bounded residual state
and forecasts the NEXT hour before observing it. This is not a live, calibrated,
operational or safety-grade digital twin. No new simulator or model API.
"""
import argparse
import json
from datetime import datetime, timedelta
from math import isfinite
from pathlib import Path

from .noaa_empirical import STATIONS, fetch_data, score_station, _mae, _rmse

SCHEMA = "plenum-noaa-observation-shadow-twin-replay-v1"
GAIN = 0.25  # Fixed before observing evaluation errors; never optimized on holdout.
MIN_PAIRS = 18


def replay_station(station, rows, raw_sha256):
    """Prequential one-hour forecasts, each issued using only already-seen data."""
    result = score_station(station, rows, raw_sha256)
    snapshots = result["sample_forecasts"]
    if len(snapshots) < MIN_PAIRS + 1:
        raise ValueError("Insufficient observed NOAA hours for shadow-state replay")
    bias = 0.0
    previous = None
    predictions = []
    for record in snapshots:
        current_time = datetime.fromisoformat(record["time_utc"].replace("Z", "+00:00"))
        current_y = float(record["measured_m"])
        harmonic = float(record["harmonic_predicted_m"])
        if not all(isfinite(v) for v in (current_y, harmonic, bias)):
            raise ValueError("Nonfinite sensor value or model state")
        # The prediction of this hour uses ONLY the state updated after the
        # previous observed hour. No current target observation enters it.
        if previous is not None and current_time - previous["time"] == timedelta(hours=1):
            prediction = harmonic + bias
            predictions.append({
                "issued_at_utc": previous["time"].isoformat().replace("+00:00", "Z"),
                "target_at_utc": record["time_utc"],
                "observed_target_m": current_y,
                "shadow_predicted_m": float(prediction),
                "frozen_harmonic_predicted_m": harmonic,
                "one_hour_persistence_predicted_m": previous["observed"],
                "sensor_bias_state_before_target_m": float(bias),
            })
        # Only NOW may this reading update the model's online residual state.
        bias = (1.0 - GAIN) * bias + GAIN * (current_y - harmonic)
        previous = {"time": current_time, "observed": current_y}
    if len(predictions) < MIN_PAIRS:
        raise ValueError("NOAA consecutive hourly observation coverage insufficient")
    truth = [s["observed_target_m"] for s in predictions]
    modeled = [s["shadow_predicted_m"] for s in predictions]
    harmonic = [s["frozen_harmonic_predicted_m"] for s in predictions]
    persistence = [s["one_hour_persistence_predicted_m"] for s in predictions]
    metrics = {
        "shadow_mae_m": _mae(truth, modeled),
        "frozen_harmonic_mae_m": _mae(truth, harmonic),
        "one_hour_persistence_mae_m": _mae(truth, persistence),
        "shadow_rmse_m": _rmse(truth, modeled),
        "frozen_harmonic_rmse_m": _rmse(truth, harmonic),
        "one_hour_persistence_rmse_m": _rmse(truth, persistence),
    }
    if not all(isfinite(value) for value in metrics.values()):
        raise ValueError("Invalid shadow-twin metric")
    return {
        "station": station,
        "station_name": STATIONS[station],
        "source": "Actual NOAA CO-OPS hourly_height observations, not forecast products",
        "source_query": result["source_query"],
        "raw_payload_sha256": raw_sha256,
        "frozen_model": result["feature_set"],
        "fit_algorithm": result["fit_algorithm"],
        "training_end_exclusive_utc": result["fixed_training_end_exclusive_utc"],
        "historical_sensor_replay_day_utc": result["fixed_holdout_day_utc"],
        "train_observations": result["training_observations"],
        "frozen_state_update_gain": GAIN,
        "state_update_uses_only_observed_prior_hour": True,
        "evaluation_pairs": len(predictions),
        "evaluated_after_predictions_issued_in_order": True,
        "final_residual_bias_state_m": float(bias),
        **metrics,
        "beats_frozen_harmonic": metrics["shadow_mae_m"] < metrics["frozen_harmonic_mae_m"],
        "beats_one_hour_persistence": metrics["shadow_mae_m"] < metrics["one_hour_persistence_mae_m"],
        "sample_prequential_forecasts": predictions,
    }


def run_replay(opener=None):
    stations = []
    for station in STATIONS:
        rows, digest = fetch_data(station, **({"opener": opener} if opener is not None else {}))
        stations.append(replay_station(station, rows, digest))
    return {
        "schema": SCHEMA,
        "experiment": "NOAA observational shadow-twin, fixed June 2025 historical replay",
        "historical_replay_not_live_sensor_sync": True,
        "data_are_real_observations_if_fetched_from_noaa": True,
        "prequential_forecasts_not_future_data_fit": True,
        "existing_established_harmonic_engine_reused": True,
        "additional_simulation_engine_installed": False,
        "online_residual_updating": True,
        "uncertainty_quantified": False,
        "physically_calibrated_operational_digital_twin": False,
        "suitable_for_coastal_hazard_or_navigation_decisions": False,
        "AGI_or_autonomous_discovery_demonstrated": False,
        "stations": stations,
        "limitations": [
            "Historical replay on a previously studied June 2025 day is not prospective, live sensor synchronization.",
            "The original fixed harmonic model has already been evaluated on this day; this exploratory state update has not been precommitted on a NEW blind day.",
            "Frozen gain 0.25 was selected heuristically before this pilot, not scientifically calibrated.",
            "Stronger operational NOAA tide predictions, meteorological forcing, uncertainty intervals, and actual automatic fresh-data refresh are not included.",
            "A digital twin requires documented synchronization fidelity, sensor quality, calibration, out-of-sample validation and update management. This is a sensor-assimilating shadow-model prototype only.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    report = run_replay()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for site in report["stations"]:
        print(site["station_name"], "pairs", site["evaluation_pairs"],
              "shadow MAE", site["shadow_mae_m"],
              "harmonic MAE", site["frozen_harmonic_mae_m"],
              "1h persistence MAE", site["one_hour_persistence_mae_m"])
    print("Historical observation-assimilation replay, NOT operational digital twin.")


if __name__ == "__main__":
    main()
