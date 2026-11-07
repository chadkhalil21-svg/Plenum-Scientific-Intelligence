# PySCF real quantum chemistry reference

The founder asked to **integrate existing open-source scientific software now, without duplicating its physics**. We reused official [PySCF](https://pyscf.org) 2.15.0 (Nov 5, 2026; Apache 2.0) in an isolated GitHub CPU job, not on the user's iPad.

The fixed, fully specified case is two hydrogen atoms (H2), restricted Hartree-Fock, STO-3G basis, 0.74 Å internuclear spacing. It compares the result to a published conventional numerical reference (-1.1167593074 Hartree) and checks that stretching the bond to 1.48 Å raises the energy for this case. The independent test calls the **actual** PySCF package; no simulated/mock output is accepted on this job.

This does NOT verify a novel theory, full quantum chemical accuracy, physical experiments, drug efficacy, AGI, or machine consciousness. A real solver installation and a fixed reference numerical example are necessary but not sufficient for autonomous scientific discovery.

Optional dependency: `python -m pip install -e '.[chemistry]'`. The default project environment and unrelated CI do **not** install PySCF. To review the measured evidence, open Actions → **PySCF Real Quantum Chemistry Reference** and inspect the `real-pyscf-h2-quantum-chemistry-reference` artifact. No account credentials or paid API are required.

Future additions should select an independently sourced molecular challenge, genuine experimental validation and new mechanistic hypotheses, not repeatedly rerun this known reference as a discovery.
