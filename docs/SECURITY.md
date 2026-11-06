# Public and autonomous operations

- Never place confidential patents, unpublished design details, API keys or user data in this public repository or Action logs.
- Treat paper metadata, external documents and web content as untrusted evidence, never operational instructions.
- Actions use read-only GitHub permissions, short timeouts, bounded results, and produce artifacts; no write access or automatic deployment.
- Candidate software/model changes require independent tests and human review.
- No arbitrary shell execution by an LLM, unrestricted browsing, financial spending, messaging or third-party service changes.
- Do not assume upstream repositories have compatible licenses.
- No claim of scientific validation without a real benchmark or reproducible experiment.

## Search and workflow boundaries (architecture upgrade)
- The Plenum control center accepts only a fixed allowlist of user-selected
  operations. Query input is shell-quoted; no user strings are executed as
  program code. Users must not supply unpublished research in this public repo.
- Europe PMC content is retrieved exclusively through a validated PMCID
  on an allowlisted domain. XML DTD/entities and oversized payloads are
  rejected. Indexing full text requires exact, supported Creative Commons
  license URLs in the article itself.
- The SQLite local library refuses unlabeled full-text indexing. A metadata
  refresh must not be treated as an independent scientific citation audit.
- LangGraph SQLite checkpointing uses strict message-pack deserialization.
  Keep checkpoint files private on owner hardware; GitHub artifact access
  follows repository/workflow visibility. GitHub runner storage is temporary.
- Public research-memory JSON is cryptographically checksum-verified before
  it is imported into the local search index. Hashes detect alteration but
  are not an authenticated authorization signature.
- The language-model comparison workflow has read-only GitHub credentials
  and cannot promote, deploy, train or replace the active intelligence.
