# Precommitted USGS River-Flow Research | November 2026

**Status: a limited prospective research experiment, not AGI. No future test scores yet.**

## Verified independent observational source

This expands Plenum beyond its NOAA coastal water-level forecasting system to USGS measured daily mean river discharge. It uses the modern, supported USGS Water Data API v1 rather than the legacy NWIS WaterServices endpoint that will be retired.

Two stations have passed live, real-data checks on GitHub runners:
- Potomac River near Washington DC, Little Falls (01646500): 35 days of daily discharge, October 1 to November 4, 2026.
- Choptank River near Greensboro, Maryland (01491000): 35 days over the same interval.

Both datasets use USGS parameter 00060 (river discharge), statistic 00003 (daily mean), units cubic feet per second. The readings are provisional and may be revised. A Rappahannock gauge was excluded after the scientific data-quality check exposed incomplete development records.

## Registration, method, and two model families

The protocol was committed in advance at SHA 5599f4b8037e6d2a0dca78d0e3a03a034eb37c44, before any November 12 or 13 target observations were available.

- Historical development: October 1 to November 4, 2026.
- Two rolling validation folds: training through October 24 and validating November 1–2; training through October 26 and validating November 3–4.
- November 11, 2026 UTC: Qwen3-1.7B makes two model-generated forecasts, and independently trained SmolLM2-1.7B-Instruct makes two counterproposals.
- Future observed target days: November 12 and November 13, 2026.
- Independent audit no earlier than November 17, scheduled November 18 UTC.

All candidate hypotheses are numeric coefficients in a fixed seven-day-mean and damped-log-trend mixture, not independently invented physics. Baselines are latest training-day discharge, recent seven-day average and a damped 14-day trend. Selection is fixed before testing: only use Qwen or the independent critic if it beats the strongest baseline by at least five percent on BOTH validation folds. Otherwise select the baseline with the best average development score.

Both model forecasts and rejected candidates are kept. The separate scientific evaluator independently reproduces the development-series fingerprints, numerical scores and decision rule BEFORE requesting new held-out data. The original forecasts must have a Git commit timestamp prior to November 12 to be eligible for audit. Negative and missing results are reported, not fabricated.

## Run it from an iPad

GitHub > Actions > Prospective USGS Hydrology Scientific Transfer Test.

The workflow is scheduled for November 11 (proposal) and November 18 (audit). Manual dispatch is also date-gated. GitHub schedules can be delayed or skipped. Missed pre-test freezing makes the experiment ineligible for retrospective substitution.

## Strict limits

Two rivers and two adjacent target days provide only a small, correlated evaluation. River discharge and coastal water levels are distinct environmental forecasting problems, but are not evidence of broad cross-disciplinary AGI, a new physical law or recursive model self-improvement.

USGS observational revisions, missing daily measurements, invalid AI responses and altered scientific records cause explicit failures. No proprietary Plenum research, private credentials, paid inference services, GPU rentals, unrestricted generated-code execution or automatic production deployment are involved.

The next genuinely broader research milestone must test unrelated sciences (materials, chemistry, biology, mathematics or physics) with precommitted unseen tasks and independent scientific verification.
