# Original #514 — bounded USGS groundwater catalogue metadata

This closes the original engineering deliverable beyond its earlier syntax-only bot receipt: public source survey, useful validator, and original SVG derived from an actual bounded catalogue response. It does **not** establish unattended engineering, functioning wells, current water levels, statewide coverage, or observation accuracy.

## Source survey

| Official USGS resource | Use |
|---|---|
| [Monitoring locations](https://api.waterdata.usgs.gov/ogcapi/v1/collections/monitoring-locations) and [official schema](https://api.waterdata.usgs.gov/ogcapi/v1/collections/monitoring-locations/schema?f=json) | Catalogue metadata and field definitions; the only collection retrieved in this task. |
| [Time-series metadata](https://api.waterdata.usgs.gov/ogcapi/v1/collections/time-series-metadata) | Future source discovery: parameter, unit, and data availability; not fetched here. |
| [Field measurements](https://api.waterdata.usgs.gov/ogcapi/v1/collections/field-measurements) | Potential future discrete groundwater measurements; not fetched here. |
| [Data collection categories](https://waterdata.usgs.gov/data-collection-categories), [migration guide](https://api.waterdata.usgs.gov/docs/ogcapi/migration/) | Choosing appropriate catalogue versus observational endpoints. No daily or continuous observations retrieved. |

The exact query is `agency_code=USGS&state_code=12&county_code=086&site_type_code=GW&bbox=-80.4,25.65,-80.3,25.75&limit=500&f=json`. A small fixed Miami-Dade bounding box is a reproducible bounded sample, not a claim of total county coverage. The response had no continuation link. USGS publishes coordinates as EPSG:4326; original horizontal datum is a separate field. The official schema describes well and drilled-hole depth in feet below land surface datum, and makes clear that depth values are not available at every location. Attribution: U.S. Geological Survey, National Water Information System; [USGS copyright and credits](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits).

## Actual execution (15 November 2026)

`report.json` is the immutable aggregate local receipt, from actual official public bytes: 215 unique catalogue well records, 0 structural errors, 0 continuation links. Raw source and official schema hashes are included, alongside a stable canonical feature hash. The original `diagram.svg` is derived from the same receipt. Raw location names/coordinates are not redistributed.

Of 215 records, 100 recorded valid construction dates (1940–2010); 115 lacked a date. Well depth was present in 175, drilled-hole depth in 28, and local aquifer code in 122. Their nulls are retained as missing, never imputed as zero. The structural result is `REVIEW_REQUIRED` because optional metadata are incomplete; it is not an instrument, datum transformation, chemistry, or contemporary functioning-well certification. The schema itself labels non-null primitive types but the actual catalogue legitimately returns nulls, so only optional property nullability is adapted; the raw official schema is hashed unchanged. All returned non-null property types are checked by the upstream MIT-licensed `jsonschema` engine (pinned 4.26.0: https://github.com/python-jsonschema/jsonschema), and the existing Plenum `valid_coordinate` is reused. No new validation framework or service.

The path-scoped pull-request workflow fetches only the two expressly authorized metadata resources, checks the actual response, and uploads aggregate report, SVG, and hashes. It has no credential input or deployment path. The source is live, so future response timestamps and raw hashes may change; the canonical record hash detects real feature changes. This is not a prospective forecast run, and no embargoed data or prospective workflows are accessed.
