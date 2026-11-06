# Persistent scientific research memory

The separate, public research-memory branch archives small checksum-addressed JSON records. Each record includes public questions, OpenAlex metadata, workflow code SHA, time, simulation-check status, and narrow improvement-audit results.

The Autonomous Research workflow reads memory from earlier runs, searches new public literature, runs bounded tests, and creates a report. A separate job with contents-write permission validates the checksum and commits metadata ONLY to the research-memory branch. Main source code is never automatically modified.

The checksum detects altered JSON content; it does not authenticate authors, prove scientific truth, or prevent an authorized GitHub user from rewriting branch history. Model-produced hypotheses are not published as confirmed discoveries or automatically retrained on.

The existing self-improvement evaluation measures a trivial synthetic phrase-ranking parameter on two distinct, frozen 12-example datasets. An independent implementation recomputes metrics. This is an engineering practice demonstration, not AGI or scientific discovery.

Do not enter confidential ideas, unpublished patents, patient information, credentials, or proprietary information into public GitHub Actions. A continuously running private research agent needs separate authenticated hosting and a protected knowledge store.
