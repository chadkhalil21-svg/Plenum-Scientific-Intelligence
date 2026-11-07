# Plenum: Iterative Scientific Hypothesis Laboratory (Stage 4 pilot)

**Status: experimental. NOT AGI, not a verified invention, not continuous autonomy.**

This extends the existing evaluated Qwen3 reasoning and LangGraph research ecosystem
without duplicating the orchestration stack. A pinned Qwen3-1.7B model makes
six real generation calls in one bounded run: two for each of three domains.

## What the agent does

1. **Observe:** The model sees simulated public synthetic time-series data,
   not experimental data from physical laboratories or Plenum patents.
2. **Propose:** It invents continuous numerical coefficients for the hypothesis
   dy/dt = a*y + b*y^2, with a and b in [-1,0], plus a falsifier.
   The *equation grammar and experimental setup are prewritten*. The model
   is proposing parameter values, not a new law or arbitrary program.
3. **Self-critique and revise:** A development-only evaluator measures whether
   the proposed equation predicts the next three available values; the same
   model sees a numerical feedback summary and may revise its coefficients.
   This is **not an independent AI critic**.
4. **Select:** A fixed rule accepts the round with lower development mean
   absolute error. Invalid JSON, unstable simulations and nonsensical
   parameter values are logged rather than silently replaced.
5. **Independent audit:** A separate GitHub job checks the sealed proposals,
   source values, the sequence of selected candidates and their scores.
   Only then does it compute withheld later observations and test predictions
   against independently train-fitted linear and quadratic reference models.
6. **Remember:** Completed main-branch runs append all public evidence,
   including failures, to research-memory/evidence/iterative-hypotheses.

**Domains:** simplified thermal cooling, chemical reaction kinetics and
electrical relaxation. All are synthetic ODE systems implemented in known
Python math, not new real-world measurements.

## iPad workflow

Repository > Actions > Iterative Cross-Discipline Scientific Hypothesis
Laboratory > Run workflow.

It also runs with generic PUBLIC fixtures once per month as a bounded,
potentially slow, free-runner test. GitHub schedules are not an always-on
computer and can be delayed, disabled or rate-limited.

No paid API service, model training, model promotion, external purchase,
unrestricted code execution or access to unpublished patents is activated.

## What passing means and does not mean

A passing workflow means model inference completed, proposals were recorded,
synthetic computations and selection rules independently reproduced, and
negative results were preserved. It **does not** mean the predictions were
accurate, that a scientifically novel mechanism was discovered, that the
agent can work across arbitrary unbounded disciplines, or that AGI exists.

The full independent audit includes (1) the count of valid candidate
hypotheses, (2) heldout accuracy, (3) wins against the strongest
train-fitted reference and (4) the failure and revision history.

## Next steps, evidence first

- Test on licensed real external observations in multiple independent
  laboratories, with blinding, precommitment and independent expertise.
- Expand from the fixed equation family to typed mathematical symbolic
  expressions, strictly sandboxed tool use and validated experimental
  proposals. Never treat generated code as trusted instructions.
- Add a genuinely independent critic or verifier, not merely a differently
  worded prompt to the same model.
- Evaluate many genuinely unseen tasks with confidence bounds and
  model/service cost per independently accepted solution.
- Deploy secure owner-approved private encrypted memory, GPU/CPU inference,
  state checkpoints, durable queues, cost limits, authorization and rollback
  only after infrastructure and privacy review.

Public repository workflows must never receive confidential Plenum Industries
patents, business plans, credentials, personal records or protected research.
