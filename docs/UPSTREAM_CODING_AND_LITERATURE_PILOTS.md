# Reuse-first AGI engineering: optional OpenHands and PaperQA2 pilots

## Implementation scope
This step checks real upstream public SDK exports, not general intelligence.

- OpenHands Software Agent SDK: MIT, version 1.60.1, Python >=3.12.
  The controlled test imports Agent, Conversation, LLM, Tool and
  AlwaysConfirm. No agent, workspace, terminal or external model runs.
- FutureHouse PaperQA2: Apache-2.0, version 2026.8.12, Python >=3.11.
  The controlled test imports Docs, Settings and ask without asking
  anything, indexing documents, generating embeddings, or calling models.

Separate optional dependencies are never installed by default. Separate
GitHub CPU jobs install them and test their exports. No credentials are
supplied and no confidential Plenum data is loaded. These checks consume
temporary CI minutes but make zero model/API calls.

## Requirements for actual proof-of-value pilots
OpenHands may run arbitrary commands in its workspace. Any coding experiment
must run on a disposable isolated worker, never the founder's main device or
production repository. Deny host credentials, restrict network, set
AlwaysConfirm and an explicit time/token/cost ceiling; review and test
generated changes before drafting a PR. Do not auto-merge or deploy.

PaperQA2 normally uses LLM and embedding services. The next experiment
must use legally accessible public scientific papers, known citation
reference answers, a separately approved model backend, and strict cost
and data boundaries. Compare source accuracy, unsupported assertions,
omissions, latency and cost against Plenum's existing research index.
Private corporate patent materials require a separate private runtime.

Both pilots are components of the research *infrastructure*. The still
unproven goals are stronger independent reasoning, long-horizon planning,
scientific discovery and safe measurable improvement. Preserve negative
results in the canonical research-memory ledger.

## What we should not rebuild
Existing LangGraph, Inspect AI, EleutherAI LM Evaluation Harness, SciPy,
RDKit, OpenMDAO, PyBaMM, OpenMM and existing verified adapters should
remain upstream libraries with narrow Plenum wrappers, not wholesale
repository copies. A component is retained only after evidence of value.
