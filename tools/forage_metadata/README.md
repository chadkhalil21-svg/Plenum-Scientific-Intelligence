# EIDC forage nutrient metadata validator (#520)

This callable, source-specific Python validator reviews Bowskill's published EIDC hay dataset. It uses the Python 3.11+ standard library and no inference, external packages or paid services.

## Run the review

```sh
curl --fail --location --silent --show-error --proto '=https' --max-filesize 2000000 --max-time 45 \
  https://data-package.ceh.ac.uk/data/361f0587-4cc6-48df-9f7e-8ade331cf8d5.zip -o forage.zip
python tools/forage_metadata/validate.py forage.zip --require-published-bytes --audit > report.json
```

`validate_archive(bytes, require_published_bytes=True)` is also callable. The published CSV and README member hashes are pinned because the provider dynamically packages the archive. The metadata checks use its RO-Crate DOI, licence, publication date, file identifiers and temporal coverage. CSV record numbers start at one, excluding the header. Default exit codes: 0 for a clean review, 1 for findings or structural errors, and 2 for invalid input. For a review-only CI audit, `--audit` permits exit 0 when there are source findings but no structural errors; the JSON continues to mark the dataset `REVIEW_REQUIRED_SOURCE_FINDINGS`.

The initial actual source acquisition processed 125 observations and 38 fields, with no malformed record widths, duplicate sample keys or nonnumeric present numeric values. It found 1,066 blank cells and three `NA` cells, and 54 observations with the four core nutrient measurements (all in 2021). One NDF observation exceeds 1,000 g/kg and 100%. All 125 phosphorus offtake values differ from the `mg/m2` column label's dimensional conversion and match the `g/m2` alternative to published rounding precision. The README states both four and three sites; the catalogue and data show three. The energy percentage label lacks a documented dimensional interpretation. One observed sampling group has fewer records than described by the README. Preserve these original values; query the source author before applying corrections.

The validator audits structure, units, missingness and source metadata. It does not certify biological measurements, experimental completeness, feed safety or nutritional adequacy.

## Source and rights

Bowskill, V. (2024). *Nutritive and mineral content of hay from three species-rich floodplain meadows, England, 2020-21*. NERC EDS Environmental Information Data Centre. https://doi.org/10.5285/361f0587-4cc6-48df-9f7e-8ade331cf8d5

[Catalogue and source licence](https://catalogue.ceh.ac.uk/documents/361f0587-4cc6-48df-9f7e-8ade331cf8d5): [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). The initial local report and GitHub Actions report do not republish the source file; the source-member SHA-256 fingerprints preserve reproducibility.
