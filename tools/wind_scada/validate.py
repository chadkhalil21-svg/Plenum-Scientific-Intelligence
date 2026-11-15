"""Read-only SCADA CSV validation using OpenOA's published schema and time utilities."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import openoa
import pandas as pd
import yaml
from openoa.plant import column_validator
from openoa.schema.metadata import SCADAMetaData
from openoa.utils import filters, timeseries


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def audit(data, mapping, expected_assets, local_zone, extras, temperature_screen=None):
    schema = SCADAMetaData(**mapping)
    # Only the explicitly supplied source channels are required. The upstream
    # optional/default turbine-status and derived-energy columns are not invented.
    fields = {key: schema.col_map[key] for key in mapping if key != "frequency"}
    if not {"time", "asset_id"} <= fields.keys() or len(set(fields.values())) != len(fields):
        raise ValueError("metadata must provide distinct time, asset and channel mappings")
    if not any(schema.dtypes[key] is float for key in fields):
        raise ValueError("metadata must specify at least one numeric SCADA channel")
    units = {source: schema.units[key] for key, source in fields.items() if schema.dtypes[key] is float}
    if set(fields.values()) & set(extras):
        raise ValueError("extra channel overrides a published SCADA mapping")
    units.update(extras)
    columns = fields | {f"extra:{source}": source for source in extras}
    absent = sorted(column_validator(data, column_names=columns))
    result = {"rows": len(data), "frequency": schema.frequency, "source_fields": fields,
              "numeric_units": units, "missing_columns": absent,
              "unmapped_columns": sorted(set(data.columns) - set(columns.values()))}
    flags = []
    gaps = []
    if absent or data.empty or data.columns.duplicated().any():
        return result | {"status": "INVALID_SCHEMA"}, flags, gaps

    def add(code, column, mask):
        flags.extend((int(i) + 2, code, column) for i in data.index[mask])

    time_col, asset_col = fields["time"], fields["asset_id"]
    raw = data[time_col].astype("string").str.strip()
    asset = data[asset_col].astype("string").str.strip()
    has_time = raw.notna() & raw.ne("")
    explicit_offset = raw.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True, na=False)
    utc = pd.to_datetime(raw.where(explicit_offset), format="ISO8601", utc=True, errors="coerce")
    add("missing_time", time_col, ~has_time)
    add("timezone_missing", time_col, has_time & ~explicit_offset)
    add("invalid_time", time_col, explicit_offset & utc.isna())
    if local_zone:
        # Compare explicit offsets against the declared source zone, including DST.
        original = raw.str.extract(r"(Z|[+-]\d{2}:?\d{2})$", expand=False).str.replace(":", "", regex=False).replace("Z", "+0000")
        expected = utc.dt.tz_convert(local_zone).dt.strftime("%z")
        add("source_zone_offset_mismatch", time_col, utc.notna() & original.ne(expected))
    has_asset = asset.notna() & asset.ne("")
    add("missing_asset", asset_col, ~has_asset)
    if expected_assets is not None:
        add("unknown_asset", asset_col, has_asset & ~asset.isin(expected_assets))
    add("off_utc_grid", time_col, utc.notna() & utc.ne(utc.dt.floor(schema.frequency)))

    stats = {}
    for source, unit in units.items():
        column = data[source].astype("string").str.strip()
        present = column.notna() & column.ne("")
        numeric = pd.to_numeric(column, errors="coerce")
        invalid = present & numeric.isna()
        nonfinite = numeric.notna() & ~np.isfinite(numeric)
        add("missing_sensor", source, ~present)
        add("not_numeric", source, invalid)
        add("nonfinite_sensor", source, nonfinite)
        finite = numeric[numeric.notna() & np.isfinite(numeric)]
        stats[source] = {"unit": unit, "missing": int((~present).sum()),
                         "not_numeric": int(invalid.sum()), "nonfinite": int(nonfinite.sum()),
                         "finite": len(finite), "min": float(finite.min()) if len(finite) else None,
                         "max": float(finite.max()) if len(finite) else None}
        if source == fields.get("WMET_HorWdSpd"):
            add("negative_wind_speed", source, numeric.notna() & np.isfinite(numeric) & numeric.lt(0))
        if source == fields.get("WMET_EnvTmp") and temperature_screen is not None:
            outside = filters.range_flag(numeric, *temperature_screen)
            add("outside_configured_temperature_screen", source, numeric.notna() & np.isfinite(numeric) & outside)

    by_asset = {}
    # OpenOA reports subsequent duplicate instances (not the first member).
    for name, group in pd.DataFrame({"asset": asset, "utc": utc}).loc[has_asset & utc.notna()].groupby("asset"):
        timestamps = group.utc.sort_values(kind="stable")
        dup = timeseries.find_duplicate_times(timestamps)
        flags.extend((int(i) + 2, "duplicate_asset_time", time_col) for i in dup.index)
        on_grid = timestamps[timestamps.eq(timestamps.dt.floor(schema.frequency))].drop_duplicates()
        if len(on_grid) and (on_grid.iloc[-1] - on_grid.iloc[0]) / pd.Timedelta(schema.frequency) > 2_000_000:
            raise ValueError(f"gap range exceeds bounded audit for asset {name}")
        missing = timeseries.find_time_gaps(on_grid, schema.frequency) if len(on_grid) else pd.Series([], dtype=object)
        gaps.extend((str(name), value.isoformat()) for value in sorted(missing))
        by_asset[str(name)] = {"dated_rows": len(timestamps), "duplicate_rows": len(dup),
                               "missing_interior_utc_slots": len(missing),
                               "first_utc": timestamps.iloc[0].isoformat(),
                               "last_utc": timestamps.iloc[-1].isoformat()}

    counts = {}
    for _, code, _ in flags:
        counts[code] = counts.get(code, 0) + 1
    absent_assets = sorted(set(expected_assets or []) - set(by_asset))
    result.update(status="AUDITED_WITH_FINDINGS" if flags or gaps or absent_assets else "CLEAN_IN_CHECKED_SCOPE",
                  sensor_statistics=stats, asset_statistics=by_asset, diagnostic_counts=counts,
                  unique_flagged_rows=len({row for row, _, _ in flags}), interior_missing_slots=len(gaps),
                  expected_assets=sorted(expected_assets) if expected_assets is not None else None,
                  expected_assets_not_observed=absent_assets, temperature_screen_c=temperature_screen,
                  local_zone=local_zone, scope="Raw observations, no cleaning; gaps within each asset's observed on-grid span; not calibration or performance validation.")
    return result, flags, gaps


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as src:
        header = next(csv.reader(src), [])
    if not header or len(set(header)) != len(header):
        raise ValueError("empty or duplicate CSV header")
    return pd.read_csv(path, dtype="string")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--assets", type=Path, help="CSV containing the mapped asset identifier column")
    parser.add_argument("--local-zone", help="IANA timezone for validating explicit source offsets")
    parser.add_argument("--extra-channel", action="append", default=[], metavar="COLUMN=UNIT")
    parser.add_argument("--temperature-screen-c", nargs=2, type=float, metavar=("MIN", "MAX"), help="optional source-specific screening limits, not physical validity limits")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--audit", action="store_true", help="exit 0 for a completed audit, even with data findings")
    args = parser.parse_args()
    mapping = yaml.safe_load(args.metadata.read_text())["scada"]
    extras = dict(entry.split("=", 1) for entry in args.extra_channel)
    assets = set(read_csv(args.assets)[mapping["asset_id"]].dropna()) if args.assets else None
    data = read_csv(args.csv)
    if args.temperature_screen_c and (not all(np.isfinite(args.temperature_screen_c)) or args.temperature_screen_c[0] > args.temperature_screen_c[1]):
        parser.error("temperature screen requires finite increasing bounds")
    report, flags, gaps = audit(data, mapping, assets, args.local_zone, extras, args.temperature_screen_c)
    report.update(input_sha256=digest(args.csv), metadata_sha256=digest(args.metadata), openoa_version=openoa.__version__,
                  assets_sha256=digest(args.assets) if args.assets else None)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    for name, header, records in (("row_diagnostics.csv", ("csv_record_number", "diagnostic", "column"), sorted(flags)),
                                  ("missing_utc_slots.csv", ("asset_id", "utc"), gaps)):
        with (args.out / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(records)
    print(json.dumps(report, sort_keys=True, allow_nan=False))
    return 0 if report["status"] == "CLEAN_IN_CHECKED_SCOPE" or (args.audit and report["status"] == "AUDITED_WITH_FINDINGS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
