"""
*AI SCRIPT, NEED CHECKING

Compare saved benchmark CSVs or run folders without running either solver.

Run without arguments for file/folder selection, or use --help for examples.
N and dt come from the CSV's Setting row, never from indexed folder names.
Summaries use every row; only the displayed time curves are downsampled.

Examples from the project folder:
    python ComparingMethods/PlotBenchmarkCSV.py
    python ComparingMethods/PlotBenchmarkCSV.py "D:/results/run A" "D:/results/run B" --plot all
    python ComparingMethods/PlotBenchmarkCSV.py "D:/results/run A" --plot temporal --fixed-n 32000
    python ComparingMethods/PlotBenchmarkCSV.py "D:/results/run A" --plot spatial --fixed-dt 2e-19
    python ComparingMethods/PlotBenchmarkCSV.py first.csv second.csv --plot phase --log-y

Output is a new comparison_* folder containing PNG/PDF figures, summary.csv,
plot_settings.json, and (when applicable) time_samples.csv/runtime_pairs.csv.
Keep runtime_data.txt next to each CSV for cost/runtime plots. Standalone CSVs
without run.json are kept in separate panels unless --standalone-problem is given.
No source CSV, run manifest, or application setting is changed.
"""

from pathlib import Path
from datetime import datetime
from uuid import uuid4
import argparse
import csv
import json
import math
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


METHODS = ("CN", "SSF")
COLORS = {"CN": "#1764a0", "SSF": "#d46a14"}
METRICS = {"l2": ("L2Error", "Raw L2 error"),
        "aligned": ("phase_aligned_L2Error", "Phase-aligned L2 error"),
        "phase": ("phase_difference", "Global phase difference (rad)"),
        "norm-drift": ("norm", "Absolute norm drift"),
        "energy-drift": ("expected_energy", "Absolute energy drift"),
        "relative-energy-drift": ("expected_energy", "Relative energy drift"),
}
PLOTS = ("time", "temporal", "spatial", "phase", "energy", "cost", "runtime")


def SameNumber(first, second):
    return math.isclose(float(first), float(second), rel_tol = 1e-10, abs_tol = 0)


def ReadManifest(folder):
    with (folder / "run.json").open(encoding = "utf-8-sig") as file:
        manifest = json.load(file)
    if manifest.get("status", "completed") not in ("completed", "stopped"):
        raise ValueError(f"Use a completed or stopped run: {folder}")
    records = {}
    for record in manifest["results"]:
        path = (folder / record["folder"] / "comparison_data.csv").resolve()
        if not path.is_relative_to(folder):
            raise ValueError(f"Result path is outside its run folder: {path}")
        if path in records:
            raise ValueError(f"Duplicate manifest result: {path}")
        config = dict(manifest["configuration"]["problems"][record["problem"]])
        # Save these fields as seperate keys in record
        for field in ("N", "dt", "solver"):
            config.pop(field, None)
        if config.get("boundary_condition") is None:
            config["boundary_condition"] = "Periodic"
        records[path] = {"problem": record["problem"], "config": config,
                         "N": record["N"], "dt": record["dt"],
                         "run_path": str(folder), "run": folder.name}
    return records


#Read the N and dt off the first row in a CSV
def ReadCSVHeader(path):
    with path.open(encoding = "utf-8-sig", newline = "") as file:
        first = next(csv.reader(file), [])
    if not first or first[0].strip() != "Setting:":
        return 0, None, None
    values = {}
    for cell in first[1:]:
        key, separator, value = cell.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return 1, int(values["N"]), float(values["dt"])


def FindInputs(inputs, standalone_problem = None):
    manifests = {}
    legacy = {}
    paths = []
    for item in inputs:
        path = Path(item).expanduser().resolve()
        if path.is_dir():
            if not (path / "run.json").is_file():
                found = sorted(path.glob("*/*/comparison_data.csv"))
                if not found:
                    raise ValueError(f"No run.json or legacy problem/setting/comparison_data.csv files: {path}")
                print(f"Legacy run {path.name}: grouping by problem folder; physical configuration is unverified.")
                for source in found:
                    source = source.resolve()
                    legacy[source] = {"problem": source.parent.parent.name, "config": {},
                                      "N": None, "dt": None, "run_path": str(path), "run": path.name}
                paths.extend(found)
            else:
                manifests[path] = ReadManifest(path)
                paths.extend(manifests[path])
        elif path.is_file() and path.suffix.lower() == ".csv":
            paths.append(path)
        else:
            raise ValueError(f"Not a CSV file or run folder: {path}")

    records = []
    for path in dict.fromkeys(paths):
        if not path.is_file():
            raise ValueError(f"Missing CSV: {path}")
        metadata = dict(legacy[path]) if path in legacy else None
        for folder in path.parents:
            if (folder / "run.json").is_file():
                if folder not in manifests:
                    manifests[folder] = ReadManifest(folder)
                if path not in manifests[folder]:
                    raise ValueError(f"CSV is not listed as a completed result in run.json: {path}")
                metadata = dict(manifests[folder][path])
                break
        skiprows, n, dt = ReadCSVHeader(path)
        if metadata is None:
            # Separate unidentified files unless the caller declares a common problem.
            problem = standalone_problem or f"Standalone: {path.stem} ({len(records) + 1})"
            metadata = {"problem": problem, "config": {}, "N": n, "dt": dt,
                        "run": "Selected CSVs", "run_path": "standalone"}
            print(f"No run.json for {path.name}; physical configuration is unverified.")
        elif metadata["N"] is None:
            metadata.update(N=n, dt=dt)
        elif n is not None and (n != metadata["N"] or not SameNumber(dt, metadata["dt"])):
            raise ValueError(f"CSV settings disagree with run.json: {path}")
        n, dt = metadata["N"], metadata["dt"]
        if type(n) is not int or n < 3 or dt is None or not math.isfinite(dt) or dt <= 0:
            raise ValueError(f"Cannot determine valid N and dt for {path}. Keep its Setting row or run.json.")
        metadata.update(path=path, skiprows=skiprows,
                        signature=json.dumps(metadata["config"], sort_keys=True))
        records.append(metadata)
    if not records:
        raise ValueError("No completed CSV results were selected.")

    # Distinguish different runs even when their folder names are identical.
    run_names = {}
    for record in records:
        run_names.setdefault(record["run_path"], record["run"])
    for index, (path, name) in enumerate(run_names.items(), 1):
        if list(run_names.values()).count(name) > 1:
            for record in records:
                if record["run_path"] == path:
                    record["run"] = f"{name} [{index}]"
    return records


def PickInputs():
    import tkinter as tk
    from tkinter import filedialog, messagebox
    root = tk.Tk()
    root.withdraw()
    try:
        folders = messagebox.askyesnocancel(
            "Select benchmark data", "Select whole run folders?\n\n"
            "Yes: run folders containing run.json.\nNo: individual CSV files.", parent=root)
        if folders is None:
            return []
        selected = []
        while True:
            title = "Select data; Cancel finishes the selection"
            if folders:
                result = filedialog.askdirectory(title=title, parent=root)
                if not result:
                    break
                selected.append(result)
            else:
                result = filedialog.askopenfilenames(title=title, parent=root,
                                                    filetypes=[("CSV files", "*.csv")])
                if not result:
                    break
                selected.extend(result)
        return selected
    finally:
        root.destroy()


def SelectTimeFiles(records, args):
    chosen = set()
    groups = {}
    for record in records:
        groups.setdefault((record["problem"], record["signature"]), []).append(record)
    for (problem, _), group in groups.items():
        if args.fixed_n is not None:
            group = [r for r in group if r["N"] == args.fixed_n]
        if args.fixed_dt is not None:
            group = [r for r in group if SameNumber(r["dt"], args.fixed_dt)]
        # Avoid hundreds of overlapping time curves when selecting whole runs.
        if len(group) > 8:
            n = max(r["N"] for r in group)
            dt = min(r["dt"] for r in group if r["N"] == n)
            group = [r for r in group if r["N"] == n and SameNumber(r["dt"], dt)]
            print(f"Time curves for {problem}: N={n}, dt={dt:g} (automatic slice).")
        chosen.update(r["path"] for r in group)
    return chosen


def ReadRuntime(record, rows, final_time):
    path = record["path"].with_name("runtime_data.txt")
    if not path.is_file():
        print(f"No runtime_data.txt for {record['path']}; timing plots omit this file.")
        return {method: np.nan for method in METHODS}
    try:
        text = path.read_text(encoding="utf-8-sig")
        result = {}
        for name, expected in (("N", record["N"]), ("dt", record["dt"]),
                               ("T_final", final_time), ("steps", rows - 1)):
            match = re.search(rf"^{name}\s*=\s*(\S+)\s*$", text, re.M)
            if match and not SameNumber(float(match.group(1)), expected):
                raise ValueError(f"{name} disagrees with the CSV")
        for method in METHODS:
            matches = re.findall(rf"^{method} runtime:\s*(\S+)\s+seconds\s*$", text, re.M)
            if len(matches) != 1:
                raise ValueError(f"Missing or duplicate {method} runtime")
            result[method] = float(matches[0])
            if not math.isfinite(result[method]) or result[method] < 0:
                raise ValueError("Invalid runtime")
        return result
    except ValueError as error:
        print(f"Ignoring runtime file {path}: {error}")
        return {method: np.nan for method in METHODS}


def AnalyzeCSV(record, keep_trace, max_points):
    path = record["path"]
    columns = pd.read_csv(path, skiprows=record["skiprows"], nrows=0).columns
    if not {"step", "time"}.issubset(columns):
        raise ValueError(f"Expected benchmark step/time columns: {path}")
    wanted = ["step", "time"] + [f"{m}_{suffix}" for m in METHODS
              for suffix in dict.fromkeys(value[0] for value in METRICS.values())
              if f"{m}_{suffix}" in columns]
    if len(wanted) == 2:
        raise ValueError(f"No CN/SSF diagnostic columns found: {path}")
    initial = {}
    maxima = {(m, metric): -np.inf for m in METHODS for metric in METRICS}
    missing = {key: 0 for key in maxima}
    final = {}
    trace = pd.DataFrame()
    count, stride = 0, 1
    last = None
    for chunk in pd.read_csv(path, skiprows=record["skiprows"], usecols=wanted,
                             dtype=float, chunksize=100000, float_precision="round_trip"):
        if chunk.empty:
            continue
        sequence = np.arange(count, count + len(chunk))
        if not np.array_equal(chunk["step"].to_numpy(), sequence):
            raise ValueError(f"Missing, duplicate, or out-of-order steps in {path}")
        times = chunk["time"].to_numpy()
        if not np.all(np.isfinite(times)) or not np.allclose(
                times, sequence * record["dt"], rtol=1e-10, atol=0):
            raise ValueError(f"CSV times disagree with dt: {path}")
        values = pd.DataFrame({"row": sequence, "time": times})
        for method in METHODS:
            for metric, (suffix, _) in METRICS.items():
                column = f"{method}_{suffix}"
                data = chunk[column].to_numpy() if column in chunk else np.full(len(chunk), np.nan)
                if np.isinf(data).any():
                    raise ValueError(f"Infinite values in {column}: {path}")
                if suffix in ("norm", "expected_energy") and column in chunk and not np.isfinite(data).all():
                    raise ValueError(f"Missing values in {column}: {path}")
                if suffix in ("norm", "L2Error", "phase_aligned_L2Error") and (data < 0).any():
                    raise ValueError(f"Negative values in {column}: {path}")
                if metric == "phase" and (np.abs(data) > np.pi + 1e-12).any():
                    raise ValueError(f"Phase outside [-pi, pi] in {path}")
                initial.setdefault(column, data[0])
                if metric.endswith("drift"):
                    data = np.abs(data - initial[column])
                    if metric == "relative-energy-drift":
                        energy = abs(initial[column])
                        data = data / energy if np.isfinite(energy) and energy > 0 else np.full(len(data), np.nan)
                key = (method, metric)
                finite = np.isfinite(data)
                missing[key] += int((~finite).sum())
                if finite.any():
                    maxima[key] = max(maxima[key], float(np.max(np.abs(data[finite]))))
                final[key] = float(data[-1])
                if keep_trace:
                    values[f"{method}_{metric}"] = data
        if keep_trace:
            last = values.iloc[[-1]].copy()
            trace = pd.concat([trace, values.loc[sequence % stride == 0]], ignore_index=True)
            while len(trace) > max_points:
                stride *= 2
                trace = trace.loc[trace["row"] % stride == 0].copy()
        count += len(chunk)
        final_time = float(times[-1])
    if count < 2:
        raise ValueError(f"CSV must contain an initial state and at least one step: {path}")
    expected_time = record["config"].get("T_final")
    if expected_time is not None and not SameNumber(final_time, expected_time):
        raise ValueError(f"CSV does not reach the configured final time: {path}")
    if keep_trace:
        trace = pd.concat([trace, last]).drop_duplicates("row").sort_values("row")
    runtime = ReadRuntime(record, count, final_time)
    rows = []
    for method in METHODS:
        row = {"run": record["run"], "run_path": record["run_path"],
               "problem": record["problem"], "configuration": record["signature"],
               "N": record["N"], "dt": record["dt"], "method": method,
               "rows": count, "final_time": final_time, "runtime": runtime[method],
               "source_csv": str(path)}
        for metric in METRICS:
            key = (method, metric)
            # A maximum over only the available times can understate the true maximum.
            row[f"max_{metric}"] = maxima[key] if missing[key] == 0 else np.nan
            row[f"final_{metric}"] = abs(final[key])
            row[f"missing_{metric}"] = missing[key]
            if 0 < missing[key] < count:
                print(f"Partly unavailable {method} {metric} in {path}; its maximum is omitted.")
        rows.append(row)
    return rows, trace


def AssignGroups(summary):
    # Keep different physical configurations and observation intervals separate.
    keys = list(dict.fromkeys(zip(summary.problem, summary.configuration,
                                summary.final_time.map(lambda value: f"{value:.12g}"))))
    labels = {}
    for index, key in enumerate(keys, 1):
        label = key[0]
        if sum(k[0] == label for k in keys) > 1:
            label += f" [configuration/interval {index}]"
        labels[key] = label
    summary["group"] = [labels[(r.problem, r.configuration, f"{r.final_time:.12g}")]
                        for r in summary.itertuples()]
    return summary


def DrawCurve(ax, x, y, label, color, style="-", log=False, marker=None):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    valid = np.isfinite(x) & np.isfinite(y)
    if log:
        valid &= (x > 0) & (y > 0)
    if not valid.any():
        return False
    # Preserve gaps in time curves; do not connect across unavailable diagnostics.
    if not log:
        ax.plot(x, np.where(valid, y, np.nan), style, color=color, label=label, linewidth=1.2,
                marker=marker, markevery=max(1, len(x) // 12), markersize=3)
    else:
        x, y = x[valid], y[valid]
        order = np.argsort(x)
        line = style if len(np.unique(x)) == len(x) else "None"
        ax.loglog(x[order], y[order], linestyle=line, marker="o", markersize=4,
                  color=color, label=label, linewidth=1.2)
    return True


def SaveFigure(fig, output, name):
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    for extension in ("png", "pdf"):
        fig.savefig(output / f"{name}.{extension}", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {name}.png and .pdf")


def PlotPanels(summary, traces, args, mode, output):
    groups = list(summary.groupby("group", sort=False))
    metric = args.metric
    metric_column = f"{args.stat}_{metric}"
    styles = {run: style for run, style in zip(summary.run.unique(),
              ["-", "--", ":", "-."] * (len(summary.run.unique()) // 4 + 1))}
    markers = {run: ["o", "s", "^", "D", "v", "x", "P", "*"][i % 8]
               for i, run in enumerate(summary.run.unique())}
    # Limit the size of each exported page for runs containing many problems.
    for offset in range(0, len(groups), 6):
        page = groups[offset:offset + 6]
        columns = min(2, len(page))
        fig, axes = plt.subplots(math.ceil(len(page) / columns), columns,
                                 figsize=(11 if columns == 2 else 8, 4 * math.ceil(len(page) / columns)),
                                 squeeze=False)
        figure_has_data = False
        for ax, (problem, data) in zip(axes.flat, page):
            has_data = False
            title = problem
            if mode in ("time", "phase", "energy"):
                metrics = ["l2", "aligned"] if mode == "phase" else [
                    "relative-energy-drift" if mode == "energy" else metric]
                for source, rows in data.groupby("source_csv", sort=False):
                    if source not in traces:
                        continue
                    trace = traces[source]
                    setting = rows.iloc[0]
                    for method in METHODS:
                        for item in metrics:
                            y = trace[f"{method}_{item}"].to_numpy().copy()
                            if args.log_y and item == "phase":
                                y = np.abs(y)
                            if args.log_y:
                                y[y <= 0] = np.nan
                            label = f"{method}, {setting['run']}, N={setting['N']}, dt={setting['dt']:g}"
                            if mode == "phase":
                                label += ", " + ("raw" if item == "l2" else "aligned")
                            style = ("--" if item == "aligned" else "-") if mode == "phase" else styles[setting["run"]]
                            has_data |= DrawCurve(ax, trace.time * 1e15, y, label, COLORS[method], style,
                                                  marker=markers[setting["run"]] if mode == "phase" else None)
                ax.set_xlabel("Time (fs)")
                ax.set_ylabel("L2 error" if mode == "phase" else METRICS[metrics[0]][1])
                if mode == "time" and metric == "phase" and args.log_y:
                    ax.set_ylabel("Absolute global phase difference (rad)")
                if args.log_y:
                    ax.set_yscale("log")
            else:
                if mode == "temporal":
                    n = args.fixed_n if args.fixed_n is not None else int(data.N.max())
                    data = data[data.N == n]
                    title += f"\nN = {n}"
                    x_column, scale, xlabel = "dt", 1e15, "Time step (fs)"
                elif mode == "spatial":
                    dt = args.fixed_dt if args.fixed_dt is not None else float(data.dt.min())
                    data = data[np.isclose(data.dt, dt, rtol=1e-10, atol=0)]
                    title += f"\ndt = {dt:g} s"
                    x_column, scale, xlabel = "N", 1, "Grid points N"
                else:
                    x_column, scale, xlabel = "runtime", 1, "Recorded propagation time (s)"
                for (run, method), rows in data.groupby(["run", "method"], sort=False):
                    rows = rows.sort_values(x_column)
                    if mode == "cost":
                        rows = rows[np.isfinite(rows.runtime) & (rows.runtime > 0) &
                                    np.isfinite(rows[metric_column]) & (rows[metric_column] > 0)]
                        if not rows.empty:
                            ax.loglog(rows.runtime, rows[metric_column], linestyle="None", marker="o",
                                      markersize=4, alpha=0.5, color=COLORS[method], label=f"{method}, {run}")
                            best = rows.loc[rows.groupby("runtime")[metric_column].idxmin()].sort_values("runtime")
                            best = best[best[metric_column] < best[metric_column].cummin().shift(fill_value=np.inf)]
                            ax.loglog(best.runtime, best[metric_column], styles[run], color=COLORS[method])
                            has_data = True
                    else:
                        has_data |= DrawCurve(ax, rows[x_column] * scale, rows[metric_column],
                                              f"{method}, {run}", COLORS[method], styles[run], log=True)
                ax.set_xlabel(xlabel)
                adjective = "Maximum" if args.stat == "max" else "Final"
                ax.set_ylabel(f"{adjective} {'absolute ' if metric == 'phase' else ''}{METRICS[metric][1]}")
            ax.set_title(title, fontsize=10)
            ax.grid(True, which="both", alpha=0.18)
            if has_data:
                ax.legend(fontsize=7)
                figure_has_data = True
            else:
                ax.text(0.5, 0.5, "No available values for this selection", ha="center", va="center", transform=ax.transAxes)
        for ax in list(axes.flat)[len(page):]:
            ax.set_visible(False)
        if figure_has_data:
            fig.suptitle(f"Benchmark comparison: {mode}" +
                         (" (energy diagnostics may differ between runs)" if mode == "energy" else ""), fontsize=13)
            suffix = f"_{offset // 6 + 1}" if len(groups) > 6 else ""
            SaveFigure(fig, output, f"{mode}_{metric if mode not in ('phase', 'energy') else 'comparison'}{suffix}")
        else:
            plt.close(fig)
            print(f"Skipped {mode}: no available values for the selected settings.")


def PlotRuntime(summary, args, output):
    paired = summary.pivot(index=["run", "group", "N", "dt", "source_csv", "rows"],
                           columns="method", values="runtime").reset_index()
    paired = paired[np.isfinite(paired.CN) & np.isfinite(paired.SSF) & (paired.CN > 0) & (paired.SSF > 0)].copy()
    if paired.empty:
        print("Skipped runtime: no positive paired timings are available.")
        return
    run_keys = []
    for run in summary.run.unique():
        rows = paired[paired.run == run]
        run_keys.append(set(zip(rows.group, rows.N, rows.dt)))
    common = set.intersection(*run_keys)
    if not common:
        print("Skipped runtime: selected runs have no common problem/N/dt settings.")
        return
    paired = paired[[key in common for key in zip(paired.group, paired.N, paired.dt)]].copy()
    paired["ratio"] = paired.CN / paired.SSF
    paired.to_csv(output / "runtime_pairs.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    dt = args.fixed_dt if args.fixed_dt is not None else paired.dt.min()
    for index, (run, rows) in enumerate(paired.groupby("run", sort=False)):
        ratio = rows.groupby("N").ratio.median()
        axes[0].semilogx(ratio.index, ratio, marker="o", label=run)
        rows = rows[np.isclose(rows.dt, dt, rtol=1e-10, atol=0)].copy()
        for method in METHODS:
            rows["per_step"] = rows[method] / (rows["rows"] - 1)
            per_step = rows.groupby("N").per_step.median()
            axes[1].loglog(per_step.index, per_step, ["-", "--", ":", "-."][index % 4],
                           marker="o", color=COLORS[method], label=f"{method}, {run}")
    axes[0].axhline(1, color="gray", linewidth=0.8)
    axes[0].set_ylabel("Median CN time / SSF time (>1 favors SSF)")
    axes[0].set_title("Matched settings shared by the selected runs")
    axes[1].set_ylabel("Median propagation time per step (s)")
    axes[1].set_title(f"dt = {dt:g} s")
    for ax in axes:
        ax.set_xlabel("Grid points N")
        ax.grid(True, which="both", alpha=0.18)
        ax.legend(fontsize=8)
    fig.suptitle("Recorded runtime comparison (single recorded timing per file)")
    SaveFigure(fig, output, "runtime_comparison")


def Main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="*", help="Benchmark CSV paths or run folders containing run.json")
    parser.add_argument("--plot", choices=("all",) + PLOTS, default="time")
    parser.add_argument("--metric", choices=tuple(METRICS), default="l2")
    parser.add_argument("--stat", choices=("max", "final"), default="max", help="Statistic for convergence/cost plots")
    parser.add_argument("--fixed-n", type=int, help="N for temporal plots; also filters time/phase/energy curves")
    parser.add_argument("--fixed-dt", type=float, help="dt in seconds for spatial/runtime plots; also filters time curves")
    parser.add_argument("--problem", action="append", help="Exact problem name to include; repeat for several names")
    parser.add_argument("--standalone-problem", help="Declare a common problem for CSVs copied outside their run folders")
    parser.add_argument("--log-y", action="store_true", help="Log time-curve y axis; phase uses absolute values and zeros are omitted")
    parser.add_argument("--max-points", type=int, default=2000, help="Maximum sampled time points, plus the final point")
    parser.add_argument("--output", type=Path, default=Path.cwd() / "ComparisonGraphs", help="Parent folder for a new output folder")
    args = parser.parse_args()
    if args.max_points < 2 or (args.fixed_n is not None and args.fixed_n < 3):
        parser.error("max-points must be at least 2 and fixed-n at least 3.")
    if args.fixed_dt is not None and (not math.isfinite(args.fixed_dt) or args.fixed_dt <= 0):
        parser.error("fixed-dt must be finite and positive.")
    inputs = args.inputs or PickInputs()
    if not inputs:
        print("No data selected.")
        return
    records = FindInputs(inputs, args.standalone_problem)
    if args.problem:
        records = [r for r in records if r["problem"] in args.problem]
    if not records:
        raise ValueError("No selected CSVs match the problem filter.")
    modes = PLOTS if args.plot == "all" else (args.plot,)
    selected_time = SelectTimeFiles(records, args) if set(modes) & {"time", "phase", "energy"} else set()
    total = len(records)
    if args.plot in ("time", "phase", "energy"):
        records = [r for r in records if r["path"] in selected_time]
    elif args.plot in ("temporal", "spatial"):
        groups = {}
        for record in records:
            groups.setdefault((record["problem"], record["signature"]), []).append(record)
        selected = []
        for group in groups.values():
            if args.plot == "temporal":
                n = args.fixed_n if args.fixed_n is not None else max(r["N"] for r in group)
                selected.extend(r for r in group if r["N"] == n)
            else:
                dt = args.fixed_dt if args.fixed_dt is not None else min(r["dt"] for r in group)
                selected.extend(r for r in group if SameNumber(r["dt"], dt))
        records = selected
    if not records:
        raise ValueError("No CSVs match the requested N/dt slice.")
    print(f"Reading {len(records)} of {total} selected files for {args.plot} plots.")
    summaries, traces = [], {}
    for index, record in enumerate(records, 1):
        print(f"[{index}/{len(records)}] {record['run']} / {record['problem']}, N={record['N']}, dt={record['dt']:g}", flush=True)
        rows, trace = AnalyzeCSV(record, record["path"] in selected_time, args.max_points)
        summaries.extend(rows)
        if not trace.empty:
            traces[str(record["path"])] = trace
    summary = AssignGroups(pd.DataFrame(summaries))
    output = args.output.resolve() / f"comparison_{datetime.now():%Y-%m-%d_%H-%M-%S}_{uuid4().hex[:6]}"
    output.mkdir(parents=True)
    summary.to_csv(output / "summary.csv", index=False)
    if traces:
        pd.concat([trace.assign(source_csv=source) for source, trace in traces.items()],
                  ignore_index=True).to_csv(output / "time_samples.csv", index=False)
    settings = vars(args).copy()
    settings.update(inputs=[str(Path(p).resolve()) for p in inputs], output=str(output),
                    source_files=[str(r["path"]) for r in records],
                    notes=["Summary statistics use every CSV row; time curves are sampled.",
                           "Missing diagnostics remain unavailable; zero/nonpositive log values are omitted.",
                           "Energy drift is not energy accuracy; diagnostic definitions can differ across runs.",
                           "Standalone physical configurations cannot be verified without run.json."])
    (output / "plot_settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    for mode in modes:
        if mode == "runtime":
            PlotRuntime(summary, args, output)
        else:
            PlotPanels(summary, traces, args, mode, output)
    print(f"\nOutputs: {output}\nsummary.csv uses all rows. time_samples.csv contains only plotted samples.")


if __name__ == "__main__":
    try:
        Main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(f"Cannot plot benchmark data: {error}")
