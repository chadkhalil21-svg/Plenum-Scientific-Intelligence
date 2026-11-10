"""One NEW Plenum/PyBaMM first-use integration: change current, run real SPM.

This imports the exact already-declared upstream battery extra. Its purpose is
to close the "source indexed, solver never executed" gap. It is a lightweight
physical consistency check, not a calibrated battery or novel science.

Original reference: https://docs.pybamm.org/en/pybamm-v26.10.1.1/
source/examples/notebooks/getting_started/tutorial-4-setting-parameter-values.html
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def run_spm_first_use() -> dict:
    import numpy as np
    import pybamm

    model_name = "Single Particle Model (SPM)"
    parameter_set = "Chen2020"
    duration_s = 300.0
    requested_currents_A = (1.5, 3.0)
    outcomes = []
    for applied_A in requested_currents_A:
        # Each run is a REAL PyBaMM physics solve; no scraped results or agent
        # text, and no external provider, API key, GPU or model inference.
        parameters = pybamm.ParameterValues(parameter_set)
        parameters["Current function [A]"] = applied_A
        simulation = pybamm.Simulation(
            pybamm.lithium_ion.SPM(), parameter_values=parameters
        )
        solution = simulation.solve(
            t_eval=np.linspace(0.0, duration_s, 31)
        )
        t_s = np.asarray(solution["Time [s]"].entries, dtype=float).reshape(-1)
        amps = np.asarray(solution["Current [A]"].entries, dtype=float).reshape(-1)
        volts = np.asarray(solution["Voltage [V]"].entries, dtype=float).reshape(-1)
        discharged_Ah = np.asarray(
            solution["Discharge capacity [A.h]"].entries, dtype=float
        ).reshape(-1)
        if not (
            len(t_s) == len(amps) == len(volts) == len(discharged_Ah)
            and len(t_s) >= 5
            and all(np.all(np.isfinite(x)) for x in (t_s, amps, volts, discharged_Ah))
        ):
            raise RuntimeError("Malformed or nonfinite PyBaMM solver output")
        if np.any(np.diff(t_s) <= 0) or t_s[0] < -1e-8:
            raise RuntimeError("Nonmonotone solver timeline")
        # Independent analytic constant-current integral from the ACTUAL output
        # samples, instead of trusting the model's discharge-capacity variable.
        amp_hours_from_current = float(np.sum((amps[:-1] + amps[1:]) * np.diff(t_s) / 2.0) / 3600.0)
        model_discharge_Ah = float(discharged_Ah[-1] - discharged_Ah[0])
        reference_Ah = float(applied_A * (t_s[-1] - t_s[0]) / 3600.0)
        current_error = float(np.max(np.abs(amps - applied_A)))
        balance_error_Ah = abs(model_discharge_Ah - amp_hours_from_current)
        reference_error_Ah = abs(reference_Ah - amp_hours_from_current)
        voltage_bounds_pass = bool(np.min(volts) > 2.0 and np.max(volts) < 5.0)
        ok = bool(
            abs(t_s[-1] - duration_s) <= 1.0
            and current_error < 0.015
            and balance_error_Ah < 0.001
            and reference_error_Ah < 0.001
            and model_discharge_Ah > 0
            and voltage_bounds_pass
        )
        outcomes.append({
            "applied_current_A": applied_A,
            "simulated_duration_s": float(t_s[-1] - t_s[0]),
            "sample_count": int(len(t_s)),
            "terminal_voltage_start_V": float(volts[0]),
            "terminal_voltage_end_V": float(volts[-1]),
            "discharged_Ah_reported_by_PyBaMM": model_discharge_Ah,
            "independently_integrated_current_Ah": amp_hours_from_current,
            "analytical_constant_current_Ah": reference_Ah,
            "current_max_abs_error_A": current_error,
            "capacity_balance_abs_error_Ah": balance_error_Ah,
            "voltage_bounded": voltage_bounds_pass,
            "physical_conservation_check_passed": ok,
        })

    ratio = (
        outcomes[1]["discharged_Ah_reported_by_PyBaMM"]
        / outcomes[0]["discharged_Ah_reported_by_PyBaMM"]
    )
    changed_input_consistent = (
        math.isfinite(ratio)
        and abs(ratio - requested_currents_A[1] / requested_currents_A[0]) < .035
        and all(x["physical_conservation_check_passed"] for x in outcomes)
    )
    return {
        "schema": "plenum-pybamm-real-spm-first-use-v1",
        "status": ("PYBAMM_REAL_PHYSICS_CHECK_PASS" if changed_input_consistent
                   else "PYBAMM_PHYSICS_CHECK_FAILED"),
        "library": "PyBaMM",
        "upstream_repository": "pybamm-team/PyBaMM",
        "upstream_version": str(pybamm.__version__),
        "model": model_name,
        "parameter_set": parameter_set,
        "solver_ran": True,
        "independent_check_method": "Analytical I*t/3600 and independent trapezoidal current integration",
        "cases": outcomes,
        "changed_input_capacity_ratio": float(ratio),
        "changed_input_check_passed": bool(changed_input_consistent),
        "actual_external_cell_measurements": False,
        "external_experiment_validation": False,
        "novel_battery_discovery": False,
        "agent_model_inference_calls": 0,
        "private_accounts_accessed": False,
        "paid_api_used": False,
        "limitation": "Idealized known SPM with Chen2020 parameters; checks only short-duration self-consistency, not cell performance/life or external empirical validity.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="reports/pybamm-spm-first-use.json")
    args = parser.parse_args()
    dst = Path(args.out)
    if (dst.is_absolute() or ".." in dst.parts or not dst.parts
            or dst.parts[0] != "reports" or dst.suffix != ".json"):
        parser.error("Output must be a relative JSON file under reports/")
    result = run_spm_first_use()
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"])
    if result["status"] != "PYBAMM_REAL_PHYSICS_CHECK_PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
