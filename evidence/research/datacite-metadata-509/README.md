# Original #509 — public research-metadata validation

Executed 15 November 2026. This is the original owner-authored public Python
validator objective, not the earlier syntax-only starter run. The recorded
reservation is issue #509 comment `6902098845`.

## Actual evidence

- Direct, anonymous DataCite REST API GET, historical Zenodo dataset query:
  `client-id=cern.zenodo`, `publicationYear:2024 AND types.resourceTypeGeneral:Dataset`,
  `page[size]=8`, `sort=created`. The original discovery and detail responses
  returned the same eight DOI identities. Detail mode supplies the original
  base64 XML in each JSON record.
- `records.json`: original discovery response, SHA-256
  `523d52abb835010ed171f66b04101a066042a0e321951c3dd3f639a3f201c080`.
- `records-detail.json`: exact detail response, SHA-256
  `77a80d0f00b823eb94ebac805fdb01803f6c5ac96d24f79caa7db3a0f86805e0`.
- `report.json`: actual local run after independent review of schema pinning,
  SHA-256 `6b3735b41c2f20bc525524253eb34dc609379b5a199d9083a65ebc5c79bae0a9`.
- The maintained lxml 6.1.1 / libxml2 2.14.6 XMLSchema engine validated against
  the official versioned DataCite 4.7 XSD and all eleven required includes.
  All twelve exact source SHA-256 values are in the validator and report.
  The XSD files are not re-vendored; retrieve from the official versioned site.

Results: 8 distinct DOI identities, 8 XSD-compatible records, 8 with all six
required DOI/title/creator/publisher/year/type values consistent in JSON and
XML, 0 invalid. All 8 require review because the original XML references a
generic kernel-4 schema location rather than an identified minor release;
compatibility against 4.7 is **not** certification of historical schema version.
Optional metadata gaps: language absent for 3 records and subjects absent for
1. The sample is a bounded historical metadata snapshot, not representative of
all Zenodo records. These are metadata checks only, not dataset openness,
license, scientific validity, identity of individuals, or access certification.

DataCite states its openly available DOI metadata is CC0; this is distinct from
any underlying resource license. No dataset payloads were downloaded.

## Reproduce from the archived snapshot (no new DOI query)

Use Python 3.9+ with lxml installed. Obtain the fixed XSD dependency set from
`https://schema.datacite.org/meta/kernel-4.7/`, preserving filenames and paths
listed in `report.json` under `schema_file_sha256`. The validator refuses a
missing, altered or unrecognized XSD file before schema compilation. For example:

```sh
python -m pip install 'lxml==6.1.1'
python tools/datacite_metadata_validator.py \
  evidence/research/datacite-metadata-509/records-detail.json \
  --schema /path/to/kernel-4.7/metadata.xsd \
  --output /tmp/datacite-report.json \
  --client cern.zenodo --year 2024 --type Dataset \
  --source-url 'https://api.datacite.org/dois?client-id=cern.zenodo&query=publicationYear%3A2024%20AND%20types.resourceTypeGeneral%3ADataset&page%5Bsize%5D=8&sort=created&detail=true'
```

The program accepts up to twenty DataCite JSON API records containing the
original `xml` value, refuses oversized inputs and external XML entities,
and uses a local pinned schema rather than fetching schemas named by untrusted
records. Optional scope parameters assert expected client, year and work type.
Exit 2 means at least one invalid record; exit 0 means no invalid records, not
that review flags are absent. Malformed or untrusted input/schema fails closed.

Official references:

- https://support.datacite.org/docs/api-queries
- https://support.datacite.org/docs/how-can-i-harvest-xml-metadata-with-datacite-apis
- https://support.datacite.org/docs/harvesting-datacite-doi-metadata
- https://schema.datacite.org/meta/kernel-4.7/
- https://schema.datacite.org/meta/kernel-4.7/metadata.xsd
