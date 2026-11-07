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
