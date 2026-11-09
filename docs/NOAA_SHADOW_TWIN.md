# NOAA observational shadow-twin pilot: sensor updating without another simulator

**Status:** experimental historical replay **actually executed and passed** on real NOAA observations in GitHub Actions [run #42557644772](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42557644772). It is **not yet a live or operational digital twin**. This reuses the validated Plenum NOAA harmonic forecast code, observations and independent scoring, without adding another simulator, agent framework or paid service.

## Design and provenance

NIST emphasizes that a useful digital twin requires a model of a real counterpart, a method of acquiring observations and a method to update the virtual state. A credible deployment also requires validation and uncertainty quantification. Sources: https://www.nist.gov/digital-twins/essential-elements and https://www.nist.gov/publications/credibility-consideration-digital-twins-manufacturing .

The narrow prototype is a **two-station coastal water-level observational shadow model**. Sensors: Boston, MA (NOAA 8443970), and Virginia Key, FL (NOAA 8723214). Source: official public NOAA CO-OPS API `hourly_height` observed readings in meters, GMT, MLLW (https://tidesandcurrents.noaa.gov/web_services_info.html). Existing `noaa_empirical.py` downloads the original historical June 1–17, 2025 data with SHA-256 provenance and fits the fixed four established tidal constituent harmonic basis on June 1–16 only. It already withholds June 17 for independent historical forecasting.

`src/plenum_ai/noaa_shadow_twin.py` **does not refit** those harmonic coefficients, build its own physics solver or tune the holdout. It uses `score_station`'s trusted ordered frozen model outputs and simulates a low-cost sequential reading stream on June 17, updating only a single residual bias state after each observed hour:
`bias_next = (1 - 0.25) * bias_previous + 0.25 * (observed_water_level - frozen_harmonic_level)`.
The gain 0.25 is fixed and exploratory, **not calibrated** to this data. The prediction at hour `t+1` is `harmonic(t+1) + state_after_observing(t)` and must be recorded before reading the `t+1` target. The independent comparison uses the **same** target hours for (a) observationally updated shadow model, (b) original frozen harmonic model, (c) strong one-hour water-level persistence `observed(t)`. No success is forced; if the update loses, retain the loss.

The fixed June 2025 holdout has already been inspected in earlier Plenum science runs. Therefore the new online-bias variant is an **exploratory historical replay**, not a freshly preregistered prospective study. Synthetic fixtures validate chronology, missing data refusal, duplicate time refusal, no future-observation leakage and baseline-loss honesty; a separate live GitHub run should fetch actual NOAA observations and archive its results. Existing `noaa-empirical.yml` is extended, not replaced, to run the replay.

## Verified observed-data run (not a prospective discovery)

GitHub Actions [run #42557644772](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42557644772) **PASSED**: original frozen-model tests, five new no-leakage/failure/source-contract tests, fresh actual NOAA hourly-height API calls and both-station historical sensor replay. 384 training observations and 23 next-hour comparisons per station; raw source SHA-256 recorded in [permanent evidence](../evidence/noaa/2025-06-17-shadow-twin-replay.json).

| Gauge | Assimilated shadow MAE (m) | Frozen harmonic MAE (m) | One-hour persistence MAE (m) |
|---|---:|---:|---:|
| Boston | 0.3198791 | 0.3204208 | 0.4161739 |
| Virginia Key | 0.0625625 | 0.0657504 | 0.0961304 |

The bias update marginally improved the original harmonic baseline for both historical series, but Boston's advantage (about **0.54 mm MAE**) is negligible without uncertainty intervals or independent prospectively unseen datasets. Neither this small improvement nor the original fixed June 2025 result proves a continuously synchronized, calibrated digital twin. Full source-linked artifact is saved at [GitHub run #42557644772, artifact #13648390728](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42557644772/artifacts/13648390728).

## Acceptance and red lines

A reproducible successful **software/sensor-replay pilot** requires independent CI execution on actual NOAA data from both fixed stations, >=18 valid consecutive next-hour evaluations per station, recorded raw API fingerprints, no target leakage, finite numerical errors, comparison with stronger baselines, and an artifact preserving failures. Even a win is **not** a calibrated, continuous or operational digital twin.

**Not yet claimed:** fresh recurring sensor synchronization, quality-flag handling, measured uncertainty intervals, assimilation uncertainty, spatial hydrodynamic state reconstruction, independent flood warning accuracy, out-of-region transfer, prospective blind performance, or safe control/actuation. No claims about coastal navigation, emergency planning or human safety may be based on this model.

## Next *distinct* real twin gate

1. Wait for already preregistered Nov 12–13, 2026 NOAA measurements to be independently audited by the existing prospective NOAA workflow without reusing those outcomes for tuning.
2. Define a new future forecast issue cutoff, collect current `hourly_height` and NOAA official `predictions` as strong external comparator, enforce sensor freshness/quality/gap rejection, and issue immutable forecasts **before** the target observations arrive. Use NOAA's existing API, not a newly written hydrodynamic solver.
3. Report calibration, forecast interval coverage, sensitivity to weather residuals and same-horizon comparisons. Require several new geographical regions/seasons and verified continuous sync before upgrading from an observational *shadow* to a true research digital twin.
4. Only when a physics and data gap is demonstrated, evaluate an established coastal hydrodynamic model (or NOAA operational forecast products) under license and computational limits.

Run after installing existing optional dependencies:
```sh
python -m pip install -e ".[empirical]"
python -m unittest discover -s tests -p 'test_noaa_shadow_twin.py' -v
python -m plenum_ai.noaa_shadow_twin --out reports/noaa_shadow_twin.json
```

No new paid API key, GPU, private patent data, cloud deployment or background automation is required.

