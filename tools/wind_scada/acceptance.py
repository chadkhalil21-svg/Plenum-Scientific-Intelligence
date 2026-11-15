"""Minimal diagnostic acceptance for the new adapter, not a retest of OpenOA."""
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

from validate import audit

source, metadata, output = map(Path, sys.argv[1:])
mapping = yaml.safe_load(metadata.read_text())["scada"]
first = pd.read_csv(source, nrows=1, dtype="string")
asset = first.loc[0, mapping["asset_id"]]
rows = pd.concat([first] * 6, ignore_index=True)
rows.loc[1, ["P_avg", "Ws_avg", "Ot_avg"]] = ["bad", "inf", pd.NA]
rows.loc[2, "Date_time"] = "2014-01-01T01:20:00+01:00"
rows.loc[3, ["Date_time", "Wind_turbine_name"]] = ["2014-01-01T01:30:00", "UNKNOWN"]
rows.loc[4, "Date_time"] = "2014-99-01T01:30:00+01:00"
rows.loc[5, "Date_time"] = "2014-01-01T01:03:00+01:00"
result, flags, gaps = audit(rows, mapping, {asset}, "Europe/Paris", {"Ya_avg": "deg"})
expected = {(3, "duplicate_asset_time", "Date_time"), (3, "not_numeric", "P_avg"),
            (3, "nonfinite_sensor", "Ws_avg"), (3, "missing_sensor", "Ot_avg"),
            (5, "timezone_missing", "Date_time"), (5, "unknown_asset", "Wind_turbine_name"),
            (6, "invalid_time", "Date_time"), (7, "off_utc_grid", "Date_time")}
assert result["status"] == "AUDITED_WITH_FINDINGS"
assert set(flags) == expected, flags
assert gaps == [(asset, "2014-01-01T00:10:00+00:00")], gaps
missing, _, _ = audit(rows.drop(columns=["P_avg"]), mapping, {asset}, "Europe/Paris", {"Ya_avg": "deg"})
assert missing["status"] == "INVALID_SCHEMA" and missing["missing_columns"] == ["P_avg"]
output.write_text(json.dumps({"scope": "six deliberately modified copies of one real row; not observations",
                             "expected_and_detected_diagnostics": sorted(flags),
                             "expected_and_detected_gap": gaps,
                             "missing_required_column_detected": missing["missing_columns"]}, indent=2) + "\n")
print("Malformed-input adapter integration acceptance passed.")
