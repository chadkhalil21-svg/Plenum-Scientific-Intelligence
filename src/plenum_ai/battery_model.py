"""Optional, reproducible PyBaMM lithium-ion discharge demonstration.

Uses published PyBaMM SPM / SPMe default parameters, not any unpublished
Plenum battery design. Simulation results require independent cell measurements
before they can be used for performance or safety claims.
"""
from math import isfinite


def assess_voltage_samples(times, voltages, label):
    if len(times) < 4 or len(voltages) != len(times):
        raise ValueError("Too few synchronized battery simulation samples")
    if any(not isfinite(float(x)) for x in times + voltages):
        raise ValueError("Nonfinite simulation value")
    if any(b <= a for a, b in zip(times[:-1], times[1:])):
        raise ValueError("Time axis must be strictly increasing")
    start, end = float(voltages[0]), float(voltages[-1])
    if not (2.0 < start < 5.0 and 2.0 < end < 5.0):
        raise ValueError("Voltage outside bounded lithium-ion demonstration range")
    return {
        "model": label, "time_span_s": float(times[-1]-times[0]),
        "initial_voltage_v": start,
        "final_voltage_v": end,
        "voltage_drop_v": start - end,
        "voltage_finite_and_in_range": True,
        "declining_voltage_under_discharge": end < start,
        "sample_count": len(times),
        "independent_cell_validation": False,
    }


def simulate_discharge(minutes=10, model_names=("SPM", "SPMe")):
    import pybamm
    if not isinstance(minutes, int) or not 1 <= minutes <= 20:
        raise ValueError("Duration must be 1..20 whole minutes")
    if not model_names or len(model_names) > 2 or len(set(model_names)) != len(model_names):
        raise ValueError("Select one or two distinct approved models")
    models = {
        "SPM": pybamm.lithium_ion.SPM,
        "SPMe": pybamm.lithium_ion.SPMe,
    }
    if any(x not in models for x in model_names):
        raise ValueError("Unapproved battery electrochemical model")
    reports = []
    for label in model_names:
        model = models[label]()
        simulation = pybamm.Simulation(model)
        solution = simulation.solve([0, minutes*60])
        times = [float(x) for x in solution.t]
        voltages = [float(x) for x in solution["Voltage [V]"].entries]
        assessed = assess_voltage_samples(times, voltages, label)
        reports.append(assessed)
    return {
        "experiment": "PyBaMM default lithium-ion constant-current discharge",
        "pybamm_version": pybamm.__version__,
        "duration_requested_minutes": minutes,
        "models": reports,
        "simulation_completed": all(x["voltage_finite_and_in_range"] for x in reports),
        "predicted_voltage_decline": all(x["declining_voltage_under_discharge"] for x in reports),
        "actual_battery_cell_data_loaded": False,
        "experimentally_validated": False,
        "new_material_discovered": False,
        "safety_qualification": False,
        "limitations": [
            "Default parameterized lithium-ion models, not the Plenum battery patents.",
            "Numerically solved electrochemical equations are not independently measured capacity, degradation, safety or manufacturing evidence.",
            "Cross-model agreement alone is not empirical truth; compare against appropriately documented battery experiments.",
        ],
    }
