import math
"""
This script is for validating time step 
"""

def CountTimeSteps(T_final, dt, max_steps = None):
    if not math.isfinite(T_final) or T_final <= 0:
        raise ValueError("T_final must be finite and positive.")

    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive.")

    ratio = T_final / dt

    if not math.isfinite(ratio):
        raise ValueError("T_final / dt is too large.")

    steps = round(ratio)

    # Allow small floating-point rounding differences.
    tolerance = max(1e-10, 8 * math.ulp(ratio))

    if steps < 1 or abs(ratio - steps) > tolerance:
        raise ValueError("T_final must be an integer multiple of dt.")

    if max_steps is not None and steps > max_steps:
        raise ValueError(f"This run exceeds the limit of {max_steps} time steps.")

    return steps