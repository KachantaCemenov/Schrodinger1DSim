import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json
import math
from itertools import product
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
from queue import Queue, Empty

from ResultTable import ResultTable
from Tooltips import AddToolTip
from TooltipHelpText import READ_BENCHMARK_HELP

def ReadBenchmarkManifest(folder, *, allow_running = False):
    folder = Path(folder).resolve()

    with (folder / "run.json").open("r", encoding = "utf-8") as f:
        manifest = json.load(f)

    #Check EVERYTHING    (REMEMBER TO CHANGE WHEN CHANGE CONFIG VERSION)
    if not isinstance(manifest, dict):
        raise ValueError("run.json was not loaded as a dict.")

    config = manifest.get("configuration")
    results = manifest.get("results")
    if not isinstance(config, dict) or config.get("version") != 1:
        raise ValueError("Unsupported run configuration format.")

    problems = config.get("problems")
    n_values = config.get("N_values")
    dt_values = config.get("dt_values")

    
    if not isinstance(problems, dict) or not problems:
        raise ValueError("The run must contain named problems.")

    for name, data in problems.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Problem names must be nonempty strings.")

        if not isinstance(data, dict):
            raise ValueError(f"Invalid configuration for problem '{name}'.")

        #Support loading my old benchmark runs
        boundary = data.get("boundary_condition")
        if boundary is None:
            boundary = "Periodic"

        if boundary not in ("Periodic", "Dirichlet"):
            raise ValueError(f"Problem '{name}' has an invalid boundary condition.")

        if data.get("potential_type") == "Infinite Square Well":
            raise ValueError(f"Problem '{name}' uses Infinite Square Well. This run format compares CN and FFT-based SSF, which does not support infinite walls.")

        if boundary != "Periodic":
            raise ValueError(f"Problem '{name}' declares Dirichlet boundaries, but this benchmark format compares both solvers using periodic boundaries.\n\n"
                        "Existing results cannot be converted by changing their boundary label. Create a new periodic benchmark.")

        data["boundary_condition"] = boundary

    if not isinstance(n_values, list) or not n_values:
        raise ValueError("The run must contain N values.")
    if not isinstance(dt_values, list) or not dt_values:
        raise ValueError("The run must contain dt values.")

    for n in n_values:
        if type(n) is not int or n < 3:
            raise ValueError("N values must be integers of at least 3.")
    for dt in dt_values:
        if type(dt) not in (int, float) or not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt values must be finite and positive.")

    if len(set(n_values)) != len(n_values):
        raise ValueError("The run contains duplicate N values.")
    if len(set(dt_values)) != len(dt_values):
        raise ValueError("The run contains duplicate dt values.")
    if not isinstance(results, list):
        raise ValueError("The manifest results must be a list.")

    status = manifest.get("status", "completed") #"complete" might not be needed here, just put there so I can load my old saves 
    allowed_statuses = {"completed", "stopped"}
    if allow_running:                           #Running files are written to a recovery folder
        allowed_statuses.add("running")
    if status not in allowed_statuses:
        raise ValueError("Open a completed or deliberately stopped benchmark run.")

    expected = set(product(problems, map(str, n_values), map(str, dt_values)))
    found = set()

    for record in results:
        if not isinstance(record, dict):
            raise ValueError("Invalid record in results.")

        problem = record.get("problem")
        relative_folder = record.get("folder")
        if not isinstance(problem, str) or not isinstance(relative_folder, str):
            raise ValueError("Each result needs a problem name and folder.")

        key = (problem, str(record.get("N")), str(record.get("dt")))
        if key not in expected or key in found:
            raise ValueError(f"Unexpected or duplicate result: {key}")

        csv_path = (folder / relative_folder / "comparison_data.csv").resolve()
        if not csv_path.is_relative_to(folder):
            raise ValueError("A result path points outside the run folder.")
        if not csv_path.is_file():
            raise ValueError(f"Missing result file: {csv_path}")
        found.add(key)

    if status == "completed" and found != expected:
        raise ValueError("The completed run is missing some results.")

    # Count good configuration and records.
    manifest["completed_combinations"] = len(found)
    manifest["total_combinations"] = len(expected)

    # A stop requested at the very end may have produced all results.
    manifest["status"] = ("completed" if found == expected else "stopped")

    return manifest


class BenchmarkResults(ttk.Frame):
    QUANTITIES = {
        "Norm": ("CN_norm", "SSF_norm"),
        "Position <x>": ("CN_expected_x", "SSF_expected_x"),
        "Momentum <p>": ("CN_expected_p", "SSF_expected_p"),
        "Energy <E>": ("CN_expected_energy", "SSF_expected_energy"),
        "L2 error": ("CN_L2Error", "SSF_L2Error"),
    }

    def __init__(self, parent):
        super().__init__(parent)

        self.folder = None
        self.records = {}
        self.loaded_path = None
        self.data = None
        self.problems = {}

        #For the convergence display
        self.manifest = None
        self.run_generation = 0

        self.convergence_cache = {}
        self.convergence_table = None
        self.convergence_key = None
        self.convergence_busy = False
        self.convergence_queue = Queue()
        self.plot_mode = tk.StringVar(value = "Against time") #default

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 5))

        self.variables = {}
        self.dropdowns = {}

        #Choose the problem
        for column, label in enumerate(("Problem", "Quantity", "N", "dt")):
            controls.columnconfigure(column, weight=1)

            ttk.Label(controls, text=label).grid(row=0, column=column, sticky="w", padx=4)

            variable = tk.StringVar(master=self)
            dropdown = ttk.Combobox(controls, textvariable=variable, state="disabled", width=16)
            dropdown.grid(row=1, column=column, sticky="ew", padx=4)
            dropdown.bind("<<ComboboxSelected>>", self.ShowSelection)

            self.variables[label] = variable
            self.dropdowns[label] = dropdown
            AddToolTip(dropdown, READ_BENCHMARK_HELP[label]) #Add tooltip

        #Add the boundary text
        self.boundary_text = tk.StringVar(value = "Boundary: no problem selected")
        ttk.Label(controls, textvariable = self.boundary_text).grid(row = 2, column = 0, columnspan = 4,sticky = "w", padx = 4, pady = (6, 0))

        #A dropdown for switching to convergence graphs
        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill = "x", pady = (0, 6))
        ttk.Label(mode_frame, text = "Plot mode:").pack(side = "left")
        self.plot_mode_dropdown = ttk.Combobox(mode_frame, textvariable = self.plot_mode,values = ("Against time",
                                                                                                "Vary dt (fixed N)",
                                                                                                "Vary N (fixed dt)"), state = "disabled", width = 24)
        self.plot_mode_dropdown.pack(side = "left", padx = 8)
        self.plot_mode_dropdown.bind("<<ComboboxSelected>>", self.ShowSelection)

        AddToolTip(self.plot_mode_dropdown, READ_BENCHMARK_HELP["plot_mode"])

        self.plot_status = tk.StringVar()
        ttk.Label(mode_frame, textvariable = self.plot_status, wraplength = 650).pack(side = "left", padx = 8)

        #Make the table and graph sections into panedwindows
        self.result_panes = ttk.Panedwindow(self, orient="horizontal")
        self.result_panes.pack(fill="both", expand=True)

        graph_frame = ttk.Frame(self.result_panes)
        table_frame = ttk.Frame(self.result_panes, padding=(8, 0))
        self.result_panes.add(graph_frame, weight=3)
        self.result_panes.add(table_frame, weight=2)

        self.figure = Figure(figsize=(6, 3), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.table_page = 0
        self.table_page_size = 200 #Putting 500 000 rows into this window isn't good idea

        paging = ttk.Frame(table_frame)
        paging.pack(side="bottom", fill="x", pady=5)
        self.previous_page_button = ttk.Button(paging,text="Previous",
                                        command=lambda: self.ChangeTablePage(-1),state="disabled")
        self.previous_page_button.pack(side="left")
        self.next_page_button = ttk.Button(paging,text="Next",
                                        command=lambda: self.ChangeTablePage(1), state="disabled")
        self.next_page_button.pack(side="right")

        self.table_page_text = tk.StringVar(value = "No results loaded")
        ttk.Label(paging, textvariable = self.table_page_text).pack(side = "left", padx = 8)

        self.result_table = ResultTable(table_frame)
        self.result_table.pack(fill = "both", expand = True)

        AddToolTip(self.previous_page_button, READ_BENCHMARK_HELP["previous"])
        AddToolTip(self.next_page_button, READ_BENCHMARK_HELP["next"])

    def RefreshTable(self):
        #convergence table
        if self.convergence_table is not None:
            table = self.convergence_table
            start = self.table_page * self.table_page_size
            end = min(start + self.table_page_size, len(table))

            page = table.iloc[start:end]
            formatted = page.map(lambda value: "N/A" if pd.isna(value) else f"{value:.16g}")
            self.result_table.LoadDataFrame(formatted)

            self.table_page_text.set(f"Rows {start + 1}–{end} of {len(table)}")
            self.previous_page_button.configure(state = "normal" if self.table_page > 0 else "disabled")
            self.next_page_button.configure(state = "normal" if end < len(table) else "disabled")
            return

        if self.data is None:
            self.result_table.LoadDataFrame(pd.DataFrame(columns=["Time", "Crank–Nicolson", "SSF"]))
            self.table_page_text.set("No results loaded")
            self.previous_page_button.configure(state="disabled")
            self.next_page_button.configure(state="disabled")
            return

        quantity = self.variables["Quantity"].get()
        cn_column, ssf_column = self.QUANTITIES[quantity]

        start = self.table_page * self.table_page_size
        end = min(start + self.table_page_size, len(self.data)) 
        page = self.data.iloc[start:end][["time", cn_column, ssf_column]].copy()
        page.columns = ["Time", "Crank–Nicolson", "SSF"]

        formatted = page.map(lambda value: "N/A" if pd.isna(value) else f"{value:.16g}") #16 significant digits
        self.result_table.LoadDataFrame(formatted)

        self.table_page_text.set(f"Rows {start + 1}–{end} of {len(self.data)}")
        self.previous_page_button.configure(state="normal" if self.table_page > 0 else "disabled")
        self.next_page_button.configure(state="normal" if end < len(self.data) else "disabled")

    def ChangeTablePage(self, direction): 
        table = (self.convergence_table if self.convergence_table is not None else self.data)

        if table is None or table.empty:
            return

        last_page = (len(table) - 1) // self.table_page_size
        self.table_page = max(0, min(self.table_page + direction, last_page))
        self.RefreshTable()

    """
    def LoadRun(self, folder, manifest):
        self.folder = Path(folder)
        self.loaded_path = None
        self.data = None


        self.records = {(record["problem"], str(record["N"]), str(record["dt"])): record for record in manifest["results"]}
        # (problem, n, dt) : results


        values = {
            "Problem": list(manifest["configuration"]["problems"]),
            "Quantity": list(self.QUANTITIES),
            "N": [str(value) for value in manifest["configuration"]["N_values"]],
            "dt": [str(value) for value in manifest["configuration"]["dt_values"]]
        }

        for label, choices in values.items():
            self.dropdowns[label].configure(values = choices, state = "readonly")
            self.variables[label].set(choices[0])
        self.ShowSelection()
    """
    def LoadRun(self, folder, manifest):

        self.run_generation += 1
        self.manifest = manifest

        self.convergence_cache.clear()
        self.convergence_table = None
        self.convergence_key = None

        self.plot_mode.set("Against time")
        self.plot_mode_dropdown.configure(state = "disabled")
        self.plot_status.set("")

        self.folder = Path(folder)
        self.problems = manifest["configuration"]["problems"]
        self.boundary_text.set("Boundary: no completed problem selected")
        self.loaded_path = None
        self.data = None
        self.table_page = 0

        self.records = {(record["problem"], str(record["N"]), str(record["dt"])): record for record in manifest["results"]}

        for label in self.variables:
            self.variables[label].set("")
            self.dropdowns[label].configure(values=(), state="disabled")

        self.RefreshTable()
        self.axes.clear()

        if not self.records: #Combinations that weren't calculated in the stopped run
            self.axes.set_title("No completed combinations yet")
            self.axes.text(0.5, 0.5,
                "This partial run contains its configuration,\nbut no completed results to inspect.",
                ha="center", va="center", transform=self.axes.transAxes)
            self.axes.set_axis_off()
            self.canvas.draw_idle()
            return

        self.SetResultChoices("Problem", list(dict.fromkeys(key[0] for key in self.records)))
        self.SetResultChoices("Quantity", list(self.QUANTITIES))
        self.plot_mode_dropdown.configure(state = "readonly")
        self.ShowSelection()

    def SetResultChoices(self, label, choices):
        self.dropdowns[label].configure(values=choices, state="readonly" if choices else "disabled")
        if self.variables[label].get() not in choices:
            self.variables[label].set(choices[0] if choices else "")

    def UpdateResultChoices(self):
        from BenchmarkConvergence import CONVERGENCE_QUANTITIES

        problem = self.variables["Problem"].get()
        mode = self.plot_mode.get()

        if mode == "Against time":
            self.SetResultChoices("Quantity", list(self.QUANTITIES))
        else:
            self.SetResultChoices("Quantity", list(CONVERGENCE_QUANTITIES))

        n_values = sorted({n for p, n, dt in self.records if p == problem}, key = int)
        self.SetResultChoices("N", n_values)

        if mode == "Vary N (fixed dt)":
            dt_values = sorted({dt for p, n, dt in self.records if p == problem}, key = float)
        else:
            selected_n = self.variables["N"].get()
            dt_values = sorted({dt for p, n, dt in self.records if p == problem and n == selected_n}, key = float)

        self.SetResultChoices("dt", dt_values)

        if mode == "Vary dt (fixed N)":
            self.variables["dt"].set("")
            self.dropdowns["dt"].configure(state = "disabled")
        elif mode == "Vary N (fixed dt)":
            self.variables["N"].set("")
            self.dropdowns["N"].configure(state = "disabled")


    def ClearConvergenceDisplay(self, message):
        #Remove the previous graph and table while reading another selection
        self.data = None
        self.loaded_path = None
        self.convergence_table = None
        self.table_page = 0
        self.RefreshTable()

        self.axes.clear()
        self.axes.text(0.5, 0.5, message, ha = "center", va = "center", transform = self.axes.transAxes)
        self.axes.set_axis_off()
        self.canvas.draw_idle()
        self.plot_status.set(message)

    def ShowConvergence(self):
        from BenchmarkConvergence import BuildConvergenceData #Import in here because it would be an import loop if import at top

        problem = self.variables["Problem"].get()
        mode = self.plot_mode.get()
        fixed_field = "N" if mode == "Vary dt (fixed N)" else "dt"
        fixed_value = self.variables[fixed_field].get()

        boundary = self.problems[problem]["boundary_condition"]
        self.boundary_text.set(f"Boundary: {boundary}")

        key = (self.run_generation, problem, mode, fixed_value)
        self.convergence_key = key

        if key in self.convergence_cache:
            self.DrawConvergence(self.convergence_cache[key])
            return

        self.ClearConvergenceDisplay("Reading convergence data...")

        #Only one reader at a time. When it finishes, load the latest selection.
        if self.convergence_busy:
            self.plot_status.set("Waiting for the previous data read...")
            return

        folder = self.folder
        manifest = self.manifest
        output = self.convergence_queue

        def Work():
            try:
                data = BuildConvergenceData(folder, manifest, problem, mode, fixed_value)
                output.put((key, data, None))
            except Exception as error:
                output.put((key, None, str(error)))

        self.convergence_busy = True

        try:
            #Read-only worker: it never accesses Tkinter widgets or writes files
            Thread(target = Work, daemon = True).start()
        except Exception as error:
            self.convergence_busy = False
            self.ClearConvergenceDisplay("Could not start the data reader.")
            messagebox.showerror("Cannot read convergence data", str(error), parent = self)
            return

        self.after(100, self.PollConvergence)

    def PollConvergence(self):
        try:
            key, data, error = self.convergence_queue.get_nowait()
        except Empty:
            self.after(100, self.PollConvergence)
            return

        self.convergence_busy = False

        #A result from a previously loaded run must not enter the new cache
        if key[0] == self.run_generation and error is None:
            self.convergence_cache[key] = data

        if self.plot_mode.get() == "Against time" or not self.records:
            return

        if key != self.convergence_key:
            #The user changed the run, problem, or fixed parameter
            self.ShowConvergence()
            return

        if error is not None:
            self.ClearConvergenceDisplay("Unable to read convergence data.")
            messagebox.showerror(
                "Cannot read convergence data", error, parent = self)
            return

        self.DrawConvergence(data)


    #Show the a selected problem in the run
    def ShowSelection(self, event = None):
        if not self.records: #Only populate valid combinations before read
            return
        self.UpdateResultChoices()
        if self.plot_mode.get() != "Against time":
            self.ShowConvergence()
            return

        self.convergence_key = None
        self.convergence_table = None
        self.plot_status.set("")

        problem = self.variables["Problem"].get()
        quantity = self.variables["Quantity"].get()
        boundary = self.problems[problem]["boundary_condition"]
        self.boundary_text.set(f"Boundary: {boundary}")
        n = self.variables["N"].get()
        dt = self.variables["dt"].get()
        columns = self.QUANTITIES[quantity]
        self.table_page = 0

        try:
            record = self.records[(problem, n, dt)]
            path = self.folder / record["folder"] / "comparison_data.csv"

            if path != self.loaded_path:
                data = pd.read_csv(path, skiprows = 1)
                required = {"time"} #set
                for pair in self.QUANTITIES.values():
                    required.update(pair)
                
                missing = required.difference(data.columns)
                if missing:
                    raise ValueError(f"Missing CSV columns: {','.join(sorted(missing))}")

                data = data.apply(pd.to_numeric, errors = "raise")
                if data.empty:
                    raise ValueError("The selected result table is empty.")

                self.data = data
                self.loaded_path = path

        except (OSError, ValueError, KeyError) as e: #Reset everything
            self.data = None
            self.loaded_path = None
            self.RefreshTable()
            self.axes.clear()
            self.axes.set_title("Unable to load selected results")
            self.canvas.draw_idle()
            messagebox.showerror("Cannot display benchmark results", str(e), parent=self)
            return

        #If L2 error is selected but not available
        if quantity == "L2 error" and self.data[list(columns)].isna().all().all():
            self.axes.clear()
            self.axes.set_title(f"{problem} — N={n}, dt={dt}")
            self.axes.text(0.5,0.5,"L2 error is unavailable.\n"
                    "This result contains no analytical-reference error values.", ha="center", va="center",
                    transform=self.axes.transAxes)
            self.axes.set_axis_off()
            self.canvas.draw_idle()
            self.RefreshTable()
            return
        
        self.axes.clear()
        self.axes.set_axis_on()
        self.axes.plot(self.data["time"],
                        self.data[columns[0]],
                        label = "Crank–Nicolson")
        self.axes.plot(self.data["time"],
                        self.data[columns[1]],
                        label = "SSF",
                        linestyle="--")
        self.axes.set_xlabel("Time")
        self.axes.set_ylabel(quantity)
        self.axes.set_title(f"{problem} — N={n}, dt={dt}")
        self.axes.legend()
        self.axes.grid(alpha=0.25)
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self.RefreshTable()

    def DrawConvergence(self, data):
        from BenchmarkConvergence import MakeConvergenceTable #Would be import loop if import at top

        mode = self.plot_mode.get()
        quantity = self.variables["Quantity"].get()
        problem = self.variables["Problem"].get()

        table = MakeConvergenceTable(data, mode, quantity)
        varying_field = table.columns[0]
        fixed_field = "N" if varying_field == "dt" else "dt"
        fixed_value = self.variables[fixed_field].get()

        self.data = None
        self.loaded_path = None
        self.convergence_table = table
        self.table_page = 0
        self.RefreshTable()

        self.axes.clear()
        self.axes.set_axis_on()
        self.axes.set_title(f"{problem} — {fixed_field}={fixed_value}")
        self.axes.set_xlabel(varying_field)
        self.axes.set_ylabel(quantity)

        values = table[["Crank–Nicolson", "SSF"]]
        available = values.stack().dropna()

        if available.empty:
            self.axes.text(0.5, 0.5,
                            "This error metric is unavailable.\nNo analytical-reference error values were recorded.",
                            ha = "center", va = "center",
                            transform = self.axes.transAxes)
            self.axes.set_axis_off()
            self.plot_status.set("L2 error unavailable; table shows N/A.")
            self.canvas.draw_idle()
            return

        for method, style in (("Crank–Nicolson", "-"), ("SSF", "--")):
            self.axes.plot(table[varying_field],
                            table[method],
                            marker = "o",
                            linestyle = style,
                            label = method)

        #N and dt must be positive for log-log. Zero error must remain visible.
        self.axes.set_xscale("log")

        if (available > 0).all():
            self.axes.set_yscale("log")
            scale_note = "Logarithmic axes."
        else:
            self.axes.set_yscale("linear")
            scale_note = "Linear error axis because zero values are present."

        notes = [f"{len(table)} completed combinations.", scale_note]

        if len(table) < 2:
            notes.append("At least two points are needed to inspect a trend.")

        if values.isna().any().any():
            notes.append("Unavailable values are shown as N/A.")

        self.plot_status.set(" ".join(notes))

        self.axes.legend()
        self.axes.grid(alpha = 0.25, which = "both")
        self.figure.tight_layout()
        self.canvas.draw_idle()