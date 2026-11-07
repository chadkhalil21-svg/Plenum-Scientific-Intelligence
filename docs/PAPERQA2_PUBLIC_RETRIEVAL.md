# PaperQA2 Public-Document Retrieval Pilot

The existing, pinned open-source PaperQA2 package is now used for a real
source-retrieval challenge rather than a package-import demonstration.

Two already-public Plenum research documents are indexed:
- NOAA empirical coastal-water-level forecasting (public project notes).
- PyBaMM battery-electrochemistry modeling (public project notes).

Each has one prespecified domain-specific question and an expected
original document. PaperQA2 reads the local documents and uses its
own SparseEmbeddingModel, not a custom Plenum retrieval engine.
The output records retrieved source IDs and exact SHA-256 input hashes.
External networking is denied during actual ingestion/retrieval.
No model, proprietary research data, credential, vector database subscription,
GPU, generated research answer or paid inference service is used.

Tests record top-one source correctness, including failures; a passing
workflow means the experiment ran, NOT necessarily that retrieval was right.
Two public document-selection questions are insufficient to establish
scientific reasoning, peer-reviewed discovery, citation hallucination rates
or AGI. PaperQA2 generative citation answers should be evaluated only after
a separately approved local LLM or costed provider and expert-labelled
rights-cleared papers are available.

Official upstream:
https://github.com/Future-House/paper-qa

## First independently scored result

The original frozen retrieval run [42340104253](https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42340104253) successfully executed the reviewed upstream library on the two existing public project documents. **Top-one correct source: 1 of 2.** The PyBaMM/SPM battery query returned the intended battery document, while the NOAA Boston/Virginia Key tide question incorrectly returned the battery document. The original output and input SHA-256 fingerprints are retained in workflow artifact `paperqa-original-public-retrieval-evidence`, ID 13561750015.

This is negative evidence for reliable two-source retrieval, not an AGI or citation-quality result. No model-generated answers were tested and no network connection or paid model inference was permitted. Any subsequent adaptation to these *inspected* questions is retrospective debugging, not a fresh heldout gain; future performance claims require a preregistered independent unseen document set and baseline comparison.
