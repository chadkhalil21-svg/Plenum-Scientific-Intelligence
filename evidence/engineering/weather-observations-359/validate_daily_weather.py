#!/usr/bin/env python3
"""Validate a bounded NOAA NCEI daily-summaries metric CSV (TMAX/TMIN/PRCP).

This is an offline intake check, not NOAA's own quality-control algorithm.
"""

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

FIELDS = ("TMAX", "TMIN", "PRCP")
UNITS = {"TMAX": "degC", "TMIN": "degC", "PRCP": "mm"}
REQUIRED = {"STATION", "DATE", *FIELDS, *(f"{f}_ATTRIBUTES" for f in FIELDS)}
# NCEI GHCN-Daily README, measurement / quality / source flag tables.
MFLAGS = set("ABCDEFGHIKLOPTW")
QFLAGS = set("DGIKLMNORSTWXZ")
SFLAGS = set("01267AabBCDdEFGHIKMfmNQRrSsTUuWXZz")
MAX_BYTES = 2_000_000
MAX_DAYS = 3660


def inspect(raw, station, start, end):
    """Return machine-readable structural and physical intake findings."""
    if not re.fullmatch(r"[A-Z0-9]{11}", station):
        raise ValueError("station must be an 11-character GHCN ID")
    span = (end - start).days + 1
    if not 1 <= span <= MAX_DAYS:
        raise ValueError(f"expected date interval must be 1..{MAX_DAYS} days")
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("input is empty or exceeds 2 MB")
    findings = []
    seen = set()
    stats = {
        field: {"numeric": 0, "missing": 0, "quality_flagged": 0,
                "measurement_flags": Counter(), "source_flags": Counter(),
                "observation_times": Counter()}
        for field in FIELDS
    }

    def note(level, code, row=None, field=None, detail=None):
        entry = {"severity": level, "code": code}
        if row is not None:
            entry["line"] = row
        if field is not None:
            entry["field"] = field
        if detail is not None:
            entry["detail"] = detail
        findings.append(entry)

    records = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    columns = records.fieldnames or []
    if len(columns) != len(set(columns)) or not REQUIRED.issubset(columns):
        raise ValueError(f"duplicate or missing required columns: {sorted(REQUIRED - set(columns))}")
    rows = 0
    for row in records:
        rows += 1
        if rows > MAX_DAYS:
            raise ValueError("row limit exceeded")
        line = records.line_num
        if None in row or any(row[name] is None for name in REQUIRED):
            note("ERROR", "malformed-row-width", line)
            continue
        day_text = row["DATE"]
        try:
            day = date.fromisoformat(day_text)
            if day.isoformat() != day_text:
                raise ValueError("expected YYYY-MM-DD")
        except ValueError:
            note("ERROR", "invalid-date", line, "DATE", day_text)
            day = None
        if row["STATION"] != station:
            note("ERROR", "unexpected-station", line, "STATION", row["STATION"])
        elif day is not None:
            if not start <= day <= end:
                note("ERROR", "date-outside-interval", line, "DATE", day_text)
            elif day in seen:
                note("ERROR", "duplicate-station-date", line, "DATE", day_text)
            else:
                seen.add(day)

        values = {}
        for field in FIELDS:
            value = row[field]
            attributes = row[field + "_ATTRIBUTES"]
            info = stats[field]
            # The API CSV uses blanks for absent values; -9999 is the native
            # GHCN sentinel. Neither may be counted as a measurement here.
            missing = value == "" or value in ("-9999", "-9999.0", "-999.9")
            if missing:
                info["missing"] += 1
                note("INCOMPLETE", "missing-value", line, field)
            else:
                try:
                    if not re.fullmatch(r"[+-]?[0-9]+(?:\.[0-9]+)?", value):
                        raise InvalidOperation
                    number = Decimal(value)
                    if not number.is_finite():
                        raise InvalidOperation
                except InvalidOperation:
                    note("ERROR", "nonfinite-or-invalid-number", line, field, value)
                else:
                    info["numeric"] += 1
                    values[field] = number
                    if field == "PRCP" and number < 0:
                        note("ERROR", "negative-precipitation", line, field, value)
                    if field in ("TMAX", "TMIN") and number < Decimal("-273.15"):
                        note("ERROR", "temperature-below-absolute-zero", line, field, value)

            if missing and attributes == "":
                continue
            parts = attributes.split(",")
            if len(parts) not in (3, 4):
                note("ERROR", "invalid-attributes", line, field, attributes)
                continue
            mflag, qflag, sflag = parts[:3]
            if mflag:
                info["measurement_flags"][mflag] += 1
                if mflag not in MFLAGS:
                    note("ERROR", "unknown-measurement-flag", line, field, mflag)
            if qflag:
                info["quality_flagged"] += 1
                note("ERROR", "noaa-quality-flag" if qflag in QFLAGS
                     else "unknown-quality-flag", line, field, qflag)
            if sflag:
                info["source_flags"][sflag] += 1
                if sflag not in SFLAGS:
                    note("ERROR", "unknown-source-flag", line, field, sflag)
            elif not missing:
                note("ERROR", "missing-source-flag", line, field)
            if len(parts) == 4 and parts[3]:
                when = parts[3]
                if when != "2400" and not re.fullmatch(r"(?:[01][0-9]|2[0-3])[0-5][0-9]", when):
                    note("ERROR", "invalid-observation-time", line, field, when)
                else:
                    info["observation_times"][when] += 1

        if "TMAX" in values and "TMIN" in values and values["TMIN"] > values["TMAX"]:
            note("ERROR", "minimum-exceeds-maximum", line, "TMIN/TMAX")

    missing_days = [(start + timedelta(days=i)).isoformat()
                    for i in range(span) if (start + timedelta(days=i)) not in seen]
    for day in missing_days:
        note("INCOMPLETE", "missing-date", field="DATE", detail=day)
    severity = Counter(f["severity"] for f in findings)
    return {
        "schema": "plenum-noaa-daily-intake-v1",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_bytes": len(raw),
        "station": station,
        "interval": [start.isoformat(), end.isoformat()],
        "units": UNITS,
        "expected_days": span,
        "rows": rows,
        "covered_unique_days": len(seen),
        "fields": stats,
        "findings": findings,
        "error_count": severity["ERROR"],
        "incomplete_count": severity["INCOMPLETE"],
        "status": "ERROR" if severity["ERROR"] else
                  "INCOMPLETE" if severity["INCOMPLETE"] else "PASSED_BOUNDED_INTAKE",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--station", required=True)
    parser.add_argument("--start", required=True, type=date.fromisoformat)
    parser.add_argument("--end", required=True, type=date.fromisoformat)
    parser.add_argument("--units", required=True, choices=("metric",))
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.csv.resolve() == args.out.resolve():
        parser.error("output must not overwrite input")
    try:
        with args.csv.open("rb") as source:
            raw = source.read(MAX_BYTES + 1)
        report = inspect(raw, args.station, args.start, args.end)
    except (ValueError, OSError, UnicodeError, csv.Error) as exc:
        parser.exit(2, f"Input could not be validated: {exc}\n")
    report["validator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    print(f"{report['status']}: {report['rows']} rows; "
          f"{report['error_count']} errors; {report['incomplete_count']} incomplete")
    return 0 if report["status"] == "PASSED_BOUNDED_INTAKE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
