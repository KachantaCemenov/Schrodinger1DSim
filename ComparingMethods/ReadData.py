from pathlib import Path
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np

BASE_FOLDER = Path(__file__).resolve().parent
RESULTS_FOLDER = BASE_FOLDER / "Results"

def GetLatestRun():
    runs = [folder for folder in RESULTS_FOLDER.iterdir() 
            if folder.is_dir() and folder.name.startswith("run_")]
    if not runs:
        raise FileNotFoundError("No run folders found")
    #timestamp format: run_YYYY_MM_DD_HH-MM-SS 
    latest_run = max(runs, key = lambda folder: folder.name)
    return latest_run

def SavePlot(problem_folder: Path, category: str, metric: str, filename: str):
    run_folder = problem_folder.parent

    graph_folder = run_folder / "Graphs" / problem_folder.name / category / metric
    graph_folder.mkdir(parents = True, exist_ok = True)

    graph_path = graph_folder / f"{filename}.png"
    plt.savefig(graph_path, dpi = 100, bbox_inches = "tight")
    print("Save: ", graph_path)


def ReadSetting(setting_folder: Path):
    comparison_path = setting_folder / "comparison_data.csv"

    data = pd.read_csv(comparison_path, skiprows = 1) #skip first row
    
    #add to data
    #change at each step
    data["CN_delta_norm"] = data["CN_norm"].diff().fillna(0)
    data["SSF_delta_norm"] = data["SSF_norm"].diff().fillna(0)
    data["CN_delta_energy"] = data["CN_expected_energy"].diff().fillna(0)
    data["SSF_delta_energy"] = data["SSF_expected_energy"].diff().fillna(0)

    #Relative change to initial value
    data["CN_norm_error"] = abs(data["CN_norm"] - data["CN_norm"].iloc[0])
    data["SSF_norm_error"] = abs(data["SSF_norm"] - data["SSF_norm"].iloc[0])
    data["CN_energy_error"] = abs(data["CN_expected_energy"] - data["CN_expected_energy"].iloc[0])
    data["SSF_energy_error"] = abs(data["SSF_expected_energy"] - data["SSF_expected_energy"].iloc[0])

    return data


#Use regular expression to look for the numbers in the text
#Look up: https://www.w3schools.com/python/python_regex.asp

def ReadRuntime(setting_folder: Path):

    runtime_path = setting_folder / "runtime_data.txt"
    text = runtime_path.read_text()


    cn_match = re.search(r"CN runtime:\s*([\d.]+)",text)

    ssf_match = re.search(r"SSF runtime:\s*([\d.]+)",text)

    cn_runtime = float(cn_match.group(1))
    ssf_runtime = float(ssf_match.group(1))

    return cn_runtime, ssf_runtime

def AnalyzeSetting(setting_folder: Path):

    data = ReadSetting(setting_folder)
    cn_runtime, ssf_runtime = ReadRuntime(setting_folder)

    #Extract the number N and dt from folder name
    match = re.fullmatch(r"N(\d+)_dt([0-9.eE+-]+)", setting_folder.name) 

    if match is None:
        raise ValueError(f"Invalid setting folder name: {setting_folder.name}")
    N = int(match.group(1))
    dt = float(match.group(2))

    cn_result = {
        "N": N,
        "dt": dt,
        "method": "CN",
        "runtime": cn_runtime,
        "final_L2_error": data["CN_L2Error"].iloc[-1],
        "max_L2_error": data["CN_L2Error"].max(),
        "mean_L2_error": data["CN_L2Error"].mean(),
        "max_norm_error": data["CN_norm_error"].max(),
        "max_energy_error": data["CN_energy_error"].max(),
        "max_delta_norm": abs(data["CN_delta_norm"]).max(),
        "max_delta_energy": abs(data["CN_delta_energy"]).max()
    }

    ssf_result = {
        "N": N,
        "dt": dt,
        "method": "SSF",
        "runtime": ssf_runtime,
        "final_L2_error": data["SSF_L2Error"].iloc[-1],
        "max_L2_error": data["SSF_L2Error"].max(),
        "mean_L2_error": data["SSF_L2Error"].mean(),
        "max_norm_error": data["SSF_norm_error"].max(),
        "max_energy_error": data["SSF_energy_error"].max(),
        "max_delta_norm": abs(data["SSF_delta_norm"]).max(),
        "max_delta_energy": abs(data["SSF_delta_energy"]).max()
    }

    return cn_result, ssf_result


def AnalyzeProblem(problem_folder : Path):
    res = []

    for setting_folder in problem_folder.iterdir():
        

        cn_res, ssf_res = AnalyzeSetting(setting_folder)
        cn_res["problem"] = problem_folder.name
        ssf_res["problem"] = problem_folder.name

        res.append(cn_res)
        res.append(ssf_res)

    summary = pd.DataFrame(res)
    summary = summary.sort_values(by=["N", "dt", "method"])

    return summary

def AnalyzeRun(run_folder: Path):
    all_res = []

    for problem_folder in run_folder.iterdir():

        if not problem_folder.is_dir():
            continue
        if problem_folder.name == "Graphs":
            continue

        problem_sum = AnalyzeProblem(problem_folder)
        all_res.append(problem_sum)

    #https://pandas.pydata.org/docs/reference/api/pandas.concat.html
    summary = pd.concat(all_res, ignore_index = True)

    return summary


def GetMetricColumns(metric):

    metrics = {
        "L2": (
            "CN_L2Error",
            "SSF_L2Error",
            "L2 Error"
        ),

        "norm_error": (
            "CN_norm_error",
            "SSF_norm_error",
            "Norm Error"
        ),

        "energy_error": (
            "CN_energy_error",
            "SSF_energy_error",
            "Energy Error"
        ),

        "delta_norm": (
            "CN_delta_norm",
            "SSF_delta_norm",
            "Change in Norm/ step"
        ),

        "delta_energy": (
            "CN_delta_energy",
            "SSF_delta_energy",
            "Change in Energy/ step"
        )
        }

    if metric not in metrics:
        raise ValueError(
            f"Unknown metric: {metric}"
        )

    return metrics[metric]


#PLOTTING FUNTIONS 

#Look into one problem (fixed N fixed dt) csv file and plot the error in that as step propagate 
def PlotMetric_vs_Time(setting_folder, metric = "L2"): 
    data = ReadSetting(setting_folder)

    cn_col, ssf_col, ylabel = GetMetricColumns(metric)

    plt.figure(figsize=(7,5))

    plt.plot(data["time"], data[cn_col], label = "CN")
    plt.plot(data["time"], data[ssf_col], label = "SSF")

    plt.xlabel("Time")
    plt.ylabel(ylabel)

    plt.title(f"{ylabel} vs time\n"
              f"{setting_folder.name}")

    plt.legend()
    plt.grid()

    SavePlot(setting_folder.parent, "VsTime_in_each_setting", metric, f"{metric}_vs_time_{setting_folder.name}")

    plt.close()

#Look into all setting folders with fixed N and plot them as dt change
#arg stat is to use the maximum error or the final error in each N, dt configuration
def PlotMetric_vs_Dt(problem_folder, fixed_N, metric = "L2", stat = "max"): #max or final
    row = []

    for setting_folder in problem_folder.iterdir():
        
        match = re.fullmatch(r"N(\d+)_dt([0-9.eE+-]+)", setting_folder.name)
        if match is None:
            continue

        N = int(match.group(1))
        dt = float(match.group(2))

        if N != fixed_N:
            continue

        data = ReadSetting(setting_folder)
        cn_col, ssf_col, ylabel = GetMetricColumns(metric)

        if stat == "max":
            cn_value = abs(data[cn_col]).max()
            ssf_value = abs(data[ssf_col]).max()
        elif stat == "final":
            cn_value = abs(data[cn_col]).iloc[-1]
            ssf_value = abs(data[ssf_col]).iloc[-1]
        else:
            raise ValueError("Wrong stat parameter")

        row.append({
                "dt": dt,
                "CN": cn_value,
                "SSF": ssf_value
            })

    res = pd.DataFrame(row).sort_values("dt")

    plt.figure(figsize=(7,5))
    plt.plot(
        res["dt"],
        res["CN"],
        marker="o",
        label="Crank-Nicolson"
    )

    plt.plot(
        res["dt"],
        res["SSF"],
        marker="o",
        label="Split-Step Fourier"
    )

    plt.xlabel("dt")
    plt.ylabel(f"{stat.capitalize()} {ylabel}")

    plt.title(
        f"{stat.capitalize()} {ylabel} vs dt"
        f"\nN = {fixed_N}"
    )

    plt.legend()
    plt.grid()

    SavePlot(problem_folder, "VsDt_in_problem", metric, f"{metric}_{stat}_vs_dt_N{fixed_N}")

    plt.close()

#Same as above, reverse (fixed dt changing N) . TODO: consider joining these two methods
def PlotMetric_vs_N(problem_folder, fixed_dt, metric = "L2", stat = "max"): #max or final
    row = []

    for setting_folder in problem_folder.iterdir():
        
        match = re.fullmatch(r"N(\d+)_dt([0-9.eE+-]+)", setting_folder.name)
        if match is None:
            continue

        N = int(match.group(1))
        dt = float(match.group(2))

        if dt != fixed_dt:
            continue

        data = ReadSetting(setting_folder)
        cn_col, ssf_col, ylabel = GetMetricColumns(metric)

        if stat == "max":
            cn_value = abs(data[cn_col]).max()
            ssf_value = abs(data[ssf_col]).max()
        elif stat == "final":
            cn_value = abs(data[cn_col]).iloc[-1]
            ssf_value = abs(data[ssf_col]).iloc[-1]
        else:
            raise ValueError("Wrong stat parameter")

        row.append({
                "N": N,
                "CN": cn_value,
                "SSF": ssf_value
            })

    res = pd.DataFrame(row).sort_values("N")

    plt.figure(figsize=(7,5))
    plt.plot(
        res["N"],
        res["CN"],
        marker="o",
        label="Crank-Nicolson"
    )

    plt.plot(
        res["N"],
        res["SSF"],
        marker="o",
        label="Split-Step Fourier"
    )

    plt.xlabel("N")
    plt.ylabel(f"{stat.capitalize()} {ylabel}")

    plt.title(
        f"{stat.capitalize()} {ylabel} vs N"
        f"\ndt = {fixed_dt}"
    )

    plt.legend()
    plt.grid()

    SavePlot(problem_folder, "VsN_in_each_problem", metric, f"{metric}_{stat}_vs_N_dt{fixed_dt}")

    plt.close()

def PlotL2_LogLog_vs_Dt(problem_folder, fixed_N, stat = "max"):
    summary = AnalyzeProblem(problem_folder)
    error_col = f"{stat}_L2_error"
    data = summary[summary["N"] == fixed_N].copy()

    plt.figure(figsize=(7,5))

    for method in ["CN", "SSF"]:
        method_data = data[data["method"] == method].sort_values("dt")

        dt = method_data["dt"].to_numpy()
        error = method_data[error_col].to_numpy()

        #Take out infinite and less than 0 values
        mask = (np.isfinite(dt) & np.isfinite(error) & (dt > 0) & (error > 0) )
        dt = dt[mask]
        error = error[mask]

        if len(dt) < 2: 
            continue

        slope = np.polyfit(np.log10(dt),np.log10(error), 1)[0]
        plt.loglog(dt, error, marker="o", label = f"{method}: slope = {slope:.2f}")
    plt.xlabel("dt (s)")
    plt.ylabel(f"{stat.capitalize()} L2 Error")

    plt.title(f"Temporal convergence\n {problem_folder.name}, N = {fixed_N}")

    plt.legend()
    plt.grid(True, which="both")

    SavePlot(problem_folder,"LogLog","L2",f"L2_loglog_dt_N{fixed_N}")

    plt.close()

def PlotL2_LogLog_vs_Dx(problem_folder, fixed_dt, domain_length, stat = "max"):
    summary = AnalyzeProblem(problem_folder)
    error_col = f"{stat}_L2_error"
    data = summary[np.isclose(summary["dt"], fixed_dt, rtol = 1e-10, atol = 0)].copy()

    #dx = L / N
    data["dx"] = domain_length / data["N"]

    plt.figure(figsize = (7,5))

    for method in ["CN", "SSF"]:
        method_data = data[data["method"] == method].sort_values("dx")

        dx = method_data["dx"].to_numpy()
        error = method_data[error_col].to_numpy()

        #Take out infinite and less than 0 values
        mask = (np.isfinite(dx) & np.isfinite(error) & (dx > 0) & (error > 0) )
        dx = dx[mask]
        error = error[mask]

        if len(dx) < 2: 
            continue

        slope = np.polyfit(np.log10(dx),np.log10(error), 1)[0]
        plt.loglog(dx, error, marker="o", label = f"{method}: slope = {slope:.2f}")
    plt.xlabel("dx (m)")
    plt.ylabel(f"{stat.capitalize()} L2 error")

    plt.title(f"Spatial convergence\n {problem_folder.name}, dt = {fixed_dt}")

    plt.legend()
    plt.grid(True, which="both")

    SavePlot(problem_folder,"LogLog","L2",f"L2_loglog_dx_dt{fixed_dt}")

    plt.close()

def PlotRuntime_vs_Metric(problem_folder, metric = "L2", stat = "max"):
    row = []

    for setting_folder in problem_folder.iterdir():
        data = ReadSetting(setting_folder)

        cn_runtime, ssf_runtime = ReadRuntime(setting_folder)
        cn_col, ssf_col, ylabel = GetMetricColumns(metric)

        if stat == "max":
            cn_value = abs(data[cn_col]).max()
            ssf_value = abs(data[ssf_col]).max()
        elif stat == "final":
            cn_value = abs(data[cn_col]).iloc[-1]
            ssf_value = abs(data[ssf_col]).iloc[-1]
        else:
            raise ValueError("Wrong stat parameter")

        row.append({
                "runtime": cn_runtime,
                "metric": cn_value,
                "method": "CN"
            })
        row.append({
                "runtime": ssf_runtime,
                "metric": ssf_value,
                "method": "SSF"
            })

    res = pd.DataFrame(row)

    plt.figure(figsize=(7,5))

    cn = res[res["method"] == "CN"]

    ssf = res[res["method"] == "SSF"]

    plt.scatter(
        cn["runtime"],
        cn["metric"],
        label="Crank-Nicolson"
    )

    plt.scatter(
        ssf["runtime"],
        ssf["metric"],
        label="Split-Step Fourier"
    )

    plt.xlabel("Runtime (seconds)")
    plt.ylabel(f"{stat.capitalize()} {ylabel}")

    plt.title(f"Runtime vs {stat.capitalize()} {ylabel}")

    plt.legend()
    plt.grid()

    SavePlot(problem_folder, "runtime", metric, f"runtime_vs_{metric}_{stat}")

    plt.close()


def PlotAllGraphs(run_folder: Path):
    metrics = ["L2", "norm_error", "energy_error", "delta_norm", "delta_energy"]
    stats = ["max", "final"]

    for problem_folder in run_folder.iterdir():
        #Ignor Graphs folder
        if problem_folder.name == "Graphs":
            continue

        print(f"\nPlotting: {problem_folder.name}")
        setting_folders = []
        N_values = set()
        dt_values = set()

        #Find all N/dt combinations
        for setting_folder in problem_folder.iterdir():

            match = re.fullmatch(r"N(\d+)_dt([0-9.eE+-]+)", setting_folder.name)
            if match is None:
                continue
            N = int(match.group(1))
            dt = float(match.group(2))
            N_values.add(N)
            dt_values.add(dt)

            setting_folders.append(setting_folder)

        #Metric vs time in each setting
        for setting_folder in setting_folders:
            for metric in metrics:
                PlotMetric_vs_Time(setting_folder, metric = metric)

        #Metric vs dt, fixed N in each problem
        for N in sorted(N_values):
            for metric in metrics:
                for stat in stats:
                    PlotMetric_vs_Dt(problem_folder, fixed_N = N, metric = metric, stat = stat)
        #Metric vs N, fixed dt in each problem
        for dt in sorted(dt_values):
            for metric in metrics:
                for stat in stats:
                    PlotMetric_vs_N(problem_folder, fixed_dt = dt, metric = metric, stat = stat)

        #Runtime vs metric in each problem
        for metric in metrics:
            for stat in stats:
                PlotRuntime_vs_Metric(problem_folder, metric = metric, stat = stat)



"""
#Testingg
run_folder = GetLatestRun()
print("Reading: ", run_folder.name)

summary = AnalyzeRun(run_folder)

print(summary)
problem_folder = run_folder / "Gaussian_Free"
setting_folder = problem_folder / "N1024_dt0.001"

#PlotMetric_vs_Time(setting_folder, metric = "L2")
#PlotMetric_vs_Dt(problem_folder,fixed_N=1024,metric="L2",stat="max")
#PlotMetric_vs_N(problem_folder,fixed_dt=0.005,metric="L2",stat="max")
PlotRuntime_vs_Metric(
    problem_folder,
    metric="L2",
    stat="max"
)
"""
if __name__ == "__main__":
    run_folder = GetLatestRun()

    print("Reading:", run_folder.name)

    summary = AnalyzeRun(run_folder)

    print(summary)

    PlotAllGraphs(run_folder)

    # Gaussian coherent state in harmonic potential
    gaussian = run_folder / "Gaussian_Harmonic"

    PlotL2_LogLog_vs_Dt(gaussian,fixed_N=4000)

    PlotL2_LogLog_vs_Dx(gaussian,
                        fixed_dt=2.5e-18,
                        domain_length=10e-9)


    # Harmonic oscillator ground state
    ho = run_folder / "HO_Ground"

    PlotL2_LogLog_vs_Dt(ho,fixed_N=4000)
    PlotL2_LogLog_vs_Dx(ho,
                        fixed_dt=2.5e-18,
                        domain_length=20e-9
                        )

