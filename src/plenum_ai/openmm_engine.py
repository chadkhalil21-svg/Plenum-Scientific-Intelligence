"""Isolated OpenMM CPU molecular-dynamics integration fixture.

A pair of synthetic particles joined by one harmonic bond. This verifies
OpenMM Reference-platform integration and physical unit handling, but it is
NOT protein folding, drug docking, biomolecular force-field validation or an
experimental molecular discovery.
"""
from math import isfinite, sqrt


def harmonic_energy(k_kj_mol_nm2, distance_nm, r0_nm):
    k, dist, r0 = map(float,(k_kj_mol_nm2,distance_nm,r0_nm))
    if not all(isfinite(v) for v in (k,dist,r0)) or not (0 < k <= 1e6 and 0 < dist <= 20 and 0 < r0 <= 20):
        raise ValueError("Bounded positive harmonic parameters required")
    return 0.5*k*(dist-r0)**2


def reference_diatomic(steps=100):
    if not isinstance(steps,int) or not 1 <= steps <= 250:
        raise ValueError("Must run 1 to 250 bounded molecular-dynamics steps")
    import openmm
    from openmm import unit, Vec3
    system=openmm.System()
    for _ in range(2):
        system.addParticle(39.948*unit.amu)
    bonds=openmm.HarmonicBondForce()
    bonds.addBond(0,1,0.35*unit.nanometer,
                  1000.0*unit.kilojoules_per_mole/unit.nanometer**2)
    system.addForce(bonds)
    integrator=openmm.VerletIntegrator(1*unit.femtosecond)
    context=openmm.Context(system,integrator,openmm.Platform.getPlatformByName("Reference"))
    try:
        context.setPositions([Vec3(0,0,0),Vec3(0.4,0,0)]*unit.nanometer)
        context.setVelocities([Vec3(0,0,0),Vec3(0,0,0)]*unit.nanometer/unit.picosecond)
        initial=context.getState(getEnergy=True,getPositions=True)
        p0=float(initial.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole))
        analytic=harmonic_energy(1000,0.4,0.35)
        if abs(p0-analytic)>1e-5:
            raise RuntimeError("OpenMM initial energy does not match independent harmonic reference")
        integrator.step(steps)
        end=context.getState(getEnergy=True,getPositions=True)
        positions=end.getPositions().value_in_unit(unit.nanometer)
        vector=positions[1]-positions[0]
        final_distance=sqrt(vector[0]**2+vector[1]**2+vector[2]**2)
        potential=float(end.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole))
        kinetic=float(end.getKineticEnergy().value_in_unit(unit.kilojoules_per_mole))
        drift=abs((potential+kinetic)-analytic)/analytic
        if not all(isfinite(x) for x in (potential,kinetic,final_distance,drift)):
            raise RuntimeError("Nonfinite molecular-dynamics state")
        if drift>0.01:
            raise RuntimeError("Energy conservation failed bound")
        return {
            "engine":"OpenMM",
            "engine_version":openmm.__version__,
            "platform":"Reference CPU",
            "experiment":"Synthetic two-particle harmonic bond in vacuum",
            "time_step_femtoseconds":1,
            "steps":steps,
            "initial_distance_nm":0.4,
            "equilibrium_distance_nm":0.35,
            "final_distance_nm":final_distance,
            "analytic_initial_potential_kj_mol":analytic,
            "computed_initial_potential_kj_mol":p0,
            "final_total_energy_kj_mol":potential+kinetic,
            "relative_total_energy_drift":drift,
            "numerical_fixture_passed":True,
            "real_molecular_forcefield_used":False,
            "protein_dynamics_validated":False,
            "biological_efficacy_validated":False,
            "scientific_discovery_verified":False,
            "external_or_paid_hardware_required":False,
            "limitations":[
                "Two simplified particles and a synthetic harmonic potential only.",
                "No solvent, thermodynamics, protein coordinates or calibrated molecular force-field.",
                "Numerical agreement is not an independent physical experiment."
            ],
        }
    finally:
        del context, integrator
