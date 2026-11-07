"""Official PySCF quantum-chemistry reference, isolated and bounded.

This only validates a standard two-hydrogen RHF/STO-3G numerical case. Not
a new quantum-chemistry method, chemical synthesis, pharmacology or AGI.
"""
from math import isfinite


def run_h2_reference():
    from pyscf import gto, scf
    from pyscf import __version__ as version

    if version != "2.15.0":
        raise RuntimeError("Reviewed PySCF 2.15.0 runtime required")

    def energy(distance):
        mol = gto.M(
            atom=[("H",(0.0,0.0,0.0)),("H",(0.0,0.0,distance))],
            basis="sto-3g", unit="Angstrom", charge=0, spin=0,
            verbose=0,
        )
        mf = scf.RHF(mol)
        mf.conv_tol = 1e-10
        total = float(mf.kernel())
        if not mf.converged or not isfinite(total):
            raise RuntimeError("The reference SCF did not converge")
        return total

    near = energy(0.74)
    stretched = energy(1.48)
    # Public, independently known numerical RHF/STO-3G reference energy
    # for H2 at an internuclear distance of 0.74 Angstrom.
    expected = -1.1167593073964255
    error = abs(near-expected)
    if error >= 1e-4 or not stretched>near:
        raise RuntimeError("Reference H2 quantum chemistry invariant failed")

    return {
        "schema":"plenum-pyscf-rhf-reference-v1",
        "engine":"PySCF","engine_version":version,
        "method":"restricted Hartree-Fock",
        "basis":"STO-3G","molecule":"H2",
        "bond_lengths_angstrom":[0.74,1.48],
        "total_energies_hartree":[near,stretched],
        "expected_0p74_hartree":expected,
        "absolute_numerical_error_hartree":error,
        "known_reference_passed":True,
        "stretch_raises_energy_in_this_fixture":True,
        "isolated_cpu_scientific_solver":True,
        "real_experimental_chemistry_verified":False,
        "novel_chemical_discovery":False,
        "drug_efficacy_established":False,
        "AGI_demonstrated":False,
        "limitations":"Two H atoms, minimal basis, fixed geometry and method; no independent physical experiment or new molecule."
    }
