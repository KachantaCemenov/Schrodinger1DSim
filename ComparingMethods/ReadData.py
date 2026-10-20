from pathlib import Path
import pandas as pd
import re


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

run_folder = RESULTS_FOLDER / "run_2026-10-20_14-48-21"

summary = AnalyzeRun(run_folder)

print(summary)