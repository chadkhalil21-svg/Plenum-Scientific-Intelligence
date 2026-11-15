"""Offline review of Bowskill (2024) EIDC forage nutrient metadata and CSV.

Uses Python's maintained, free standard-library CSV/JSON/ZIP/Decimal tools;
does not extract archives, change observations, impute missing values, or
certify forage quality. See the dataset DOI and OGL attribution in the report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

DOI = "https://doi.org/10.5285/361f0587-4cc6-48df-9f7e-8ade331cf8d5"
CATALOGUE = "https://catalogue.ceh.ac.uk/documents/361f0587-4cc6-48df-9f7e-8ade331cf8d5"
SOURCE = "https://data-package.ceh.ac.uk/data/361f0587-4cc6-48df-9f7e-8ade331cf8d5.zip"
LICENCE = "https://spdx.org/licenses/OGL-UK-3.0"
CITATION = ("Bowskill, V. (2024). Nutritive and mineral content of hay from three species-rich "
            "floodplain meadows, England, 2020-21. NERC EDS Environmental Information Data Centre. " + DOI)
CSV = "data/minerals_and_nutritive_data_floodplain-meadows.csv"
README = "supporting-documents/read_me.txt"
CRATE = "ro-crate-metadata.json"
CSV_SHA = "f24489340f2ec398ec8c5f1e8394271c580d0f406b88dea1e080dcfdc2f170f7"
README_SHA = "9e0ce6ae46d4dc6668bcea189beea959f0e43eb9e9311d339635b7685b695f36"
FIELDS = ("SiteName Plot QuadratID Harvest Year DayNo GDD AET GFratio Yield_gm2 "
          "CP_gkg CP_percent CP_offtake_gm2 ME_Mjkg ME_percent ME_offtake_Mjm2 "
          "ADF_gkg ADF_percent ADF_offtake_gm2 NDF_gkg NDF_percent NDF_offtake_gm2 "
          "P_mgkg P_percent P_offtake_mgm2 B_mgkg Ca_mgkg Co_mgkg Cu_mgkg I_mgkg "
          "K_mgkg Mg_mgkg Mn_mgkg Mo_mgkg Na_mgkg Se_mgkg S_mgkg Zn_mgkg").split()
IDENTIFIERS = FIELDS[:6]
CORE = ["CP_gkg", "ME_Mjkg", "ADF_gkg", "NDF_gkg"]
START, END = date(2020, 5, 1), date(2021, 9, 30)
MAX_ARCHIVE = 2_000_000
MAX_MEMBER = 1_000_000
MAX_RECORDS = 5000
D = Decimal


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_archive(data: bytes, *, require_published_bytes: bool = False) -> dict:
    """Return source-specific metadata, structural findings and observation diagnostics.

    A CSV record number is 1-based, excluding the header. Missing and explicitly
    NA cells are counted separately and never converted to zero. Offtake and
    concentration consistency is a rounding-tolerant diagnostic, not a correction.
    """
    if len(data) > MAX_ARCHIVE:
        raise ValueError("archive exceeds bounded size")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.infolist()) > 30 or sum(m.file_size for m in z.infolist()) > 4 * MAX_MEMBER:
            raise ValueError("archive exceeds expanded-size/file-count bounds")
        members = {}
        for name in (CSV, README, CRATE):
            if z.namelist().count(name) != 1 or z.getinfo(name).file_size > MAX_MEMBER:
                raise ValueError("expected one bounded member: " + name)
            members[name] = z.read(name)
    digests = {name: sha(payload) for name, payload in members.items()}
    if require_published_bytes and (digests[CSV] != CSV_SHA or digests[README] != README_SHA):
        raise ValueError("pinned published CSV/README bytes changed")
    graph = json.loads(members[CRATE])["@graph"]
    datasets = [x for x in graph if isinstance(x, dict) and x.get("@type") == "Dataset"]
    if len(datasets) != 1:
        raise ValueError("expected one RO-Crate Dataset entity")
    meta = datasets[0]
    if (meta.get("identifier") != {"@id": DOI} or meta.get("license") != {"@id": LICENCE}
            or meta.get("isAccessibleForFree") is not True
            or meta.get("datePublished") != "2024-10-29"
            or meta.get("temporalCoverage") != ["2020-05-01/2021-09-30"]
            or not {CSV, README}.issubset({x.get("@id") for x in meta.get("hasPart", [])})):
        raise ValueError("published DOI/licence/time/file metadata mismatch")
    note = members[README].decode("utf-8-sig")
    reader = csv.reader(io.StringIO(members[CSV].decode("utf-8-sig"), newline=""), strict=True)
    if next(reader, None) != FIELDS:
        raise ValueError("header differs from documented 38-column source schema")

    findings = []
    blank, na, by_site, by_year, by_group = (Counter() for _ in range(5))
    present_core_by_year = {field: Counter() for field in CORE}
    pairs_checked = Counter()
    keys = set()
    seen_rows = set()
    structural_records = set()
    source_records = set()
    count = 0

    def flag(record: int | None, code: str, field: str, kind: str) -> None:
        findings.append({"record": record, "code": code, "field": field, "kind": kind})
        if record is not None:
            (structural_records if kind == "structural" else source_records).add(record)

    def compare(num: int, numeric: dict, a: str, b: str, divisor: Decimal, tolerance: Decimal, *, multiply_yield: bool = False, code: str = "inconsistent_conversion") -> None:
        if a not in numeric or b not in numeric or (multiply_yield and "Yield_gm2" not in numeric):
            return
        actual = numeric[a] * (numeric["Yield_gm2"] if multiply_yield else D(1)) / divisor
        label = f"{a}->{b}"
        if a == "P_mgkg" and b == "P_offtake_mgm2":
            label += f" (yield multiplier, divisor={divisor})"
        pairs_checked[label] += 1
        if abs(actual - numeric[b]) > tolerance:
            flag(num, code, b, "source_review")

    for count, cells in enumerate(reader, 1):
        if count > MAX_RECORDS:
            raise ValueError("record count exceeds bound")
        if len(cells) != len(FIELDS):
            flag(count, "incorrect_record_width", "row", "structural")
            continue
        row = dict(zip(FIELDS, cells))
        for field, value in row.items():
            if not value.strip():
                blank[field] += 1
            elif value.strip().upper() == "NA":
                na[field] += 1
        if tuple(cells) in seen_rows:
            flag(count, "duplicate_exact_record", "row", "structural")
        seen_rows.add(tuple(cells))
        key = tuple(row[field] for field in ("SiteName", "Year", "Harvest", "Plot", "QuadratID"))
        if key in keys:
            flag(count, "duplicate_sample_key", "SiteName/Year/Harvest/Plot/QuadratID", "structural")
        keys.add(key)
        if any(not row[f].strip() or row[f].strip().upper() == "NA" for f in IDENTIFIERS):
            flag(count, "missing_identifier", "sampling_metadata", "structural")
        try:
            year, day, harvest = (int(row[f]) for f in ("Year", "DayNo", "Harvest"))
            observed = date(year, 1, 1) + timedelta(days=day - 1)
            if observed.year != year or not START <= observed <= END or not 1 <= harvest <= 6:
                raise ValueError("outside documented time/harvest scope")
        except (ValueError, OverflowError):
            flag(count, "invalid_sampling_date_or_harvest", "Year/DayNo/Harvest", "structural")
        by_site[row["SiteName"]] += 1
        by_year[row["Year"]] += 1
        by_group[(row["SiteName"], row["Year"], row["Harvest"])] += 1
        numeric = {}
        for field in FIELDS[6:]:
            value = row[field].strip()
            if not value or value.upper() == "NA":
                continue
            try:
                value = D(value)
                if not value.is_finite() or value.copy_abs() > D("1e12"):
                    raise InvalidOperation
            except InvalidOperation:
                flag(count, "nonfinite_or_nonnumeric", field, "structural")
                continue
            numeric[field] = value
            if value < 0:
                flag(count, "negative_measurement", field, "source_review")
            limit = (D(1000) if field.endswith("_gkg") else
                     D(1_000_000) if field.endswith("_mgkg") else
                     D(100) if field.endswith("_percent") and field != "ME_percent" else None)
            if limit is not None and value > limit:
                flag(count, "concentration_above_total_mass", field, "source_review")
        for field in CORE:
            if field in numeric:
                present_core_by_year[field][row["Year"]] += 1
        for field in ("CP", "ADF", "NDF"):
            compare(count, numeric, field + "_gkg", field + "_percent", D(10), D(".005"))
            compare(count, numeric, field + "_percent", field + "_offtake_gm2", D(100), D(".03"), multiply_yield=True)
        compare(count, numeric, "P_mgkg", "P_percent", D(10_000), D(".005"))
        compare(count, numeric, "ME_Mjkg", "ME_offtake_Mjm2", D(1000), D(".01"), multiply_yield=True)
        # P_offtake_mgm2 claims mg/m2; measured mg/kg * yield g/m2 / 1000 is mg/m2.
        compare(count, numeric, "P_mgkg", "P_offtake_mgm2", D(1000), D(".01"), multiply_yield=True, code="phosphorus_offtake_label_mgm2_inconsistent")
        compare(count, numeric, "P_mgkg", "P_offtake_mgm2", D(1_000_000), D(".01"), multiply_yield=True, code="phosphorus_offtake_gm2_alternative_inconsistent")
        if "ADF_gkg" in numeric and "NDF_gkg" in numeric and numeric["ADF_gkg"] > numeric["NDF_gkg"]:
            flag(count, "adf_exceeds_ndf", "ADF_gkg/NDF_gkg", "source_review")

    if count == 0:
        raise ValueError("no observations")
    if len(by_site) != 3:
        flag(None, "site_count_differs_from_catalogue", "SiteName", "source_review")
    if "collected on 4 sites" in note and "Sites: 3" in note:
        flag(None, "readme_site_count_inconsistent", README, "source_review")
    if "ME_percent" in FIELDS:
        flag(None, "energy_percentage_dimensional_meaning_unspecified", "ME_percent", "source_review")
    # Observed 2020 sampling uses six quadrats per harvest, 2021 three pooled quadrats.
    # A low count is recorded as a documentation query, not invented replacement data.
    low_groups = []
    for (site, year, harvest), n in sorted(by_group.items()):
        if n != (6 if year == "2020" else 3):
            low_groups.append({"site": site, "year": year, "harvest": harvest, "observed": n})
    if low_groups:
        flag(None, "sampling_group_count_differs_from_readme_design", "sampling_metadata", "source_review")
    return {
        "schema": "plenum-eidc-forage-metadata-audit-v1",
        "status": "STRUCTURAL_ERRORS" if structural_records else ("REVIEW_REQUIRED_SOURCE_FINDINGS" if findings else "STRUCTURALLY_VALID"),
        "source": {"doi": DOI, "catalogue": CATALOGUE, "download": SOURCE, "licence": LICENCE, "citation": CITATION,
                   "zip_sha256": sha(data), "member_sha256": digests,
                   "published_csv_and_readme_bytes_match": digests[CSV] == CSV_SHA and digests[README] == README_SHA,
                   "dataset_metadata_matched": True, "temporal_coverage": meta["temporalCoverage"]},
        "total_records": count, "column_count": len(FIELDS), "structurally_invalid_records": len(structural_records),
        "source_review_records": len(source_records), "site_counts": dict(by_site), "year_counts": dict(by_year),
        "missing_blank_total": sum(blank.values()), "missing_na_total": sum(na.values()),
        "missing_blank_by_field": dict(blank), "missing_na_by_field": dict(na),
        "core_nutrient_nonmissing_by_year": {field: dict(c) for field, c in present_core_by_year.items()},
        "comparisons_performed": dict(pairs_checked), "sampling_groups_to_review": low_groups,
        "finding_counts": dict(Counter(item["code"] for item in findings)), "findings": findings,
        "notes": ["Missing cells remain missing; no imputation", "RO-Crate and observed site counts show three sites; README also says four", "P_mgkg * Yield_gm2 / 1000 yields mg/m2; all values matching division by 1e6 instead warrant checking the P_offtake_mgm2 label (not silently converting)", "ME concentration uses MJ/kg; a percentage has no documented energy meaning", "NIRS-related bounds flag observations for review, not certified assay errors", "Observed sampling groups only; not an assertion that the study design required an unobserved group", "No experimental or biological validity certification"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("--require-published-bytes", action="store_true")
    parser.add_argument("--audit", action="store_true", help="exit successfully on source-review findings; never on structural errors")
    args = parser.parse_args(argv)
    try:
        if args.source_zip.stat().st_size > MAX_ARCHIVE:
            raise ValueError("archive exceeds bounded size")
        report = validate_archive(args.source_zip.read_bytes(), require_published_bytes=args.require_published_bytes)
    except (OSError, KeyError, TypeError, AttributeError, UnicodeError, ValueError, csv.Error, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "INVALID_INPUT", "reason": str(exc)}))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["structurally_invalid_records"] or (report["findings"] and not args.audit) else 0


if __name__ == "__main__":
    sys.exit(main())
