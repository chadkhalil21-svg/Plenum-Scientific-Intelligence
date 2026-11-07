# Precommitted Future NOAA Scientific Study

**Status:** scheduled research experiment. This is NOT AGI; no future test outcomes are yet available.

## Precommit and real-world measurements

The protocol was frozen in GitHub commit 45ac814869b9e47450c00ec55e83b29f02d3ca71 before the November 12–13, 2026 target observations occur.

- Public NOAA CO-OPS hourly measurements at Boston (8443970) and Virginia Key (8723214).
- Training/development dates: October 24 through November 8, 2026 UTC.
- Two rolling development folds: 11-day fit plus 2-day validation, and 13-day fit plus 3-day validation.
- Future test dates: November 12 and November 13, 2026 UTC, with an independent audit no earlier than November 15.
- Qwen3-1.7B proposes bounded numeric hypotheses, and independently trained SmolLM2-1.7B-Instruct proposes scientific counterhypotheses.
- The forecast formula is fixed. Neither model invents new physics or executes free-form generated code.
- The model is accepted only if it beats the strongest reference on BOTH development folds by at least 0.005 meters. Otherwise the predeclared baseline with the lowest average development error is selected.
- All original, critic and rejected candidates are retained for independent evaluation, including negative results.

## Fair forecasting baseline

The three comparison methods are a pattern repeating the last 24 hours of already-observed TRAINING data, a two-constituent harmonic model, and a four-constituent harmonic model. Crucially, none may use hourly observations from the days between the frozen proposal and the future test dates.

The two stations across two adjacent days yield four correlated station-day evaluations, not four independently replicated scientific experiments.

## Separate scheduled workflows

November 10, 2026 at 11:17 UTC: model jobs use development-only observations, then save an immutable frozen-forecast file on the separate public research-memory branch before the first test day. The model jobs are unable to request target observations through their approved source functions.

November 16, 2026 at 11:33 UTC: an independent job checks that the forecast was saved and committed before November 12, verifies rolling-fold measurements, and only then reads the target-day observations. Its complete results are archived separately. No model promotion or code changes occur.

These are date-gated GitHub Actions, not a persistent private AGI service. Delayed or missed GitHub scheduled tasks are possible. If the forecast was not frozen before the target day, the protocol must fail rather than create a retrospective substitute.

From an iPad: open Actions, then Prospective NOAA Research and Independent Model Criticism. Manual dispatch respects the same UTC date gates.

## Limitations and next tasks

This is a controlled test of narrow scientific forecasting across real environmental observations. Even genuine prospective accuracy gains would not prove AGI, autonomous invention or recursive self-improvement. A future independent-domain evaluation on fresh hydrology, air-quality or other licensed experimental data remains necessary.

The workflow does not use Plenum patents, private company data, paid hosted inference, unrestricted program execution or automatic production deployment.
