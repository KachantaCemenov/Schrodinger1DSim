from pathlib import Path
import pandas as pd
import re
import matplotlib.pyplot as plt

BASE_FOLDER = Path(__file__).resolve().parent
RESULTS_FOLDER = BASE_FOLDER / "Results"

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
    match = re.fullmatch(r"N(\d+)_dt([0-9.]+)", setting_folder.name) #Put eE+- inside [] when I do scientific notation for dt

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

#Look into one problem (fixed N fixed dt) csv file and plot the error in that as step propagate 
def PlotMetric_vs_Time(setting_folder, metric = "L2"): 
    data = ReadSetting(setting_folder)

    cn_column, ssf_column, ylabel = GetMetricColumns(metric)

    plt.figure()

    plt.plot(data["time"], data[cn_column], label = "CN")
    plt.plot(data["time"], data[ssf_column], label = "SSF")

    plt.xlabel("Time")
    plt.ylabel(ylabel)

    plt.title(f"{ylabel} vs time\n"
              f"{setting_folder.name}")

    plt.legend()
    plt.grid()
    plt.show()

#Look into all setting folders with fixed N and plot them as dt change
#arg stat is to use the maximum error or the final error in each N, dt configuration
def PlotMetric_vs_Dt(problem_folder, fixed_N, metric = "L2", stat = "max"): #max or final
    row = []

    for setting_folder in problem_folder.iterdir():
        
        match = re.fullmatch(r"N(\d+)_dt([0-9.]+)", setting_folder.name)
        if match is None:
            continue

        N = int(match.group(1))
        dt = float(match.group(2))

        if N != fixed_N:
            continue

        data = ReadSetting(setting_folder)
        cn_column, ssf_column, ylabel = GetMetricColumns(metric)

        if stat == "max":
            cn_value = abs(data[cn_column]).max()
            ssf_value = abs(data[ssf_column]).max()
        elif stat == "final":
            cn_value = abs(data[cn_column]).iloc[-1]
            ssf_value = abs(data[ssf_column]).iloc[-1]
        else:
            raise ValueError("Wrong stat parameter")

        row.append({
                "dt": dt,
                "CN": cn_value,
                "SSF": ssf_value
            })

    res = pd.DataFrame(row).sort_values("dt")

    plt.figure()
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

    plt.show()

#Same as above, reverse. TODO: consider joining these two methods
def PlotMetric_vs_N(problem_folder, fixed_dt, metric = "L2", stat = "max"): #max or final
    row = []

    for setting_folder in problem_folder.iterdir():
        
        match = re.fullmatch(r"N(\d+)_dt([0-9.]+)", setting_folder.name)
        if match is None:
            continue

        N = int(match.group(1))
        dt = float(match.group(2))

        if dt != fixed_dt:
            continue

        data = ReadSetting(setting_folder)
        cn_column, ssf_column, ylabel = GetMetricColumns(metric)

        if stat == "max":
            cn_value = abs(data[cn_column]).max()
            ssf_value = abs(data[ssf_column]).max()
        elif stat == "final":
            cn_value = abs(data[cn_column]).iloc[-1]
            ssf_value = abs(data[ssf_column]).iloc[-1]
        else:
            raise ValueError("Wrong stat parameter")

        row.append({
                "N": N,
                "CN": cn_value,
                "SSF": ssf_value
            })

    res = pd.DataFrame(row).sort_values("N")

    plt.figure()
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

    plt.show()


#Testingg
run_folder = RESULTS_FOLDER / "run_2026-10-20_14-48-21"

summary = AnalyzeRun(run_folder)

print(summary)
problem_folder = run_folder / "Gaussian_Free"
setting_folder = problem_folder / "N1024_dt0.001"

#PlotMetric_vs_Time(setting_folder, metric = "L2")
#PlotMetric_vs_Dt(problem_folder,fixed_N=1024,metric="L2",stat="max")
PlotMetric_vs_N(problem_folder,fixed_dt=0.005,metric="L2",stat="max")