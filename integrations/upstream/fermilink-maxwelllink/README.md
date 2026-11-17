# Isolated FermiLink / MaxwellLink baseline TLS adapter

Optional external execution only, not a copy of either upstream framework.
No upstream source, wheel or raw output CSV is redistributed in Plenum.
No automatic download, invocation, provider, model or paid API.

**Upstream rights and exact sources**

- FermiLink: Tao E. Li research group's [AGPL-3.0 repository](https://github.com/TaoELi/FermiLink), commit `1677243532ca1631750d5a62db9763c68291fddb`. Obtain the original `em.py` and `config.json` from [laser-tls-embedded](https://github.com/TaoELi/FermiLink/tree/1677243532ca1631750d5a62db9763c68291fddb/src/fermilink/tools/sci-skills-generator/assets/maxwelllink-skills-template/skills/mxl-project-scaffold/assets/templates/laser-tls-embedded). Retain upstream license and attribution. Cite [arXiv:2604.03460](https://arxiv.org/abs/2604.03460).
- MaxwellLink: [GPL-2.0 repository](https://github.com/TaoELi/MaxwellLink), release v0.5.0, commit `122d655b0a6c61209ca23ae28efc3621e5283c85`. Obtain its original `maxwelllink-0.5.0-py3-none-any.whl` through a trusted package index. Cite [arXiv:2512.06173](https://arxiv.org/abs/2512.06173). The wheel used in the original run contained 54 runtime Python files, whose Git blob hashes all matched the official tag.
- Any redistribution or integration of upstream source requires separate license review. Keep these assets outside the Plenum Git worktree. This adapter is an independent external launch boundary; no combined derivative is distributed here.

**Usage:** with local Python 3.11+, existing NumPy/SciPy dependencies:

```sh
python integrations/upstream/fermilink-maxwelllink/run_tls.py
# Explicit separately authorized run only
python integrations/upstream/fermilink-maxwelllink/run_tls.py --execute --inputs-dir /path/to/exact-upstream-assets
```

The default emits a plan only. The execute path accepts only the three exact
hash-pinned files, copies reviewed bytes into a private temporary directory, 
starts a credential-free POSIX process group with a 30-second timeout and
Python audit guards against socket/process operations, and writes only
the finite-data and physical-invariant receipt in
`reports/fermilink-maxwelllink-tls/`. It refuses overwrite and does not
pass arbitrary user commands. Python audit guards are defense-in-depth,
not a native OS sandbox.

The genuine original single run and its hash are recorded at
`evidence/fermilink/2026-11-17-tls/receipt.json`. It completed 1000 steps
with unit population conservation, valid density-matrix positivity
within floating-point error, and finite values. Because the original
xy drive is orthogonal to the z-oriented TLS, populations remained
constant. This is baseline evolution, not evidence of driven excitation,
scientific discovery, or AGI. The full FermiLink package was not installed,
and this is not its general autonomous agent harness.
