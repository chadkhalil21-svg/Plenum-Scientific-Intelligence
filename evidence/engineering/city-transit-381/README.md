# Manteca fixed-route transit study — original #381

This is the actual public-data deliverable for [original issue #381](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/381), not a syntax-only demonstration. The archived feed is the City's October 1, 2026 fixed-route release, not a live timetable. The official validator was executed once on the supplied archive on November 15, 2026 (UTC). An independent standard-library program checked the original report and performed data-derived drawing from its stored coordinates. The subsequent safety refinement of the independent reader yielded byte-identical outputs; the official CLI was not rerun.

## Findings

- Official MobilityData GTFS Validator v8.0.1 completed with exit code 0 and zero system errors. This means the validation process completed, **not that the feed passed**.
- Its actual report contains 57 errors (`trip_distance_exceeds_shape_distance`), 81 warnings and 287 informational notices. The underlying shape-distance issue must not be inferred away from the map. The reported feed interval is October 1, 2026–August 31, 2027; the computed service window instead extends to December 31, 2027, including an explicit calendar exception. Neither finding implies future operation.
- Independent identity, reference, sequence and coordinate checks passed: seven routes, 131 stops, 282 trips, eight shapes, 3,644 stored shape points and 7,776 stop-time rows (not unique passenger journeys). All route/shape/service and stop-time foreign keys resolve. The map uses actual ordered shape coordinates and route/stop relations, not invented connections; overlapping lines can conceal one another. Trips are schedule definitions, not observed ridership. This is not a navigational map, live service, distance accuracy or accessibility certification.

## Files and reproduction

| File | Purpose |
|---|---|
| `gtfs.zip` | Unmodified official Manteca data, license below |
| `upstream-report.json` | Unmodified original MobilityData report |
| `upstream-system-errors.json` | Unmodified original system-error report |
| `gtfs_transit_study.py` | Bounded immutable-study identity/geometry checks and original SVG generator |
| `independent-report.json` | Actual independent count reconciliation and notice totals |
| `transit-patterns.svg` | Original visualization from the actual coordinates |

The canonical, general-purpose validator is upstream [MobilityData v8.0.1](https://github.com/MobilityData/gtfs-validator/releases/tag/v8.0.1), Apache-2.0; do not reimplement it. Its [release JAR](https://github.com/MobilityData/gtfs-validator/releases/download/v8.0.1/gtfs-validator-8.0.1-cli.jar) SHA-256 is `19293ddd9b6f954f216d4f12054bd8a3232921751c4484339e339764a91000e2`. Java 21 ran `java -jar gtfs-validator-8.0.1-cli.jar -i gtfs.zip -o upstream-report`; exit 0, original report preserved. Its optional latest-version lookup failed DNS; the pinned validator still executed successfully and recorded no system notices. The archived original report records the execution's scratch file path and timestamp; it is not rewritten. Re-executing the upstream program can generate timestamp-specific report bytes and should not overwrite this original receipt.

To reproduce the independent readback and drawing with Python 3.11+ without network or packages, use the exact archived input and reports:

```sh
python gtfs_transit_study.py --feed gtfs.zip --upstream-report upstream-report.json --system-errors upstream-system-errors.json --out reproduced
```

The independent wrapper deliberately binds all three immutable original inputs by their SHA-256; it is **not** a validator for arbitrary GTFS feeds. The output directory must not already exist. The script checks bounded input sizes and reports its source license, actual geography IDs and scope. Exact checksums:

| Archive file | SHA-256 |
|---|---|
| gtfs.zip | `31bf6a9d37f9d8606c47d03be14022255b458308abd0f893c9a53ba2cc91e329` |
| upstream-report.json | `83f0aa6c60edb3a90d927b609ed4d5edb870bec1b0154ecd435971be8d225a9b` |
| upstream-system-errors.json | `823b06dada6cf539dde01b9451b5d2b6817ee7930f1ebeba4dc79d7688e79287` |
| gtfs_transit_study.py | `5cf59a543645ecd33d55e3cebfc5d366bf65471afd3b3d51ebf8e0844f59641d` |
| independent-report.json | `04813e2da88096a180a6cb1fc203fb83b010e681e963f6e49c727caf0398413d` |
| transit-patterns.svg | `d0bea8c993efeb91bb53ceabe5e6ed6a743d351892de1e41b80890e0a2a40b94` |

## Attribution and scope

Source: City of Manteca, California, [GTFS Data — October 1, 2026](https://www.manteca.gov/384/GTFS-Data), [original ZIP](https://www.manteca.gov/DocumentCenter/View/2279), accessed November 15, 2026, licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Original ZIP unchanged. Plenum derived validation summaries, selected and ordered route geometry, projected coordinates, and added color, labels and layout. The derivative SVG and data-derived summary are also distributed under CC BY 4.0; attribution retained. This independent work does not imply City endorsement. No private data, new service, paid inference, real-world transit changes or operational commitments are involved.
