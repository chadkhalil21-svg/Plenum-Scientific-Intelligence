# External repository repair: reuse the official SWE-bench evaluator

**Purpose:** Replace tiny public Python function puzzles as the principal coding evidence
with genuine repository issue repair and the original upstream executable test harness.
**Status:** guarded integration and offline verification only. No agent has solved
an external issue through this integration; no new model calls and no AGI claim.

## The existing upstream tools, not bespoke substitutes

- Reuse the MIT-licensed [SWE-bench official benchmark and CLI](https://github.com/SWE-bench/SWE-bench), `swebench==5.0.2` (PyPI release August 18, 2026).
- Reuse a separately reviewed coding agent, such as
  [mini-SWE-agent](https://github.com/SWE-agent/mini-swe-agent) or the existing
  OpenHands SDK or Inspect ReAct. This integration does **not** implement a
  new coding agent, a replacement functional scorer, or an inference backend.
- Reference smoke example `sympy__sympy-20590` is named by the official upstream
  documentation. It is a **public historical task**, potentially contaminated.
- Original SWE-bench Verified evaluator scores patches from the
  original repository's issue-specific tests. Its benchmark is imperfect:
  correct solutions can sometimes be rejected. Any result should preserve
  source tests, original logs, baseline, and unresolved ambiguity.

## First use: preflight without inference, downloads or spending

Run `python -m plenum_ai.swebench_bridge --stage gold` to write an
offline-only command plan. Ordinary CI unit tests check limits, provenance,
secret filtering and fail-closed behavior and **never run Docker or any model**.

Actual official execution requires:
1. A dedicated disposable x86_64 Linux evaluation machine with at least
   **120 GiB free storage** and **16 GiB physical RAM**, Docker running,
   and permission to pull public benchmark images. These are upstream
   recommendations, not a promise that all individual builds fit.
2. Explicit owner consent to the machine, downloads, compute limits, and
   upstream task sources. Keep this isolated from secrets, production mounts
   and unpublished Plenum patents. The evaluation process may use the
   network to pull images; it is not claimed networkless.
3. Separately install `swebench==5.0.2` on that machine, review the upstream
   datasets and Docker tasks, then explicitly run
   `python -m plenum_ai.swebench_bridge --stage gold --execute --run-id plenum-reference-001`.
   It passes only the official CLI command using one worker, a 900-second
   per-task timeout, one instance and no shell.
4. Inspect the original `logs/evaluation/plenum-reference-001/results.json`,
   task logs, patch hash and resource consumption. An exit code **cannot**
   be converted into a passing grade.
5. Only then generate a candidate with a separately approved upstream
   coding agent. Place **one** valid SWE-bench JSONL record at
   `reports/swebench/predictions.jsonl` (model_patch, model_name_or_path,
   instance_id), and run the candidate stage with a **different unique**
   run ID, e.g. `--stage candidate --execute --run-id plenum-candidate-001`.
   Keep original tests, agent trajectory, tool use, pass/fail, cost, model
   version, negative examples and exact benchmark results separately.
   No auto merge, deployment, retraining, or model promotion.

SWE-bench caches by run ID and instance ID rather than patch hash.
**Never reuse a run ID with a different patch.** The bridge deliberately
does not claim a score until a person/independent audit reads the original
official results. With insufficient Docker resources, do not launch an
expensive run on a small GitHub-hosted runner simply to get a green check.

## Subsequent scientific and generalization gate

After the installation smoke, pre-register **newly discovered, dated, public
issues with independent tests** from legally reviewable repositories.
Run matched direct/agentic baselines on the same issue with identical model,
time, tokens and compute ceilings. Keep failures and human feedback, don't
select only solved issues, and verify improvements on future unseen tasks.
For broader general intelligence, require independent gains in mathematics,
new scientific hypotheses, grounded literature research, multimodal
reasoning and long-horizon planning, not only code repair.

Original upstream documentation:
- https://www.swebench.com/SWE-bench/reference/cli/
- https://www.swebench.com/SWE-bench/reference/harness/
- https://pypi.org/project/swebench/5.0.2/
- https://github.com/SWE-agent/mini-swe-agent
