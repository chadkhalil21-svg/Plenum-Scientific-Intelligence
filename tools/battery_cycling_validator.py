#!/usr/bin/env python3
"""Read-only validation of the published ROVI p492-13 cycling sample, not a life prediction.

Adapt the existing metadata validator's bounded JSON/CSV approach to the upstream
battdat BatteryData.Energy.Gov format. Source: https://github.com/ROVI-org/battery-data-toolkit
at 19961e6bbb2d0cfe0bff9c129144fcf8f3dd3be6; upstream BDReader converts Frequency_Hz
non-null rows separately to EIS. No raw data redistribution or performance claim.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

FIELDS = ("Cycle_Index", "Time_s", "Current_A", "Voltage_V",
          "Charge_Capacity_Ah", "Discharge_Capacity_Ah", "Frequency_Hz")


def validate(data: bytes) -> dict:
    if not data or len(data) > 2_000_000:
        raise ValueError("empty input or input exceeds 2 MB")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
    if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("missing or duplicate CSV header")
    if not set(FIELDS) <= set(reader.fieldnames):
        raise ValueError("missing original upstream measurement fields")
    counts = dict(rows=0, cycling_rows=0, eis_rows=0, malformed_rows=0,
                  missing_or_nonfinite_rows=0, invalid_cycle_or_time=0,
                  backwards_time=0, equal_timestamps=0, nonpositive_cycling_voltage=0,
                  negative_capacity_rows=0, invalid_eis_frequency=0,
                  charge_current_rows=0, discharge_current_rows=0)
    cycles = {}
    prior = None
    voltage_min = None
    voltage_max = None
    for row in reader:
        counts["rows"] += 1
        if None in row or any(row.get(k) is None for k in FIELDS):
            counts["malformed_rows"] += 1
            continue
        try:
            cycle, elapsed, current, voltage, charge, discharge = (
                float(row[k]) for k in FIELDS[:-1])
            if not all(map(math.isfinite, (cycle, elapsed, current, voltage, charge, discharge))):
                raise ValueError("nonfinite")
        except (TypeError, ValueError):
            counts["missing_or_nonfinite_rows"] += 1
            continue
        if cycle < 1 or not cycle.is_integer() or elapsed < 0:
            counts["invalid_cycle_or_time"] += 1
            continue
        if prior is not None:
            counts["backwards_time"] += elapsed < prior
            counts["equal_timestamps"] += elapsed == prior
        prior = elapsed
        # The source's documented BDReader treats non-null Frequency_Hz as EIS.
        # Negative EIS voltage is NOT terminal-voltage cycling data.
        frequency = row["Frequency_Hz"].strip()
        if frequency != "" and frequency.lower() != "nan":
            counts["eis_rows"] += 1
            try:
                f = float(frequency)
                if not math.isfinite(f) or f <= 0:
                    raise ValueError("invalid frequency")
            except ValueError:
                counts["invalid_eis_frequency"] += 1
            continue
        counts["cycling_rows"] += 1
        counts["nonpositive_cycling_voltage"] += voltage <= 0
        counts["negative_capacity_rows"] += charge < 0 or discharge < 0
        counts["charge_current_rows"] += current > 0
        counts["discharge_current_rows"] += current < 0
        voltage_min = voltage if voltage_min is None else min(voltage_min, voltage)
        voltage_max = voltage if voltage_max is None else max(voltage_max, voltage)
        result = cycles.setdefault(str(int(cycle)), dict(rows=0, charge_current_rows=0,
                      discharge_current_rows=0, max_charge_capacity_ah=0.0,
                      max_discharge_capacity_ah=0.0))
        result["rows"] += 1
        result["charge_current_rows"] += current > 0
        result["discharge_current_rows"] += current < 0
        result["max_charge_capacity_ah"] = max(result["max_charge_capacity_ah"], charge)
        result["max_discharge_capacity_ah"] = max(result["max_discharge_capacity_ah"], discharge)

    fatal = ("malformed_rows", "missing_or_nonfinite_rows", "invalid_cycle_or_time",
             "backwards_time", "nonpositive_cycling_voltage", "negative_capacity_rows",
             "invalid_eis_frequency")
    # Genuine measured charge AND discharge with positive measured capacity in a
    # common cycle, not merely a metadata record or voltage-only example.
    has_paired_cycle = any(c["charge_current_rows"] and c["discharge_current_rows"]
                           and c["max_charge_capacity_ah"] > 0 and c["max_discharge_capacity_ah"] > 0
                           for c in cycles.values())
    passed = (not any(counts[k] for k in fatal) and len(cycles) >= 2 and has_paired_cycle
              and counts["cycling_rows"] + counts["eis_rows"] == counts["rows"])
    return dict(scope="published_rovi_p492-13_sample_measurements_only",
                input_sha256=hashlib.sha256(data).hexdigest(), counts=counts,
                cycling_cycles=len(cycles), cycles=cycles,
                cycling_voltage_range_v=[voltage_min, voltage_max], passed=passed,
                note="EIS isolated using documented frequency field; equal timestamps reported, not silently removed. This is structural validation of one public sample, not full-study or performance validation.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    with args.input.open("rb") as stream:
        report = validate(stream.read(2_000_001))
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
