from pathlib import Path
import pandas as pd
import numpy as np

from ReadData import AnalyzeRun, GetLatestRun
"""
def RecommendMethod(summary, problem, error_tolerance, error_metric = "max_L2_error"):   

    problem_data = summary[summary["problem"] == problem]
    valid = problem_data[problem_data[error_metric] <= error_tolerance]

    if valid.empty:
        return None
    best_index = valid["runtime"].idxmin()
    return valid.loc[best_index]
"""
def RecommendMethod(summary, problem, N = None, dt = None, 
                    l2_tolerance = None, norm_tolerance = None, energy_tolerance = None):   
    """
    Find fastest configuration satisfying user constraints. 
    N = None -> all tested N allowed
    Similar for dt
    """
    valid = summary[summary["problem"] == problem].copy()
    
    if N is not None:
        valid = valid[valid["N"] == N]
    if dt is not None:
        valid = valid[np.isclose(valid["dt"], dt, rtol = 1e-10, atol = 0)]
    if l2_tolerance is not None:
        valid = valid[valid["max_L2_error"] <= l2_tolerance]
    if norm_tolerance is not None:
        valid = valid[valid["max_norm_error"] <= norm_tolerance]
    if energy_tolerance is not None:
        valid = valid[valid["max_energy_error"] <= energy_tolerance]
    if valid.empty:
        return None

    best_index = valid["runtime"].idxmin()
    return valid.loc[best_index]

def RecommendationToRow(best, problem, l2_tolerance=None, norm_tolerance=None, 
                        energy_tolerance=None, selected_N=None, selected_dt=None):

    if best is None:
        return {
            "problem": problem,

            "L2_tolerance": l2_tolerance,
            "norm_tolerance": norm_tolerance,
            "energy_tolerance": energy_tolerance,

            "selected_N": selected_N,
            "selected_dt": selected_dt,

            "method": "None",
            "N": None,
            "dt": None,
            "runtime": None,

            "max_L2_error": None,
            "max_norm_error": None,
            "max_energy_error": None
        }

    return {
        "problem": problem,

        "L2_tolerance": l2_tolerance,
        "norm_tolerance": norm_tolerance,
        "energy_tolerance": energy_tolerance,

        "selected_N": selected_N,
        "selected_dt": selected_dt,

        "method": best["method"],
        "N": int(best["N"]),
        "dt": best["dt"],
        "runtime": best["runtime"],

        "max_L2_error": best["max_L2_error"],
        "max_norm_error": best["max_norm_error"],
        "max_energy_error": best["max_energy_error"]
    }
"""
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
"""

def BuildRecommendationTable(summary, problem, requirements):
    rows = []

    for requirement in requirements:
        best = RecommendMethod(summary = summary, problem = problem,
                                N = requirement.get("N"), dt = requirement.get("dt"),
                                l2_tolerance = requirement.get("l2_tolerance"), norm_tolerance = requirement.get("norm_tolerance"),
                                energy_tolerance = requirement.get("energy_tolerance"))
        rows.append(RecommendationToRow(best = best, problem = problem, l2_tolerance = requirement.get("l2_tolerance"), 
                                        norm_tolerance = requirement.get("norm_tolerance"),
                                        energy_tolerance = requirement.get("energy_tolerance"),
                                        selected_N = requirement.get("N"), selected_dt = requirement.get("dt")))
    return pd.DataFrame(rows)



def BuildAllRecommendationTables(summary, requirements): #for all problems
    tables = []

    for problem in summary["problem"].unique():
        table = BuildRecommendationTable(summary = summary, problem = problem, requirements = requirements)

        tables.append(table)

    return pd.concat(tables, ignore_index = True)

def FindCN_PreferredSettings(summary, problem):
    data = summary[summary["problem"] == problem]

    cn = data[data["method"] == "CN"]
    ssf = data[data["method"] == "SSF"]

    merged = cn.merge(ssf, on = ["problem", "N", "dt"], suffixes = ("_CN", "_SSF"))
    preferred = merged[merged["max_L2_error_CN"] < merged["max_L2_error_SSF"]]
    return preferred[["N",
                    "dt",
                    "max_L2_error_CN",
                    "max_L2_error_SSF",
                    "runtime_CN",
                    "runtime_SSF"]]



if __name__ == "__main__":
    
    run_folder = GetLatestRun()
    summary = AnalyzeRun(run_folder)

    print(FindCN_PreferredSettings(summary, "PlaneWave_Free").to_string())
    #This 

    requirements = [
    {
        "l2_tolerance": 1e-2,
        "norm_tolerance": 1e-10
    },

    {
        "N": 1000,
        "l2_tolerance": 1e-3,
        "norm_tolerance": 1e-10
    },

    {
        "N": 2000,
        "dt": 1e-17,
        "l2_tolerance": 1e-3,
        "norm_tolerance": 1e-10,
        "energy_tolerance": 1e-24
    },
    {
        "N": 4000,
        "dt": 8e-17,
        "l2_tolerance": 8e-3
    },
    {
        "N": 2000,
        "dt": 4e-17,
        "l2_tolerance": 2,
    },
    {
        "N": 4000,
        "dt": 4e-17,
        "energy_tolerance": 0.5e-21
    }
    ]
    recommendations = BuildAllRecommendationTables(summary, requirements)
    print(recommendations)

    output_path = run_folder / "recommended_method.csv"
    recommendations.to_csv(output_path, index = False)
    print("\nSave recommendation table: ", output_path)