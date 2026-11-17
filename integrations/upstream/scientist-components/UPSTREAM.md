# Licensed components adapted into the existing upstream pilot

Only bounded deterministic routines from these two upstream repositories are
incorporated into `src/plenum_ai/upstream_pilots.py`. They are not full runtimes
or installed agent frameworks. No models, network, account, or write services are
connected by these components.

- FutureHouse Robin, Copyright 2025 FutureHouse, Apache License 2.0, pinned source
  [robin/utils.py](https://github.com/Future-House/robin/blob/4a5cce310f3bc7663a67117db88af43b84733ffe/robin/utils.py),
  function `uniformly_random_pairs`. Adaptation: local seeded PRNG, reject
  invalid/excessive input, retain uniform sample without replacement, emit
  scoped non-agent receipt. Original [license](LICENSE.ROBIN).
- MIT LAMM ScienceClaw, Apache License 2.0, pinned source
  [skills/sequence/scripts/sequence_tools.py](https://github.com/lamm-mit/scienceclaw/blob/894598cd3a90891a077c254566276bd379038bad/skills/sequence/scripts/sequence_tools.py),
  function `compute_stats` canonical DNA branch. Adaptation: only public
  literal canonical DNA; no file access, sequence detection, RNA/protein mode,
  synthesis, other upstream CLI features or import of the agent; validate
  optional Biopython==1.86 before import and emit scoped non-agent receipt.
  Original [license](LICENSE.SCIENCECLAW).

Full upstream Apache License texts are retained. The changes above are modified
source, not a claim of endorsement or reproduction of whole repositories.
