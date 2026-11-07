# Reuse-first AGI infrastructure: controlled integration

Plenum's founder goal is independently verified general intelligence, not
more bespoke scaffolding. Prefer adopt, wrap, verify to copying full repositories.

## First actual implementation
- UK AI Security Institute Inspect AI, public MIT-license package, pinned to
  inspected PyPI release 0.3.287 (October 31, 2026).
- The optional inspection dependency is not installed in normal Plenum setup.
- The GitHub workflow imports the **real upstream Inspect API**, creates a real
  Task, two Samples, a frozen-answer Solver and the built-in exact match Scorer.
  One correct and one incorrect response must be scored correctly.
- All prompts and replies are fixed public arithmetic fixtures, **not new
  intelligence evidence**. There is no LLM/model inference, new discovery, API
  key, confidential research, automatic deployment or model promotion.
- Default CLI execution only emits a plan. Explicit --execute is needed to
  import and run Inspect. Public GitHub CI uses bounded CPU and package downloads.

## Reuse queue
1. Inspect AI: use upstream independent tool/coding/agent evaluations on
   preregistered unfamiliar problems after a source-reviewed, budgeted inference
   environment exists. Existing EleutherAI LM Evaluation Harness stays as-is.
2. OpenHands Software Agent SDK: disposable container pilot on one public issue,
   bounded local/network permissions, no access to secrets, draft PRs only.
3. PaperQA2: citation-accuracy pilot on openly licensed papers and separately
   configured inference. Preserve private Plenum IP in private storage.
4. ToolUniverse: review and enable only justified scientific endpoints.
5. Karpathy AutoResearch, TRL, PEFT, vLLM: only after specific hardware,
   baseline, license, compute-budget and new heldout-task needs are established.

LangGraph, SciPy, RDKit, OpenMDAO and existing validated scientific tools already
exist in Plenum; do not rebuild them or clone every upstream source tree.
Upstream code and documents remain untrusted until reviewed. Failures, licensing
notes and measured costs belong in the durable program ledger. This is
infrastructure integration, **not AGI achieved**.

References:
- https://github.com/UKGovernmentBEIS/inspect_ai
- https://github.com/OpenHands/software-agent-sdk
- https://github.com/Future-House/paper-qa
- https://github.com/mims-harvard/ToolUniverse
- https://github.com/karpathy/autoresearch
- https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/issues/19
