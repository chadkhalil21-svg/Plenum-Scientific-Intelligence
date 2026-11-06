# Scientific Tool Registry and External Sources

**Policy:** link to upstream projects, install pinned reviewed packages as dependencies, and build narrow tested adapters. Do not copy bulk repositories or execute unreviewed skill instructions.

## Verified executable integrations
| Integration | What is actually executable | Status |
|---|---|---|
| SciPy | Newtonian orbit, thermal, first-order kinetics and RC numerical fixtures | Tested |
| RDKit | Known ethanol molecular structure descriptors | Tested |
| LangGraph 1.2.20 | Parallel per-tool workers (dynamic Send), fan-in, dependent stages | Tested in multi-tool Actions |
| OpenMDAO 3.45.2 | Constrained cooling-area optimization depending on verified SciPy thermal result | Tested |
| OpenAlex | Bounded scientific metadata | Live checked earlier |
| NASA Aviary 1.0.1 | Aircraft analysis package installation and official `aviary check` | Verified installation only (run 42159140408) |

## Public sources and curated references
- Federated metadata (OpenAlex, Europe PMC, Semantic Scholar): concurrent bounded requests, DOI-level deduplication, explicit provider failure reporting. Do not claim full-text access or bibliographic truth. Actual live provider success is established only by an Actions report.
- K-Dense [scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills): curated read-only skill catalog. Pinned upstream SHA `a25cf9ec00e2745d03f8704acf6f6919694ccd9a`. Skills are **untrusted Markdown** requiring individual license, security and dependency review before any installation.
- NASA [Aviary](https://github.com/OpenMDAO/Aviary): source SHA `c005ea797e6f67ba4098ed9624b9c8fa08961ff3` and installed published version `1.0.1`.
- NASA [GMAT](https://github.com/NASA/GMAT): mission-design engine; not installed or integrated in Plenum.
- [AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2): reference only pending custom-license and generated-code security review.
- [Stanford Biomni](https://github.com/snap-stanford/Biomni): candidate biomedical tools, not installed.
- [Karpathy AutoResearch](https://github.com/karpathy/autoresearch): architectural reference only; verify permission to reuse before copying.
- [Lean 4](https://github.com/leanprover/lean4): mathematical proofs, planned.
- [SU2](https://github.com/su2code/SU2): CFD, planned.
- [OpenMM](https://github.com/openmm/openmm): molecular dynamics, planned.
- [PySCF](https://github.com/pyscf/pyscf): quantum chemistry, planned.
- [PyBaMM](https://github.com/pybamm-team/PyBaMM): battery simulation, planned.
- [pymatgen](https://github.com/materialsproject/pymatgen): materials simulation, planned.
- [Astropy](https://github.com/astropy/astropy): astronomy, planned.
- [ToolUniverse](https://github.com/mims-harvard/ToolUniverse): biomedicine tools, planned.

## Reproducibility and permissions
- PyPI executable dependency pins: LangGraph 1.2.20 and OpenMDAO 3.45.2; check transitive versions from the workflow artifact.
- Upstream source revisions for auditing: LangGraph `5847733bcb186c26b32da5cc822eaf8a89deffeb`, OpenMDAO `c36ee430b71d6918daa5418bdaf1df70cef04102`. These are **source references**, not proof PyPI wheels correspond to those exact commits.
- No unrestricted dynamic Python, shell, privileged network operations, or self-deployment.
- Tests demonstrate fixed scientific examples, not validated novel inventions, clinical efficacy, general-purpose science modeling or AGI.
- Github Actions uses temporary public CPU environments; scale beyond these examples requires job scheduling, quotas and computing budgets.
