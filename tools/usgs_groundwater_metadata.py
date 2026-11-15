"""Validate a bounded USGS monitoring-location catalogue, never water observations."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
from html import escape
import json
import re
from pathlib import Path

from jsonschema import Draft201909Validator
from water_level_metadata import valid_coordinate

BASE = "https://api.waterdata.usgs.gov/ogcapi/v1/collections/monitoring-locations"
SOURCE = BASE + "/items?agency_code=USGS&state_code=12&county_code=086&site_type_code=GW&bbox=-80.4,25.65,-80.3,25.75&limit=500&f=json"
SCHEMA = BASE + "/schema?f=json"
BOUNDS = (-80.4, 25.65, -80.3, 25.75)
FILTERS = {"agency_code": "USGS", "state_code": "12", "county_code": "086", "site_type_code": "GW", "site_type": "Well"}
CORE = {"id", "monitoring_location_number", *FILTERS}
FIELDS = ("construction_date", "well_constructed_depth", "hole_constructed_depth", "aquifer_code", "national_aquifer_code", "aquifer_type_code", "altitude", "vertical_datum")


def read_bounded(path):
    if path.stat().st_size > 2_000_000:
        raise ValueError("Input exceeds 2 MB bound")
    raw = path.read_bytes()
    return raw, json.loads(raw)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate(raw, document, schema_raw, schema):
    if schema.get("$id") != BASE + "/schema":
        raise ValueError("Unexpected official schema identity")
    definition = schema["properties"]
    if not CORE.union(FIELDS, {"original_horizontal_datum", "geometry"}).issubset(definition):
        raise ValueError("Missing source schema fields")
    # The official catalogue describes non-null field types but actually exposes nulls.
    # Adapt only optional property nullability; keep the original schema hash in the receipt.
    properties = {key: dict(value) for key, value in definition.items() if key != "geometry"}
    for key, value in properties.items():
        if key not in CORE and isinstance(value.get("type"), str):
            value["type"] = [value["type"], "null"]
    adapted = {"type": "object", "properties": properties, "required": sorted(CORE)}
    Draft201909Validator.check_schema(adapted)
    checker = Draft201909Validator(adapted)
    features = document.get("features")
    if (document.get("type") != "FeatureCollection" or not isinstance(features, list)
            or not 0 < len(features) <= 500 or document.get("numberReturned") != len(features)
            or not isinstance(document.get("links"), list)
            or any(link.get("rel") == "next" for link in document["links"])):
        raise ValueError("Incomplete, empty or oversized collection")
    errors, findings, missing, omitted = Counter(), Counter(), Counter(), Counter()
    source_datum, vertical_datum = Counter(), Counter()
    ids, years = set(), []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature" or not isinstance(feature.get("properties"), dict):
            errors["feature_shape"] += 1
            continue
        p = feature["properties"]
        for error in checker.iter_errors(p):
            errors["schema_property_" + (str(error.path[0]) if error.path else str(error.validator))] += 1
        identifier, number = p.get("id"), p.get("monitoring_location_number")
        if not isinstance(number, str) or not re.fullmatch(r"[0-9]{8,15}", number) or identifier != "USGS-" + number or identifier != feature.get("id"):
            errors["location_identity"] += 1
        elif identifier in ids:
            errors["duplicate_location"] += 1
        else:
            ids.add(identifier)
        for key, expected in FILTERS.items():
            if p.get(key) != expected:
                errors["query_scope_" + key] += 1
        geometry = feature.get("geometry")
        coords = geometry.get("coordinates") if isinstance(geometry, dict) and geometry.get("type") == "Point" else None
        if not isinstance(coords, list) or len(coords) != 2 or not valid_coordinate(coords[0], BOUNDS[0], BOUNDS[2]) or not valid_coordinate(coords[1], BOUNDS[1], BOUNDS[3]):
            errors["point_outside_bbox_or_invalid"] += 1
        for key in properties:
            if key not in p:
                omitted[key] += 1
            if p.get(key) is None or p.get(key) == "":
                missing[key] += 1
        date = p.get("construction_date")
        if date not in (None, ""):
            try:
                if not isinstance(date, str) or not re.fullmatch(r"[0-9]{8}", date):
                    raise ValueError
                years.append(datetime.strptime(date, "%Y%m%d").year)
            except ValueError:
                findings["unresolved_construction_date"] += 1
        well, hole = p.get("well_constructed_depth"), p.get("hole_constructed_depth")
        for key, depth in (("well", well), ("hole", hole)):
            if depth is not None and not valid_coordinate(depth, 0, float("inf")):
                findings[key + "_nonfinite_or_negative_depth"] += 1
        if all(valid_coordinate(v, 0, float("inf")) for v in (well, hole)) and well > hole:
            findings["well_deeper_than_drilled_hole"] += 1
        if p.get("altitude") is not None and not p.get("vertical_datum"):
            findings["altitude_without_vertical_datum"] += 1
        if isinstance(p.get("original_horizontal_datum"), str):
            source_datum[p["original_horizontal_datum"]] += 1
        if isinstance(p.get("vertical_datum"), str):
            vertical_datum[p["vertical_datum"]] += 1
    if any(missing[key] for key in FIELDS):
        findings["optional_metadata_missing_in_source"] = 1
    canonical = json.dumps(sorted(features, key=lambda item: str(item.get("id")) if isinstance(item, dict) else ""), sort_keys=True, separators=(",", ":")).encode()
    return {
        "status": "STRUCTURAL_ERROR" if errors else "REVIEW_REQUIRED" if findings else "STRUCTURE_VALID",
        "source": SOURCE, "schema_source": SCHEMA, "source_timestamp": document.get("timeStamp"),
        "source_bytes": len(raw), "source_sha256": sha(raw), "official_schema_sha256": sha(schema_raw),
        "canonical_features_sha256": sha(canonical), "source_feature_count": len(features),
        "unique_location_count": len(ids), "continuation_link": False,
        "property_schema_engine": "jsonschema 4.26.0, Draft 2019-09; optional nullable adapter",
        "published_coordinate_crs": "EPSG:4326", "source_original_horizontal_datums": dict(source_datum),
        "source_vertical_datums": dict(vertical_datum), "depth_units": "feet below land surface datum",
        "construction_year_range": [min(years), max(years)] if years else [],
        "valid_construction_dates": len(years), "critical_metadata_missing": {key: missing[key] for key in FIELDS},
        "all_missing_or_empty_property_counts": dict(missing), "omitted_property_counts": dict(omitted),
        "structural_errors": dict(errors), "review_findings": dict(findings),
        "observations_retrieved": False, "operational_status_verified": False,
    }


def render_svg(report):
    total = report["source_feature_count"]
    rows = []
    for i, key in enumerate(FIELDS):
        y = 126 + 31*i
        present = total - report["critical_metadata_missing"][key]
        width = round(250 * present / total, 2)
        rows.append(f'<text x="25" y="{y+15}">{escape(key.replace("_", " "))}</text><rect x="250" y="{y}" width="250" height="19" rx="3" fill="#e2e8f0"/><rect x="250" y="{y}" width="{width}" height="19" rx="3" fill="#0e7490"/><text x="515" y="{y+15}">{present}/{total}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="680" height="436" viewBox="0 0 680 436" role="img" aria-labelledby="title desc">\n'
            '<title id="title">USGS Miami-Dade bounded well catalogue metadata</title><desc id="desc">Bars represent the proportion of catalogue fields actually supplied, not well functionality.</desc>'
            '<rect width="680" height="436" rx="12" fill="#f8fafc"/><g font-family="sans-serif" font-size="14" fill="#172554">'
            '<text x="25" y="35" font-size="19" font-weight="bold">USGS groundwater metadata | Miami-Dade</text>'
            f'<text x="25" y="65">Official OGC monitoring-locations → schema + scope validator → {total} records</text>'
            '<text x="25" y="94" font-weight="bold">Metadata available / total catalogue records</text>'
            + ''.join(rows) + '<text x="25" y="401">Filled = supplied; grey = missing. No groundwater observations downloaded.</text></g></svg>\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("schema", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("diagram", type=Path)
    args = parser.parse_args()
    raw, document = read_bounded(args.source)
    schema_raw, schema = read_bounded(args.schema)
    report = validate(raw, document, schema_raw, schema)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.diagram.write_text(render_svg(report), encoding="utf-8")
    return int(bool(report["structural_errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
