# Independent Scientific Critic: Different-Family NOAA Review

## Status and meaning

This Stage 4 experiment adds a **distinct AI model family as a research critic**
of the already verified NOAA forecasting hypotheses, rather than merely
re-prompting Qwen3 as its own reviewer.

- Original proposer: pinned Qwen3-1.7B.
- Independent AI reviewer: pinned HuggingFaceTB/SmolLM2-1.7B-Instruct
  (Apache-2.0 licensed), immutable revision
  31b70e2e869a7173562077fd711b654946d38674.
- Scientific verifier: independent, model-free numerical code.
- Dataset: already-published, historical NOAA CO-OPS observations for the
  Boston and Virginia Key station-day cases in January and April 2026.
- Existing source record: research-memory/
  evidence/noaa-research-agent/run-42321911614.json, original commit
  4ccd3fcbd3634721b46d23967fb44bb356a4dc49.

**Important:** This is a RETROSPECTIVE model-criticism benchmark over data
that have already been publicly evaluated. It does not create new genuine
unseen observational evidence or establish prospective generalization.

## What runs and why

1. A model-free preparation worker reads Plenum's public historical record
   and produces a SANITIZED artifact containing only the prior model's
   signed development-case proposals. It does not hand the published
   independent-audit outcomes to the critic.
2. A separate critic worker checks out only the main source code and
   downloads only that sanitized artifact. It fetches development-only
   NOAA observations, checks the historic evidence integrity and source
   hashes, then asks SmolLM2 to challenge each original hypothesis with
   a continuous alternative to alpha and gain and a falsifier.
3. The critic's proposed alternative is evaluated numerically on development
   evidence alone. The fixed choice rule recommends a counterproposal
   only when it improves development MAE by at least 0.0001 meters.
   Invalid model output is recorded rather than replaced or promoted.
4. The independent, model-free audit verifies the original and critic
   development evidence and recommendation rule. Only AFTER that check
   does it query historical withheld NOAA observations and evaluate
   the original forecast, the critic alternative, the development-selected
   counterproposal and the strongest traditional benchmark.
5. Completed main-branch experiments are archived in the public
   research-memory branch, including failures.

## Use from an iPad

Actions > **Different-Family Scientific Critic of NOAA Research** > Run workflow.

No schedule is configured because repeating the same historical case
would not increase independent scientific evidence. No private company
research, credentials, proprietary patents, paid inference API or rented
GPU is involved.

## Scientific limits

This is independent MODEL criticism, **not independent peer review**
or independent laboratory validation. Both models can share pretraining
biases and the historical NOAA test observations were already public.
It is also limited to a reviewed harmonic/persistence blending formula.
It does not imply new physics, AGI, recursive self-improvement,
production model promotion or that any numerical suggestion is safe for
real-time weather or maritime navigation.

The next validation must precommit new observation windows, independently
chosen sites and longer blind evaluation horizons *before* observing
outcomes. A genuinely private continuously operating research agent would
also require owner-approved encrypted private storage, durable scheduling,
cost ceilings, access control, checkpoint recovery and external research
provenance. Do not put Plenum intellectual property into this public repo.
