# v0.9: A genuine observation-versus-prediction experiment

## Scientific question
Can a fixed four-constituent harmonic model, trained exclusively on
NOAA-measured hourly water levels from June 1 through June 16, 2025, predict
the following day's observed tide heights more accurately than a simple
same-hour, previous-day persistence baseline?

The experiment was specified before retrieving the final evaluation dataset.
It uses the two prespecified coastal stations Boston, MA (8443970) and
Virginia Key, FL (8723214). Neither station was selected after seeing model
accuracy.

NOAA observations and API documentation:
https://api.tidesandcurrents.noaa.gov/api/dev
https://tidesandcurrents.noaa.gov/stationhome.html?id=8443970
https://tidesandcurrents.noaa.gov/stationhome.html?id=8723214

## Prediction model
A fixed intercept and sine/cosine terms with periods:

- M2: 12.4206 hours
- S2: 12.0 hours
- K1: 23.9345 hours
- O1: 25.8193 hours

Nine parameters are estimated via NumPy least squares from 384 *observed*
hourly heights for June 1-16. Parameters are then frozen. Twenty-four hours
on June 17 are excluded from fitting and used to compute actual forecast error.

For each holdout hour, the baseline uses only the observed water level from
the same hour on June 16, so the baseline has no future-data advantage.

Both forecasts are scored on the **same 24 independently measured holdout
observations**, using mean absolute error (MAE) and root-mean-square error
(RMSE), in meters.

## Actual result

| NOAA gauge | Harmonic MAE | Persistence MAE | Relative MAE reduction |
|---|---:|---:|---:|
| Boston (8443970) | 0.323731 m | 0.340083 m | 4.81% |
| Virginia Key (8723214) | 0.065938 m | 0.086875 m | 24.10% |

For each station, the hypothesis was supported on the predeclared test day.

- Training observations: **384** at each station
- Heldout observations: **24** at each station
- Observation source: NOAA CO-OPS `hourly_height`, MLLW reference, GMT,
  metric units, public 2025 historical data
- GitHub run:
  https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42161428637
- Machine-readable evidence, exact metrics, observation fingerprints, source
  checksums and run commit:
  [evidence/noaa/2025-06-17.json](../evidence/noaa/2025-06-17.json)

## What is and is not verified
**Verified:** the pipeline fetched real tide-gauge observations, fitted the
predeclared mathematical model only on prior observations, forecast a
previously withheld day, and independently scored the predictions against
the withheld water levels. Both beat an appropriate fixed naive baseline.

**Not verified:** any new physics, general forecasting robustness,
a dependable operational flood-warning model, AI-generated scientific
invention, or increased AGI capability.

Only two locations and one holdout day were evaluated. The four tidal
periods are established physical knowledge, not independently invented by
the AI. Do not use this experimental implementation for navigation,
coastal flood safety, emergency planning, or operational predictions.

## Experimental discipline
The experiment was fixed and committed before the first attempt to retrieve
the holdout observations. The initial workflow failed because a *synthetic
failure-case unit test* assumed a water-level shock must harm the harmonic
model relative to persistence. Only that test was corrected by making its
synthetic persistence baseline exactly correct; the model, forecast date,
station IDs, harmonic periods and NOAA scoring remained unchanged.

The corrected source was verified on GitHub run 42161428637; its source
revision was `3591097d9b209f7083a6b8506eba7d1994298169`.

## Next necessary step
Establish a larger fully precommitted out-of-time study using several
different seasons, storms and coastal stations. Include observational
uncertainty, bootstrap intervals and a comparison against stronger
operational tide predictions. Keep all failures. Do not optimize to the
already-observed June 17 sample.

## Reproduction
```sh
python -m pip install -e ".[empirical]"
plenum empirical-tides --out reports/noaa_measured_tides.json
```

No paid API key is required. The NOAA service may have outages or rate
limits. Public workflows retain complete JSON artifacts for 14 days;
a compact summary is permanently archived under `evidence/noaa/`.

## v0.9b: Previously untested seasonal holdouts (three new dates)

After the June 17 run, we **kept the model unchanged** and specified
three additional future-to-the-training-window holdout days before
retrieving their NOAA observations:

- March 17, 2025
- September 17, 2025
- December 17, 2025

For each date, we independently fetched the preceding 16 days of observed
hourly water levels, fit the **same** four established tidal periods with
the **same** least-squares approach, and scored the following 24 hours
against the previous-day persistence baseline.

| Site and season | Harmonic model MAE | Baseline MAE | Harmonic won? |
|---|---:|---:|---|
| Boston, March | 0.21275 m | 0.27179 m | Yes |
| Virginia Key, March | 0.10695 m | 0.10471 m | **No** |
| Boston, September | 0.28466 m | 0.49067 m | Yes |
| Virginia Key, September | 0.06502 m | 0.09654 m | Yes |
| Boston, December | 0.30299 m | 0.27750 m | **No** |
| Virginia Key, December | 0.05996 m | 0.07150 m | Yes |

**Aggregate:** four wins, two losses across six station-days and 144
held-out observed hourly heights. Sample-weighted mean absolute errors:
**0.17205 m** (harmonic) versus **0.21878 m** (baseline),
a **21.36% lower aggregate MAE**. This is an observation-based
evaluation, not a generally proven forecast system.

- Successful fixed multi-season run:
  https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42161902806
- Source revision: `e3277dc93c96dc8c7e6e0c67f82534b97f2cde4e`
- Permanent, machine-readable station/day results and raw-source SHA-256:
  [evidence/noaa/2025-seasonal-independent.json](../evidence/noaa/2025-seasonal-independent.json)

The six NOAA datasets are real measurements rather than the provider's
predicted tide heights. Neither the model nor its established constituent
periods was invented by Plenum's foundation model. There was no test-based
parameter tuning. All failed station-days remain visible.

These results still cannot certify coastal forecasting or flood-warning
performance. The experiment excludes nonlinear hydrodynamics, changing
meteorology and uncertainty. Six station-days at two locations do not
represent independent region-wide samples or every season/weather condition.

### Reproduce
```sh
python -m pip install -e ".[empirical]"
plenum empirical-tides-seasons --out reports/noaa_seasonal_validation.json
```

The follow-on research program should compare against NOAA's operational
predictions, quantify confidence intervals, expand to geographically
independent stations, and hold out a **future** evaluation period.
