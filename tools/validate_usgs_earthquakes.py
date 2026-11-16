#!/usr/bin/env python3
"""Validate two USGS ComCat export formats and render their agreed observations."""
import argparse
import csv
import hashlib
import io
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from jsonschema import Draft7Validator

SCHEMA_SHA256 = "83e781f1513e447be9287b2180c300621f8b4c65245d7822a22fcf39431e0471"
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON member {key}")
        result[key] = value
    return result


def bad_constant(value):
    raise ValueError(f"Invalid JSON numeric constant: {value}")


def strict_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=bad_constant)


def numeric(value):
    require(not isinstance(value, bool), "Boolean is not a numeric observation")
    result = Decimal(str(value))
    require(result.is_finite(), "Non-finite numeric value")
    return result


def instant(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0),
            "Timestamp must be explicitly UTC")
    return stamp


def milliseconds(stamp):
    delta = stamp - EPOCH
    require(delta.microseconds % 1000 == 0, "Expected millisecond precision")
    return delta // timedelta(milliseconds=1)


def observation(event_id, time_ms, lon, lat, depth, mag, mag_type, event_type, status):
    require(isinstance(event_id, str) and bool(event_id), "Missing event ID")
    require(type(time_ms) is int, f"{event_id}: invalid millisecond timestamp")
    lon, lat, depth, mag = map(numeric, (lon, lat, depth, mag))
    require(-180 <= lon <= 180 and -90 <= lat <= 90,
            f"{event_id}: invalid longitude/latitude")
    require(all(isinstance(v, str) and v for v in (mag_type, event_type, status)),
            f"{event_id}: missing magnitude type/event type/status")
    return (time_ms, lon, lat, depth, mag, mag_type, event_type, status)


def geo_observations(raw, schema_raw):
    require(sha256(schema_raw) == SCHEMA_SHA256, "Unapproved schema version/digest")
    schema = strict_json(schema_raw)
    data = strict_json(raw)
    Draft7Validator.check_schema(schema)
    Draft7Validator(schema).validate(data)
    require(data["metadata"]["status"] == 200, "USGS response status not 200")
    require(data["metadata"]["count"] == len(data["features"]), "Metadata count mismatch")
    result = {}
    for f in data["features"]:
        event_id = f["id"]
        require(event_id not in result, f"Duplicate GeoJSON ID {event_id}")
        g, p = f["geometry"], f["properties"]
        require(g["type"] == "Point" and len(g["coordinates"]) == 3,
                f"{event_id}: expected USGS longitude, latitude, depth")
        require(type(p["mag"]) in (int, float), f"{event_id}: expected numerical magnitude")
        result[event_id] = observation(
            event_id, p["time"], *g["coordinates"],
            p["mag"], p["magType"], p["type"], p["status"])
    return result, data["metadata"]


def csv_observations(raw):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    needed = {"id", "time", "longitude", "latitude", "depth", "mag", "magType", "type", "status"}
    require(reader.fieldnames is not None and needed <= set(reader.fieldnames),
            "Required CSV headers absent")
    require(len(reader.fieldnames) == len(set(reader.fieldnames)), "Duplicate CSV headers")
    result = {}
    for row in reader:
        require(None not in row and all(x is not None for x in row.values()), "Malformed CSV row")
        event_id = row["id"]
        require(event_id not in result, f"Duplicate CSV ID {event_id}")
        result[event_id] = observation(
            event_id, milliseconds(instant(row["time"])), row["longitude"],
            row["latitude"], row["depth"], row["mag"], row["magType"], row["type"], row["status"])
    return result


def semantic_hash(records):
    # Decimal's normalization makes 5 and 5.0 semantically equal.
    canonical = [[key, *[format(v.normalize(), "f") if isinstance(v, Decimal) else v
                         for v in records[key]]] for key in sorted(records)]
    return sha256(json.dumps(canonical, separators=(",", ":"), ensure_ascii=True).encode())


def plot(records, start, end, min_mag, output):
    ordered = sorted(records.items(), key=lambda kv: kv[1][0])
    times = [EPOCH + timedelta(milliseconds=r[0]) for _, r in ordered]
    depths = [float(r[3]) for _, r in ordered]
    mags = [float(r[4]) for _, r in ordered]
    peak = max(range(len(mags)), key=mags.__getitem__)
    plt.rcParams.update({"svg.hashsalt": "plenum-usgs-mission-378", "svg.fonttype": "none",
                         "font.family": "DejaVu Sans", "axes.spines.top": False,
                         "axes.spines.right": False, "axes.labelcolor": "#26384a",
                         "xtick.color": "#425467", "ytick.color": "#425467"})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.3), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1.1]})
    fig.patch.set_facecolor("#ffffff")
    fig.suptitle("Cataloged earthquakes | Magnitude & depth", x=.11, y=.975,
                 ha="left", fontsize=19, weight="bold", color="#17324d")
    fig.text(.11, .895, f"USGS ComCat · {start:%d %b}–{end:%d %b %Y} UTC"
             f" · M ≥ {min_mag} · {len(records)} matched events",
             fontsize=11, color="#425467")
    colors = ["#bd572d" if m >= 6 else "#247c93" for m in mags]
    for ax, y, title in ((ax1, mags, "Preferred magnitude"), (ax2, depths, "Depth (km)")):
        ax.scatter(times, y, c=colors, s=36, edgecolors="white", linewidths=.6, zorder=3)
        ax.set_ylabel(title, fontsize=10)
        ax.grid(axis="y", color="#dde4eb", linewidth=.75)
        ax.set_axisbelow(True)
        ax.margins(y=.15)
    ax1.annotate(f"M {mags[peak]:g} · {ordered[peak][0]}", (times[peak], mags[peak]),
                 xytext=(10, -12), textcoords="offset points", fontsize=9,
                 color="#9b4123", weight="bold")
    ax2.invert_yaxis()
    ax2.set_xlim(start, end)
    ax2.xaxis.set_major_locator(mdates.DayLocator(tz=timezone.utc))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b", tz=timezone.utc))
    fig.text(.11, .055, "Each dot is one event; overlapping dots are possible. Orange: M ≥ 6.",
             fontsize=9, color="#425467")
    fig.text(.11, .032, "Credit: U.S. Geological Survey, ANSS Comprehensive Earthquake Catalog. "
             "Catalog consistency, not a seismic-hazard or prediction model.",
             fontsize=8, color="#425467")
    fig.subplots_adjust(left=.11, right=.96, top=.83, bottom=.125, hspace=.22)
    fig.savefig(output, format="svg", metadata={"Date": None, "Creator": "Plenum Engineering"})
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--geojson", type=Path, required=True)
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--schema", type=Path, required=True)
    p.add_argument("--start", required=True, help="inclusive UTC instant")
    p.add_argument("--end", required=True, help="inclusive UTC instant")
    p.add_argument("--min-magnitude", type=Decimal, required=True)
    p.add_argument("--svg", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    raw_geo, raw_csv, raw_schema = (path.read_bytes() for path in (args.geojson, args.csv, args.schema))
    geo, metadata = geo_observations(raw_geo, raw_schema)
    tabular = csv_observations(raw_csv)
    require(geo and geo.keys() == tabular.keys(), "Empty data or differing event ID sets")
    mismatches = sorted(key for key in geo if geo[key] != tabular[key])
    require(not mismatches, f"GeoJSON/CSV field disagreements: {mismatches}")
    start, end = instant(args.start), instant(args.end)
    start_ms, end_ms = milliseconds(start), milliseconds(end)
    require(start < end and args.min_magnitude.is_finite(), "Invalid selection bounds")
    for key, record in geo.items():
        require(start_ms <= record[0] <= end_ms, f"{key}: outside requested time window")
        require(record[4] >= args.min_magnitude and record[6] == "earthquake",
                f"{key}: outside requested magnitude/type")
    plot(geo, start, end, args.min_magnitude, args.svg)
    peak_id = max(sorted(geo), key=lambda key: geo[key][4])
    report = {
        "status": "VALIDATED_CATALOG_CONSISTENCY",
        "source_url": metadata["url"],
        "source_generated_epoch_ms": metadata["generated"],
        "source_api_version": metadata["api"],
        "selection": {"start_utc": start.isoformat(), "end_utc": end.isoformat(),
                      "min_magnitude": str(args.min_magnitude), "event_type": "earthquake"},
        "libraries": {"jsonschema": version("jsonschema"), "matplotlib": version("matplotlib")},
        "sha256": {"geojson": sha256(raw_geo), "csv": sha256(raw_csv),
                   "schema": sha256(raw_schema), "svg": sha256(args.svg.read_bytes()),
                   "geojson_semantic": semantic_hash(geo), "csv_semantic": semantic_hash(tabular)},
        "checks": {"upstream_geojson_schema": "pass", "unique_id_sets_match": True,
                   "record_fields_compared": ["time", "longitude", "latitude", "depth", "mag",
                                              "magType", "type", "status"],
                   "semantic_field_mismatches": len(mismatches), "query_constraints": "pass"},
        "events": len(geo),
        "reviewed_events": sum(r[7] == "reviewed" for r in geo.values()),
        "magnitude_range": [float(min(r[4] for r in geo.values())), float(max(r[4] for r in geo.values()))],
        "depth_km_range": [float(min(r[3] for r in geo.values())), float(max(r[3] for r in geo.values()))],
        "peak_magnitude_event_id": peak_id,
        "limitations": "Two representations of one mutable catalog, not independent physical measurements. "
                       "Byte digests identify these retrieved inputs; later catalog revisions may differ."
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
