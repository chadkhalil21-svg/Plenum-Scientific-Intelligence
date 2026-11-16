#!/usr/bin/env python3
"""Read-only validation of Battery Archive's public experimental-cell metadata.

This does NOT validate raw battery cycling measurements or battery performance.
Input is a locally supplied CSV; fetching and licensing remain caller responsibilities.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

FIELDS = ("cell_id", "study", "cathode", "anode", "temperature", "min_soc",
          "max_soc", "charge_crate", "discharge_crate", "capacity_ah", "form_factor")
NUMERIC = ("temperature", "min_soc", "max_soc", "charge_crate",
           "discharge_crate", "capacity_ah")


def validate(data: bytes) -> dict:
    if len(data) > 2_000_000:
        raise ValueError("metadata input exceeds 2 MB")
    source_sha256 = hashlib.sha256(data).hexdigest()
    rows = csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    if rows.fieldnames is None or len(rows.fieldnames) != len(set(rows.fieldnames)):
        raise ValueError("missing or duplicate CSV header")
    missing = sorted(set(FIELDS) - set(rows.fieldnames))
    if missing:
        raise ValueError("missing required fields: " + ",".join(missing))
    counts = {"rows": 0, "duplicate_cell_ids": 0, "missing_fields": 0,
              "nonfinite_or_non_numeric": 0, "invalid_soc_order": 0,
              "out_of_range_soc": 0, "nonpositive_rates_or_capacity": 0,
              "malformed_rows": 0}
    examples = []
    seen = set()
    for line, row in enumerate(rows, start=2):
        counts["rows"] += 1
        problems = []
        if None in row or any(k not in row for k in FIELDS):
            counts["malformed_rows"] += 1
            problems.append("malformed_row")
        if any(not (row.get(k) or "").strip() for k in FIELDS):
            counts["missing_fields"] += 1
            problems.append("missing_field")
        identifier = (row.get("cell_id") or "").strip()
        if identifier in seen:
            counts["duplicate_cell_ids"] += 1
            problems.append("duplicate_cell_id")
        seen.add(identifier)
        vals = {}
        for key in NUMERIC:
            try:
                val = float(row.get(key) or "")
                if not math.isfinite(val):
                    raise ValueError("nonfinite")
                vals[key] = val
            except (TypeError, ValueError):
                counts["nonfinite_or_non_numeric"] += 1
                problems.append("invalid_" + key)
        if "min_soc" in vals and "max_soc" in vals:
            if vals["min_soc"] >= vals["max_soc"]:
                counts["invalid_soc_order"] += 1
                problems.append("invalid_soc_order")
            if not (0 <= vals["min_soc"] <= 100 and 0 <= vals["max_soc"] <= 100):
                counts["out_of_range_soc"] += 1
                problems.append("out_of_range_soc")
        if any(key in vals and vals[key] <= 0
               for key in ("charge_crate", "discharge_crate", "capacity_ah")):
            counts["nonpositive_rates_or_capacity"] += 1
            problems.append("nonpositive_rates_or_capacity")
        if problems and len(examples) < 30:
            examples.append({"csv_line": line, "cell_id": identifier,
                             "findings": sorted(set(problems))})
    return {"scope": "battery_archive_cell_metadata_only",
            "input_sha256": source_sha256, "counts": counts,
            "first_30_flagged_rows": examples,
            "note": "No raw cycling voltage/current/capacity time series were tested."}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.input.read_bytes())
    text = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
