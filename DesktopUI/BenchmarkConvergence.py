import math
import pandas as pd

from Recommendation import SummarizeBenchmarkCombination

CONVERGENCE_QUANTITIES = {
    "Maximum L2 error": "max_L2_error",
    "Maximum norm drift": "max_norm_error",
    "Maximum energy drift": "max_energy_error",
}

CONVERGENCE_MODES = (
    "Vary dt (fixed N)",
    "Vary N (fixed dt)",
)

def BuildConvergenceData(folder, manifest, problem, mode, fixed_value, progress = None):
    #Read completed combinations for one problem and one fixed parameter
    if mode not in CONVERGENCE_MODES:
        raise ValueError("Unknown convergence plot mode.")
    problems = manifest["configuration"]["problems"]
    if problem not in problems:
        raise ValueError(f"Unknown benchmark problem: '{problem}'.")

    config = problems[problem]

    if mode == "Vary dt (fixed N)":
        fixed_field = "N"
        varying_field = "dt"
    else:
        fixed_field = "dt"
        varying_field = "N"

    fixed_number = float(fixed_value)
    if not math.isfinite(fixed_number) or fixed_number <= 0:
        raise ValueError("The fixed parameter must be finite and positive.")
    if fixed_field == "N" and not fixed_number.is_integer():
        raise ValueError("The fixed N must be an integer.")

    #Only use completed combinations in the manifest
    records = [record for record in manifest["results"] if record["problem"] == problem and float(record[fixed_field]) == fixed_number]
    records.sort(key = lambda record: float(record[varying_field]))

    if not records:
        raise ValueError("No completed combinations match this selection.")
    rows = []
    for index, record in enumerate(records, start=1):
        if progress is not None:
            progress.put(f"Reading {index}/{len(records)}: {problem}, N={record['N']}, dt={record['dt']:g}")

        rows.extend(SummarizeBenchmarkCombination(folder, record, config, read_runtime = False))

    columns = ["problem", "N", "dt", "method", "max_L2_error", "max_norm_error", "max_energy_error", "analytical_available"]

    data = pd.DataFrame(rows)[columns]

    return data.sort_values([varying_field, "method"], ignore_index = True)

def MakeConvergenceTable(data, mode, quantity):
    #One row per varying parameter, one column per solver
    if mode not in CONVERGENCE_MODES:
        raise ValueError("Unknown convergence plot mode.")
    if quantity not in CONVERGENCE_QUANTITIES:
        raise ValueError("Unknown convergence quantity.")

    varying_field = "dt" if mode == "Vary dt (fixed N)" else "N"
    metric = CONVERGENCE_QUANTITIES[quantity]

    table = data.pivot(index = varying_field, columns = "method", values = metric)

    table = table.reindex(columns = ["CN", "SSF"]).sort_index()
    table = table.rename(columns = {"CN": "Crank–Nicolson"})
    table.columns.name = None

    return table.reset_index()