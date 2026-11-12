"""Offline validation of NOAA CO-OPS-style water-level station metadata.

Accepts JSON station records or NOAA station collections. This checks the
structure of supplied metadata; it does not certify station status, instrument
accuracy, datum correctness, or NOAA compliance.

NOAA official field definitions:
https://api.tidesandcurrents.noaa.gov/mdapi/dev/
No network calls, credentials, external packages, or writes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

STATION_ID = re.compile(r"[A-Za-z0-9]{2,20}\Z")
MAX_STATIONS = 5000
MAX_BYTES = 2_000_000
MAX_REPORTED_ERRORS = 100


def station_records(document: object) -> list:
    """Read standalone, list, or NOAA-style collection input."""
    if isinstance(document, list):
        items = document
    elif isinstance(document, dict):
        if "stations" in document:
            items = document["stations"]
        elif "stationList" in document:
            items = document["stationList"]
        elif "station" in document:
            items = [document["station"]]
        elif "id" in document:
            items = [document]
        else:
            raise ValueError("Expected station, stations, stationList, or records list")
    else:
        raise ValueError("Expected a JSON object or array")
    if not isinstance(items, list):
        raise ValueError("Station collection must be a JSON list")
    if len(items) > MAX_STATIONS:
        raise ValueError("Station collection exceeds bounded size")
    return items


def valid_coordinate(value: object, minimum: float, maximum: float) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value)) and minimum <= value <= maximum
    except (OverflowError, ValueError, TypeError):
        return False


def validate_station_metadata(document: object) -> dict:
    """Return bounded public structural findings without echoing input rows."""
    records = station_records(document)
    errors: list[dict] = []
    bad_rows: set[int] = set()
    identifiers: set[str] = set()

    def flag(index: int, code: str) -> None:
        bad_rows.add(index)
        if len(errors) < MAX_REPORTED_ERRORS:
            errors.append({"row": index, "code": code})

    for i, row in enumerate(records):
        if not isinstance(row, dict):
            flag(i, "station_not_object")
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not STATION_ID.fullmatch(identifier):
            flag(i, "invalid_station_id")
        elif identifier in identifiers:
            flag(i, "duplicate_station_id")
        else:
            identifiers.add(identifier)
        name = row.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 200:
            flag(i, "invalid_station_name")
        if not valid_coordinate(row.get("lat"), -90, 90):
            flag(i, "invalid_latitude")
        if not valid_coordinate(row.get("lng"), -180, 180):
            flag(i, "invalid_longitude")
        for field in ("tidal", "greatlakes"):
            if field in row and not isinstance(row[field], bool):
                flag(i, "invalid_" + field + "_flag")

    return {
        "schema": "plenum-noaa-station-metadata-structure-v1",
        "total_rows": len(records),
        "structurally_valid_rows": len(records) - len(bad_rows),
        "invalid_rows": len(bad_rows),
        "errors": errors,
        "errors_truncated": len(bad_rows) > 0 and len(errors) == MAX_REPORTED_ERRORS,
        "independent_station_identity_verified": False,
        "datum_reference_validated": False,
        "instrument_accuracy_verified": False,
        "no_network_or_account_access": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline NOAA-style station metadata structure review")
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_file.stat().st_size > MAX_BYTES:
            raise ValueError("Input file exceeds bounded size")
        document = json.loads(args.json_file.read_text(encoding="utf-8"))
        result = validate_station_metadata(document)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "INVALID_INPUT", "reason_type": type(exc).__name__}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["invalid_rows"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
