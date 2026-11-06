"""Bounded numerical physics demonstrators with deterministic verification."""
import math


def diffuse_heat(initial=(0.0, 0.0, 100.0, 0.0, 0.0), alpha=0.0001,
                 dx=0.01, dt=0.1, steps=40):
    """Explicit finite-volume 1D heat equation with insulated ends.

    The model is dimensionless in temperature with alpha in m²/s and dx in m.
    No claim of real material performance is implied.
    """
    if len(initial) < 3 or len(initial) > 1001 or not 1 <= steps <= 20000:
        raise ValueError("Grid must have 3..1001 cells and steps 1..20000")
    if any(not math.isfinite(v) for v in (*initial, alpha, dx, dt)):
        raise ValueError("Inputs must be finite")
    if alpha <= 0 or dx <= 0 or dt <= 0:
        raise ValueError("alpha, dx and dt must be positive")
    c = alpha * dt / (dx * dx)
    if c > 0.5:
        raise ValueError("Unstable explicit time step; alpha*dt/dx² must be <= 0.5")
    grid = list(map(float, initial))
    total_before = math.fsum(grid)
    for _ in range(steps):
        nxt = [grid[0] + c * (grid[1] - grid[0])]
        nxt.extend(grid[i] + c * (grid[i-1] - 2*grid[i] + grid[i+1])
                   for i in range(1, len(grid)-1))
        nxt.append(grid[-1] + c * (grid[-2] - grid[-1]))
        grid = nxt
    total_after = math.fsum(grid)
    error = abs(total_after-total_before)
    tolerance = 1e-9 * max(1.0, abs(total_before))
    return {
        "model": "1D insulated heat diffusion, constant diffusivity",
        "parameters": {"alpha_m2_s": alpha, "dx_m": dx, "dt_s": dt, "steps": steps},
        "initial_profile": list(initial),
        "final_profile": grid,
        "verification": {"conserved_discrete_total": error <= tolerance,
                         "initial_sum": total_before, "final_sum": total_after,
                         "absolute_error": error, "stable_courant_ratio": c},
        "status": "numerical_model_only_not_material_validation",
    }
