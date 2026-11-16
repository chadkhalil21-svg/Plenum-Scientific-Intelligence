# USGS earthquake catalog validation (original founder mission #378)

This is a reusable catalog-consistency validator and an original SVG illustration of a real historical selection of earthquake observations. It uses the existing GeoJSON FeatureCollection schema, Python jsonschema and Matplotlib rather than a new validation or rendering framework.

## Reproduce

Run in a Python 3.12 environment. The actual execution used installed jsonschema 4.26.0 (MIT) and Matplotlib 3.10.8 (PSF-compatible license).

```sh
python -m pip install jsonschema==4.26.0 matplotlib==3.10.8
curl --fail --silent --show-error --max-time 25 \
  'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-01-01&endtime=2024-01-08&minmagnitude=5&eventtype=earthquake&orderby=time-asc' \
  -o earthquakes.geojson
curl --fail --silent --show-error --max-time 25 \
  'https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2024-01-01&endtime=2024-01-08&minmagnitude=5&eventtype=earthquake&orderby=time-asc' \
  -o earthquakes.csv
curl --fail --silent --show-error --max-time 15 \
  https://geojson.org/schema/FeatureCollection.json -o FeatureCollection.json
python tools/validate_usgs_earthquakes.py \
  --geojson earthquakes.geojson --csv earthquakes.csv --schema FeatureCollection.json \
  --start 2024-01-01T00:00:00Z --end 2024-01-08T00:00:00Z --min-magnitude 5 \
  --svg earthquakes.svg --report report.json
```

The validator rejects malformed input, a different upstream schema digest, duplicate event IDs, differing ID sets, disagreements between eight shared fields and events outside the selection. It checks the USGS response status/count and bounded geographic coordinates. It does not impose a scientifically unjustified minimum depth. The report identifies the exact input bytes and an order-independent semantic digest of the selected shared fields. A historical catalog query is not an immutable upstream archive: catalog revisions (or the GeoJSON response's generation timestamp) can change the downloaded bytes. Compare the reported semantic digest to the recorded value before treating a later download as the same observations. The validator does not redistribute the original raw downloads.

## Executed evidence

The connected task-scoped Engineering specialist obtained GeoJSON and CSV independently from the public USGS service, checked the schema hash, ran the validator locally on the real files (Python 3.12.14, exit 0), and visually inspected the SVG rendered using Inkscape on 16 November 2026 UTC. No GitHub runner, model inference, credentials, private account data, new hosting or paid API were used.

| Measurement | Result |
| --- | --- |
| Unique event IDs in both exports | 33 |
| Shared observation fields compared per ID | 8 |
| Field comparisons | 264 |
| Field mismatches | 0 |
| Catalog-reviewed events | 33 |
| Preferred magnitude range | 5.0–7.5 |
| Depth range | 6–197 km |

The largest preferred magnitude is USGS event [us6000m0xl](https://earthquake.usgs.gov/earthquakes/eventpage/us6000m0xl), the 2024 Noto Peninsula earthquake. The actual JSON report and original time-based SVG are included here; source file digests are recorded in the report.

- Tool SHA-256: `137e179cb5b939203da4a33516c27331f93f3645cf576a3b90ab41bfc39f9736`
- Report SHA-256: `da6def045d0e5c27a0d93538efe836fcd238d7e9dc0c6ddfef417c084fc9f884`
- SVG SHA-256: `57a9119d063d88cbeab204ea430f4445bc62bd900d75baac697cd8592fadc639`

The two serialization formats come from the same catalog. Their agreement is a format and data-integrity check, not independent geological measurements, a complete earthquake catalog, or an assessment of seismic hazard. The original failed Chief run 42796438425 remains a historical failure; this execution is a separate connected specialist outcome, pending independent peer review.

## Source and licensing

- [USGS ANSS Comprehensive Earthquake Catalog: FDSN query parameters](https://earthquake.usgs.gov/fdsnws/event/1/)
- [USGS GeoJSON summary format](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
- [USGS CSV format](https://earthquake.usgs.gov/earthquakes/feed/v1.0/csv.php)
- [USGS data credit and copyright policy](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits); USGS-originated data are public domain, with exceptions for third-party content. Only derived numerical results and an original illustration are published here.
- [GeoJSON schema upstream (MIT)](https://github.com/geojson/schema), exact schema SHA-256 recorded in the report (draft-07).
- [jsonschema upstream (MIT)](https://github.com/python-jsonschema/jsonschema) and [Matplotlib license](https://matplotlib.org/3.10.8/devel/license.html).
