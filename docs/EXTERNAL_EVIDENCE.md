# Plenum v0.8: NASA catalog-based scientific model assessment

## Question being tested
Are orbital periods listed in NASA's public exoplanet catalog numerically
consistent with Keplerian periods calculated using catalog stellar masses
and semimajor axes?

The reference equation (planet mass neglected) is:

P = 2 * pi * sqrt(a^3 / (G * M_star))

The code uses **Astropy** constants and physical units rather than handcrafted
conversion factors. It retrieves at most 80 records from NASA's Planetary
Systems table through TAP, limiting records to positive, non-null parameters
and the default planetary solution.

Data source: https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html

## Verified output, 2026-11-05
GitHub Actions run: https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42160359555

- Catalog entries evaluated: **80**; entries rejected: **0**.
- Median absolute fractional period difference: **0.00159133 (0.159%)**.
- Fraction of catalog periods within 10% of the simple Keplerian estimate:
  **73/80 (91.25%)**.
- The NASA query and a deterministic SHA-256 fingerprint of the selected
  planet names are preserved with the report.
- GitHub Actions stores the downloadable full report as an artifact for 14 days.

## Critical scientific limitation
**This does not independently validate Kepler's law.** Some NASA catalog
semimajor axes are calculated using the periods and stellar masses, so
comparing the corresponding values can be circular. The catalog values also
have source uncertainties, and simple two-body calculations neglect planet
mass, additional companions, and other dynamics.

The verified outcome is **catalog parameter consistency and a working
NASA-to-Astropy computational pipeline**. No new astronomical discovery or
independent experimental result is established.

The next scientific phase should identify genuinely independent measured
quantities and provenance before adopting any hypothesis as tested.
It should also preserve observation uncertainties and analyze deviations
rather than silently removing them.

## Repeat
```sh
python -m pip install -e ".[astronomy]"
plenum nasa-exoplanets --out reports/nasa_exoplanet_consistency.json
```

No API key or paid astronomy service is required for this read-only public
TAP query. External service access is subject to NASA availability and terms.
