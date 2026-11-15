# Public weather-observation intake validator — original issue #359

## Scope and reproduction

The Python command validates a bounded, single-station NOAA NCEI
Global Historical Climatology Network daily (GHCN-Daily) **Data Service API
CSV** with `units=metric`, `includeAttributes=true`, and TMAX, TMIN, PRCP.
It uses Python's standard-library CSV and Decimal parsers: no external model,
data service, package, credential, or network is required to run the validator.
The input is daily sensor-derived station summaries (not raw instantaneous
or simultaneous electronic measurements).

```sh
python3 validate_daily_weather.py noaa-miami-2025-01.csv \
  --station USW00012839 --start 2025-01-01 --end 2025-01-31 \
  --units metric --out new-report.json
```

Use a new output path to preserve prior evidence. Exit 0 means only that
the requested date coverage and listed intake checks pass; exit 1 means a
record-level error or incompleteness; exit 2 means the input/configuration
cannot be interpreted. See the JSON error and incomplete counts and findings.
The validator supports 1–3,660 requested calendar days, at most 3,660 rows
and a 2 MB input. It requires an explicit expected station and date interval.
The caller is responsible for confirming the original API units: the CSV
does not carry an independent units declaration. Do not feed raw GHCN .dly
integer values or Fahrenheit values into this metric interface.

The checks include required field names and duplicate columns, row width,
expected station, ISO date validity, duplicate station-day and complete
calendar coverage, missing values, finite numeric values, the absolute-zero
temperature limit, nonnegative precipitation, TMIN <= TMAX, source/measurement
flags, NOAA's quality flags, and optional local observation time (including
2400 at end of day). Nonblank recognized quality flags are reported as intake
errors; unknown flags are reported separately. Nonblank measurement flags
are retained, not silently stripped or automatically treated as erroneous.
Missing values and missing dates are incomplete, not replaced by zero.

This is a useful input/metadata gate, not NOAA's operational QA system, a
claim of instrument calibration, a complete climate homogenization check,
or an inference that blank quality flags eliminate all observation errors.
No station-specific outlier limits or precipitation traces are invented.

## Source and immutable input

- NOAA NCEI, GHCN-Daily, station USW00012839 (Miami International Airport,
  Florida, US), inclusive 2025-01-01 through 2025-01-31; retrieved
  2026-11-15. Exact unmodified API response:
  [Daily Summaries CSV](https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=USW00012839&startDate=2025-01-01&endDate=2025-01-31&dataTypes=TMAX,TMIN,PRCP&units=metric&includeAttributes=true&format=csv).
  2,266 bytes, SHA-256 `354c21d5230f3a0063ce9e4127593813b6f17ce992f795a7a0892c4e7ef8fad4`.
- [Station metadata](https://www.ncei.noaa.gov/cdo-web/datasets/GHCND/stations/GHCND%3AUSW00012839/detail).
- [Dataset metadata and citation](https://www.ncei.noaa.gov/metadata/geoportal/rest/metadata/item/gov.noaa.ncdc%3AC00861/html),
  [GHCN-Daily format/flags](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt),
  [by-station attributes](https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/readme-by_station.txt),
  and [Data Service API documentation](https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation).
- Cite: Menne, M. J., et al. (2012), Global Historical Climatology
  Network-Daily (GHCN-Daily), Version 3, NOAA National Centers for
  Environmental Information, DOI [10.7289/V5D21VHZ](https://doi.org/10.7289/V5D21VHZ);
  station/date subset as specified above.
- NOAA states that its own data are in the public domain in its
  [public-use FAQ](https://www.noaa.gov/office-education/outreach-communication/faq);
  [NCEI open data policy](https://www.ncei.noaa.gov/sites/default/files/2023-12/NCEI%20PD-10-2-02%20-%20Open%20Data%20Policy%20Signed.pdf).
  The archived station observations use US NOAA/NWS/WBAN source codes
  W and 1; no claim is made over NOAA data or of NOAA endorsement.

## Original evidence

The exact input is archived unchanged. The JSON report binds the input and
validator SHA-256 values to the actual bounded execution. The underlying
historical agent run #42782070733 reported BLOCKED; it is not repeated or
claimed as the source of this result.

The original execution on Python 3.12.14 returned exit 0 with
`PASSED_BOUNDED_INTAKE`: 31 rows, 31 expected days covered, 93 numeric
entries, zero missing values, zero nonblank NOAA quality flags, and zero
errors/incomplete findings. These are raw numerical entries, not
independently calibrated observations. The report retains six trace
precipitation measurement flags (T); a reported trace is not proof that no
precipitation occurred. All 31 PRCP source flags are W (WBAN/ASOS Summary
of the Day), with local observation time 2400. TMAX and TMIN each have 30
W flags and one 1 (NWS CF6 daily summaries). A separate peer inspected
the exact archived bytes and official format documentation.

- Validator SHA-256:
  `d35b6477e586418f1221982ec558021c3797fabcd750ef595cbc090c0e23cd35`
- Original report SHA-256:
  `1640bfff66e86a6364645f8ee9489cf72ef139244d0773d13b695a2f2a2b5524`
