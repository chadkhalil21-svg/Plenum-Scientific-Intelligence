# USGS November 2026 prospective study: original OGC interval-query correction

**Recorded:** November 9, 2026 UTC, BEFORE the frozen November 11 forecast issuance and November 12–13 real river-flow target dates. This is a **source-query interoperability correction**, not a new research hypothesis or a different prediction protocol.

## Verified original upstream specification

The publicly precommitted [November 7 original hydrology protocol](../protocols/usgs-hydrology-2026-11.json) commits to **modern USGS OGC Daily Values API** `https://api.waterdata.usgs.gov/ogcapi/v1/collections/daily/items`, two specific gauges, discharge parameter `00060`, mean statistic `00003`, fixed October 1–November 4 development window, and November 12–13 future test observations.

Our original `src/plenum_ai/usgs_hydrology.py` had constructed the interval query as `time=2026-10-01/2026-11-04`. The official upstream documentation distinguishes:
- **`datetime`**: reserved OGC API *query parameter* for date/time interval filters, e.g. `datetime=2024-12-01/2024-12-31`.
- **`time`**: name of the *observation property* returned inside each daily FeatureCollection feature. This property is not the documented date-range query argument.

The original program's `time=START/END` could return an empty/incorrectly filtered result rather than original development measurements. Before live forecast issuance, change **only** the request key to `datetime=START/END`, preserving the original string dates and every scientific method.

**Upstream official documentation:** [Getting Started with USGS Water Data OGC APIs](https://api.waterdata.usgs.gov/docs/ogcapi/) and [Migration to Modernized USGS APIs](https://api.waterdata.usgs.gov/docs/ogcapi/migration/). The latter explains that the returned old WaterServices timestamp is now named `time` inside the daily dataset, separate from the query filter.

## What remains unchanged

- Original November 7 `protocols/usgs-hydrology-2026-11.json` and original source protocol commit `5599f4b8037e6d2a0dca78d0e3a03a034eb37c44`, with all immutable target dates and selection rules untouched.
- Both river locations (Potomac `01646500`, Choptank `01491000`); parameter code `00060`; mean statistic `00003`; `ft^3/s` units; public read-only bounded OGC API and maximum 500 features.
- Exact development window ending Nov 4, 2026 and fixed future target days Nov 12–13; no prospective holdout fetch prior to the original audit.
- Frozen Qwen3-1.7B and distinct SmolLM2 critic models, existing candidate forecast formula, three original baselines, rolling training folds, required five-percent margin and November 18 independent audit date.
- No new solver, evaluation framework, network privileges, confidential data, compute spending or repeated upstream software tests.

## Real evidence and limitations

This code corrects the source query by the USGS original **published request contract**. Our existing mocked-source tests were updated to reject `time=...` interval filters and require `datetime=...`, while still parsing returned observation property `time`. These tests validate **our adapter only**; they do not prove today's LIVE USGS API response, site coverage, completed forecasts, or original scientifically scored future outcomes. Keep source response SHA256, exact statuses, station/date/QC restrictions, immutable forecast commit timestamp and the original independent auditor.

This explanation was publicly committed before November 11 original issuance. If the upstream endpoint is unavailable or delivers insufficient approved data, report the source failure without inventing measurements or silently altering the model after observing outcomes. The outcome of this source-compatibility correction is **not evidence of AGI or ASI**.
