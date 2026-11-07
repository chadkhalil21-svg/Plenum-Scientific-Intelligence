# Real-Observation Scientific Hypothesis Cycle

**Stage 4 pilot:** model-generated continuous hypotheses tested on measured public observations. **Not AGI.**

This complements, rather than replaces, the existing synthetic hypothesis cycle and the NOAA fixed-menu forecasting pilot.

## What the real scientific agent does

- Sources genuine NOAA CO-OPS observed hourly water levels from the established, bounded, read-only NOAA adapter; two reviewed stations (Boston and Virginia Key) and two precommitted historical dates (January 17 and April 17, 2026).
- Fits fixed physical harmonic constituents on the earliest 12 days, with four subsequent development-only days.
- Uses pinned Qwen3-1.7B (exact SHA 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e) to generate continuous hypothesis parameters **alpha** and **gain** rather than select from a fixed menu.
- Independently measures the resulting MAE on development data and shows the same model its own first attempt and the baseline errors. The model may revise the parameters. This is **same-model self-critique**, not independent model criticism.
- Selects the lower development error from the two model attempts. It records invalid model outputs, rather than fabricating a fallback.
- Seals the development evidence and predictions, then sends them to a **separate, model-free evaluation job**. The auditor first checks source-data integrity, precommitted chronology, scores and selections. Only then does the audit worker fetch the previously withheld final day of measurements.
- Scores the frozen candidate against three independently recomputed models: 24-hour persistence, two-constituent harmonic and four-constituent harmonic. The best among these three is the reference. The full run is archived in the public research-memory branch, including losses and unverified hypotheses.

The model's prediction family is restricted to a prewritten blend of persistence and scaled harmonic forecasts. It is **not** inventing new governing equations, conducting physical laboratory experiments, proving generalizable scientific discovery, altering source code, self-training, or running as AGI.

## How to use it

From the public Plenum GitHub repository, open **Actions → Model-Revised Hypotheses on Real NOAA Observations → Run workflow**.

The workflow is deliberately not scheduled to repeat the same four historical tests indefinitely. Repeating fixed examples consumes compute without creating independent evidence. New studies should precommit new dates, stations and limits in a separately reviewed change before seeing their test measurements.

The proposer runs open-weight CPU inference and never needs access to the hidden test day. The auditor does not load the model. Invalid or unavailable NOAA sources cause a failed experiment instead of invented observations. Public data and model hypotheses only. No paid inference API, GPU provisioning, private research data, or production model promotion.

## What next for AGI?

Independent gains on *real* data are a useful milestone. They remain far from AGI. The next gates are broad unfamiliar-domain evaluations; licensed full-text scientific evidence retrieval with source checking and retractions; robust tool-use and test planning; a genuinely independent reasoning critic; long-running private agents with durable queues, encrypted storage and recovery; and independent demonstration of repeated capability gains without evaluation leakage.

Do not enter unpublished Plenum patents, confidential design information or private operational data in this public repository or its Actions inputs.
