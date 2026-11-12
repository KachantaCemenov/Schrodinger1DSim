from pathlib import Path
import math
import re

import numpy as np
import pandas as pd

from BenchmarkResults import ReadBenchmarkManifest

SUMMARY_COLUMNS = ["problem",
                    "N",
                    "dt",
                    "method",
                    "runtime",
                    "max_L2_error",
                    "max_norm_error",
                    "max_energy_error",
                    "analytical_available",
                    "rows"]

def ReadRecommendationRuntime(path):
    #Read execution time
    text = Path(path).read_text(encoding="utf-8") #path to the runtime_data.txt
    runtimes = {}

    for method in ("CN", "SSF"):
        matches = re.findall(rf"^{method} runtime:\s*(\S+)\s+seconds\s*$", text, flags=re.MULTILINE)

        if len(matches) != 1:
            raise ValueError(f"Expected one {method} runtime in {path}.")

        value = float(matches[0])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{method} runtime must be finite and positive in {path}. A runtime rounded to zero cannot be ranked.")
        runtimes[method] = value
    return runtimes

def SummarizeBenchmarkCombination(folder, record, config, chunk_size=50_000):
    #One summary row per solver of one combination, no loading the full csv cus it may freeze the app

    run_folder = Path(folder).resolve()
    setting_folder = run_folder / record["folder"]

    csv_path = (setting_folder / "comparison_data.csv").resolve()
    runtime_path = (setting_folder / "runtime_data.csv").resolve()

    for path in (csv_path, runtime_path):
        if not path.is_relative_to(run_folder):
            raise ValueError("A result file points outside the run folder.")
        if not path.is_file():
            raise ValueError(f"Can not find any result files at {path}.")

    runtimes = ReadRecommendationRuntime(runtime_path) #get the runtime out

    dt = float(record["dt"])
    T = float(config["T_final"])
    ratio = final_time / dt

    if not math.isfinite(ratio) or ratio < 1:
        raise ValueError("Invalid final time or dt in the saved configuration.")
    expected_steps = round(ratio)
    if not math.isclose(ratio, expected_steps, rel_tol=0, abs_tol=1e-10):
        raise ValueError("Saved T_final is not a whole number of time steps.")

    #Get the fields out
    columns = ["step", "time"]
    for method in ("CN", "SSF"):
        columns.extend([f"{method}_norm", f"{method}_expected_energy", f"{method}_L2Error"])

    stats = {method: {"initial_norm": None, "initial_energy": None, "max_norm_error": 0.0, 
                      "max_energy_error": 0.0, "max_L2_error": 0.0, "l2_count": 0} for method in ("CN", "SSF")}
    row_count = 0

    #Inspect save file
    with pd.read_csv(csv_path, skiprows=1, usecols=columns, chunksize=chunk_size) as reader:
        for chunk in reader:
            if chunk.empty:
                continue
            # "N/A" is read as NaN
            chunk = chunk.apply(pd.to_numeric, errors="raise")

            steps = chunk["step"].to_numpy(dtype=float)
            times = chunk["time"].to_numpy(dtype=float)
            expected_sequence = np.arange(row_count, row_count + len(chunk))

            if not np.array_equal(steps, expected_sequence):
                raise ValueError(f"Missing, duplicate, or out-of-order steps in {csv_path}.")

            if not np.all(np.isfinite(times)) or not np.allclose(times, expected_sequence * dt, rtol=1e-10, atol=0):
                raise ValueError(f"Invalid time values in {csv_path}.")

            for method in ("CN", "SSF"):
                state = stats[method]
                norms = chunk[f"{method}_norm"].to_numpy(dtype=float)
                energies = chunk[f"{method}_expected_energy"].to_numpy(dtype=float)
                l2 = chunk[f"{method}_L2Error"].to_numpy(dtype=float)

                if (not np.all(np.isfinite(norms)) or not np.all(np.isfinite(energies))):
                    raise ValueError( f"{method} contains invalid norm or energy values in {csv_path}.")

                if state["initial_norm"] is None:      #There's no "initial_norm" in csv
                    state["initial_norm"] = float(norms[0])
                    state["initial_energy"] = float(energies[0])

                norm_drift = np.abs(norms - state["initial_norm"])
                energy_drift = np.abs(energies - state["initial_energy"])

                if not np.all(np.isfinite(norm_drift)) or not np.all(np.isfinite(energy_drift)):
                    raise ValueError(f"Overflow in drift values: {csv_path}")

                state["max_norm_error"] = max(state["max_norm_error"], float(norm_drift.max()))
                state["max_energy_error"] = max(state["max_energy_error"],float(energy_drift.max()))

                available_l2 = l2[~np.isnan(l2)] #save l2 values that are not NaN
                if available_l2.size:
                    if not np.all(np.isfinite(available_l2)) or np.any(available_l2 < 0)):
                        raise ValueError(f"Invalid {method} L2 errors in {csv_path}.")

                    state["max_L2_error"] = max(state["max_L2_error"], float(available_l2.max()))
                    state["l2_count"] += available_l2.size

            row_count += len(chunk)

    
    if row_count != expected_steps + 1:
        raise ValueError(f"Incomplete result table: {csv_path}\nExpected {expected_steps + 1} rows, found {row_count}.")
    declared_reference = record.get("analytical_available")  #Bool
    if declared_reference is not None and type(declared_reference) is not bool:
        raise ValueError("Invalid analytical_available field.")
    rows = []

    
    for method, state in stats.items():
        count = state["l2_count"]

        if count not in (0, row_count):
            raise ValueError(f"{method} has L2 errors missing for only some time steps in {csv_path}.")

        has_reference = count == row_count

        if declared_reference is not None and declared_reference != has_reference):
            raise ValueError(f"{method} L2 data disagrees with the manifest in {csv_path}.")

        rows.append({"problem": record["problem"],
                    "N": record["N"],
                    "dt": record["dt"],
                    "method": method,
                    "runtime": runtimes[method],
                    "max_L2_error": state["max_L2_error"] if has_reference else np.nan,
                    "max_norm_error": state["max_norm_error"],
                    "max_energy_error": state["max_energy_error"],
                    "analytical_available": has_reference,
                    "rows": row_count})

    if rows[0]["analytical_available"] != rows[1]["analytical_available"]:
        raise ValueError("Discrepancy in analytical-availability between CN and SSF")

    return rows

def BuildRecommendationSummary(folder, progress=None):
    #Read completed/ partial run, return manifest and summary
    folder = Path(folder).resolve()
    manifest = ReadBenchmarkManifest(folder)
    records = manifest["results"]
    rows = []

    for index, record in enumerate(records, start=1):
        if progress is not None:
            progress.put(f"Analyzing {index}/{len(records)}: {record['problem']}, N={record['N']}, dt={record['dt']:g}")

        config = manifest["configuration"]["problems"][record["problem"]]

        rows.extend(SummarizeBenchmarkCombination(folder, record, config))

    summary = pd.DataFrame(rows, columns=SUMMARY_COLUMNS)

    if not summary.empty:
        summary = summary.sort_values(["problem", "N", "dt", "method"], ignore_index=True)

    return manifest, summary

