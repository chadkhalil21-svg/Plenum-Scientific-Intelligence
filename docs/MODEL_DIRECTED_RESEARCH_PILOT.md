# Model-Directed Research Pilot

Status: **model-directed scientific software experiment, NOT AGI**.

## What is now implemented

This is a new step beyond the existing science demo and precommitted NOAA
experiment. A real pinned Qwen3-0.6B foundation model chooses among three
numerical methods after studying development-only SciPy solver results.
A **separate GitHub job** independently recomputes the development metrics
before running the holdout, which is a different predeclared domain.

The selected method is judged against RK45 and the strongest actual method.
Losses and ties are preserved. No code, model weights, or services are
autonomously changed; no paid inference API or GPU purchase is authorized.

The task is intentionally narrow: computational efficiency of numerical
solvers on known ordinary differential equations. It does not establish
a novel scientific law, an invention, long-horizon autonomous intelligence,
or a repeatable cross-domain improvement.

Public source metadata may be retrieved but is classified as untrusted
background information. It is not independent validation of claims and
cannot trigger new tools or executable instructions.

## Using it from an iPad

Go to the GitHub repository, select Actions, then select
**Model-Directed Cross-Domain Research Pilot** and **Run workflow**.
Provide a PUBLIC research question and choose a development domain.
The proposer and independent evaluator save separate downloadable reports.
A scheduled version uses a generic public question each Wednesday.
GitHub scheduled runs may be delayed or missed.

Successful runs on main archive the complete public reports (including
failures) on the separate research-memory branch, under
evidence/research-pilot. GitHub run artifacts expire after 14 days.

To try a stronger, owner-controlled model later, install Ollama and the model
on an authorized local machine, then run:

    python -m plenum_ai.research_pilot propose \
      --question "PUBLIC solver research" --domain materials \
      --engine ollama --ollama-model MODEL_NAME --out reports/pilot_proposal.json
    python -m plenum_ai.research_pilot audit \
      --proposal reports/pilot_proposal.json --out reports/pilot_audit.json

Ollama model use has not been configured or verified by this workflow.
Unpublished patents, confidential company research, credentials and private
messages must not be put in this public repository or in GitHub inputs.

## Moving toward much more capable autonomous intelligence

1. Benchmark stronger independent models on hidden, unfamiliar tasks across
   mathematics, engineering, life sciences, coding and the humanities.
2. Make agents propose original, typed scientific predictions and tests
   instead of choosing only among fixed numerical methods.
3. Add permitted research-paper full text and persistent private source-backed
   memory, with provenance, corrections and contradiction tracking.
4. Execute proposed software only in isolated, resource-limited environments,
   require independent tests, and submit reviewable changes before promotion.
5. Establish a separate always-on agent service only when measured reliability
   and cost per correct result justify dedicated private computing resources.

A SHA-256 seal is an integrity check, not an authenticated signature or
proof that the model independently invented an idea. The public benchmarks
may be familiar to a model and do not establish AGI or self-improvement.
