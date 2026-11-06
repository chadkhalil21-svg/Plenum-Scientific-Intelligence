"""NASA-origin OpenMDAO engineering adapter with strict, constant inputs.

The cooling-area fixture illustrates constrained multidisciplinary data flow.
It cannot validate real thermal or aircraft engineering without empirical inputs.
"""
import math

def optimize_cooling_area(thermal):
    if thermal.get("domain") != "materials" or not thermal.get("verified_fixture"):
        raise ValueError("Optimization requires an independently verified thermal fixture")
    measured = float(thermal["observed"])
    if not math.isfinite(measured) or not 300.0 < measured < 360.0:
        raise ValueError("Thermal state outside the approved model range")
    delta_t = measured - 300.0
    transfer_coefficient = 10.0  # W/(m2*K), illustrative assumption
    required_watts = 20.0       # W, illustrative requirement
    expected_area = required_watts / (transfer_coefficient * delta_t)
    import openmdao.api as om
    prob = om.Problem(reports=False)
    # No AI-generated expression is evaluated. This equation is part of reviewed code.
    prob.model.add_subsystem("cooler", om.ExecComp(
        "heat_watts = h * area_m2 * delta_t_k",
        h=transfer_coefficient, area_m2=1.0, delta_t_k=delta_t,
        heat_watts=0.0,
    ))
    prob.driver = om.ScipyOptimizeDriver()
    prob.driver.options["optimizer"] = "SLSQP"
    prob.model.add_design_var("cooler.area_m2", lower=0.01, upper=20.0)
    prob.model.add_constraint("cooler.heat_watts", lower=required_watts)
    prob.model.add_objective("cooler.area_m2")
    prob.setup()
    prob.set_val("cooler.area_m2", max(expected_area * 1.5, 0.02))
    try:
        fail = prob.run_driver()
        area = float(prob.get_val("cooler.area_m2").item())
        watts = float(prob.get_val("cooler.heat_watts").item())
    finally:
        prob.cleanup()
    check = (not fail and watts >= required_watts - 1e-5
             and abs(area - expected_area) < 1e-3)
    return {
        "tool": "openmdao.cooling", "library": "OpenMDAO + SLSQP",
        "status": "completed", "verified_fixture": bool(check),
        "dependent_input": "scipy.thermal.observed",
        "input_temperature_k": measured,
        "input_delta_t_k": delta_t,
        "heat_transfer_coefficient_w_m2_k": transfer_coefficient,
        "required_heat_rejection_w": required_watts,
        "optimized_area_m2": area,
        "analytical_minimum_area_m2": expected_area,
        "predicted_heat_rejection_w": watts,
        "limitations": "Constant-coefficient, lumped model, not a validated engineered cooling system",
        "scientific_discovery_verified": False,
    }
