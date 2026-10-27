from pathlib import Path
import pandas as pd

from ReadData import AnalyzeRun, GetLatestRun

def RecommendMethod(summary, problem, error_tolerance, error_metric = "max_L2_error"):   

    problem_data = summary[summary["problem"] == problem]
    valid = problem_data[problem_data[error_metric] <= error_tolerance]

    if valid.empty:
        return None
    best_index = valid["runtime"].idxmin()
    return valid.loc[best_index]

def BuildRecommendationTable(summary, problem, tolerances, error_metric = "max_L2_error"):
    rows = []

    for tolerance in tolerances:
        best = RecommendMethod(summary=summary,
                               problem=problem,
                               error_tolerance=tolerance,
                               error_metric=error_metric)
        if best is None:
            rows.append({
                "problem": problem,
                "tolerance": tolerance,
                "method": "None",
                "N": None,
                "dt": None,
                "runtime": None,
                "error": None
                })
        else:

            rows.append({
                "problem": problem,
                "tolerance": tolerance,
                "method": best["method"],
                "N": int(best["N"]),
                "dt": best["dt"],
                "runtime": best["runtime"],
                "error": best[error_metric]
            })

    return pd.DataFrame(rows)