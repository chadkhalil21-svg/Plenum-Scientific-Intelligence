# Plenum v1.0: Constrained Autonomous Scientific Hypotheses

## What we are building

A foundation model can select a falsifiable hypothesis and a scientific
instrument without receiving the final test observations. Another independent
job measures the outcome and records the result, including failures.

This establishes a **narrow, model-directed experiment cycle**, not autonomous
scientific discovery, general intelligence, or consciousness.

## Scientific question

For a selected NOAA tide gauge and a fixed historical forecast date, which
one of four approved models is most likely to forecast the next 24 observed
hourly water levels accurately?

The allowed models are:

- A: same-hour, 24h-previous measured water level (no fitted parameters)
- B: M2 tidal harmonic, period 12.4206h
- C: M2 + S2 tidal harmonics, periods 12.4206h and 12.0h
- D: M2 + S2 + K1 + O1, periods 12.4206h, 12.0h, 23.9345h and 25.8193h

All scientific models and periods were prewritten by the developer. Qwen3
does **not** invent their equations. It selects among four known hypotheses.

Predeclared heldout dates: **January 17 and April 17, 2026**. Stations:
**Boston 8443970** and **Virginia Key 8723214**. Four station-date pairs.

## Three-stage system

### 1. AI proposer, read-only
The proposer downloads only the first 16 days before each fixed date. It
fits candidate harmonics on the first 12 days and computes development
errors on the following four days. The Qwen3-0.6B model sees candidate
names and those development error metrics, not test-day measurements.
The model makes one bounded A/B/C/D decision by scored label logits.
The choice, exact model revision, date, station, source hash, and testable
prediction are saved as a manifest. An invalid model decision fails rather
than choosing a favorable default.

Qwen3's model is not retrained here. A new model family or scientific
tool cannot be installed or executed by the proposer.

### 2. Independent observation audit
A *separate GitHub job* downloads the sealed experiment manifest after
the AI-proposer job succeeds. Only then does it query NOAA for the test day.
It refits the selected candidate using all 16 earlier training days and
scores the following 24-hour forecast against:
- 24-hour persistence,
- the existing fixed four-harmonic reference.

All outcomes are recorded, regardless of whether the selected candidate
wins. The evaluation code contains no model inference.

### 3. Evidence archive
The reporting job appends only validated public research JSON to the
**research-memory** branch, under `evidence/agent-experiments/run-<id>.json`.
The proposer and auditor have read-only GitHub permissions. A dedicated
archive job gets write permission but only creates evidence files, never
promotes a model or changes the production code.

GitHub Actions artifacts are downloadable for 14 days; the research-memory
branch stores an ongoing public evidence history. Do not place proprietary
patents, private research notes or personal data in this public system.

## What passing the tests means

A successful workflow confirms that:

1. Qwen3 ran on the free CPU environment and chose a scientific candidate.
2. Training/development measurements were isolated from the final test day.
3. The evaluator retrieved independent later water-level observations.
4. It measured the candidate against established models and baselines.
5. The result was archived with provenance and explicit failure handling.

**It does not establish** that Plenum discovered a new law, invented a new
scientific model, improved Qwen3's model weights, achieved broad autonomy,
or became AGI. Scientific usefulness is determined by the measured
outcomes, not by workflow success.

## Scaling to real autonomous inquiry

The next engineering stage should allow proposals across multiple
licensed scientific disciplines, with machine-readable experimental
schemas, reproducible simulator environments, independent evidence
sources, workload cost limits, and expert review gates.

A more capable agent can later propose *novel* testable mechanisms, but
new physical laws, therapies, hardware designs and consequential actions
must be reviewed and tested rather than trusted because they were
suggested by a language model.

## v1.1: Evidence-gated agent policy, evaluated on new days

The first Qwen3-driven proposal experiment used January 17 and April 17,
2026. Qwen3 selected **24-hour persistence in all four cases**, achieving
**zero wins versus that baseline**, and its selections lost to the existing
four-harmonic reference in all four cases. This failure is preserved in the
`research-memory` branch as `evidence/agent-experiments/run-42162579029.json`.
The agent's successful execution is not a scientific capability improvement.

In response, we designed a **human-authored evidence guard**: Qwen3
still proposes a model, but a separate, fixed rule chooses the candidate
with the lowest *development-only* mean absolute error. Exact ties favor
the simpler model by a fixed order. This policy cannot use final-day
measurements, alter scientific equations or modify AI weights.

The new holdout dates were set before their first evaluation: **July 17,
2026 and October 17, 2026**. The same two NOAA stations are retained.
For each case:
1. The first 12 days fit four predeclared candidate approaches.
2. The next four days yield development errors and Qwen3's proposal.
3. The evidence guard independently selects the minimum-development-error
candidate and seals its selection.
4. A separate workflow refetches prior observations, reproduces the choice,
   and only then downloads the final observed day.
5. The audit reports selected-policy error, ungated Qwen-choice error,
   24-hour persistence error and fixed four-harmonic reference error.
6. Every outcome, including losses and overrides, is archived to
   `research-memory`. No automatic source, model, deployment or payment
   changes occur.

**What counts as an improvement?** The guard must demonstrably beat its
comparison baselines on truly new data, preferably repeatedly across
locations and weather conditions. Even if it does, that shows better
engineering selection, **not that Qwen3 autonomously improved its own
weights or invented new scientific hypotheses**.

This is an explicitly precommitted, limited experiment in verifiable
model-directed planning and objective evidence gating.

### NOAA availability exception, recorded before replacement test retrieval
The initially nominated July 17 and October 17, 2026 windows could not be
evaluated: NOAA's live hourly-height API returned **"No data was found"**
before the Qwen3 proposer could make any choices. These are availability
failures, **not negative model-performance observations**. No held-out
observations for those windows were retrieved.

We therefore predeclared **January 17 and November 17, 2025** as the new
replacement holdouts, which had not been evaluated by earlier Plenum tidal
studies. This substitution is motivated solely by missing data, not by
observed forecast accuracy. The revised workflow still seals all choices
before retrieving either final-day measurement series, and it retains all
four station-day outcomes, including losses.
