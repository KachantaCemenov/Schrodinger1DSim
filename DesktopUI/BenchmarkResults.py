import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json
import math
from itertools import product
from ResultTable import ResultTable

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def ReadBenchmarkManifest(folder):
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
    if any(not name.strip() for name in problems):
        raise ValueError("Problem names cannot be empty.")
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
    if not isinstance(results, list) or not results:
        raise ValueError("The manifest must contain result records.")

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

    if found != expected:
        raise ValueError("The run is missing some problem/N/dt results.")

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

        """self.figure = Figure(figsize=(8, 3), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)"""

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

    def RefreshTable(self):
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
        if self.data is None:
            return
        last_page = (len(self.data) - 1) // self.table_page_size
        self.table_page = max(0, min(self.table_page + direction, last_page))
        self.RefreshTable()


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

    #Show the a selected problem in the run
    def ShowSelection(self, event = None):
        problem = self.variables["Problem"].get()
        quantity = self.variables["Quantity"].get()
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
        self.axes.plot(
            self.data["time"],
            self.data[columns[0]],
            label="Crank–Nicolson",
        )
        self.axes.plot(
            self.data["time"],
            self.data[columns[1]],
            label="SSF",
            linestyle="--",
        )
        self.axes.set_xlabel("Time")
        self.axes.set_ylabel(quantity)
        self.axes.set_title(f"{problem} — N={n}, dt={dt}")
        self.axes.legend()
        self.axes.grid(alpha=0.25)
        self.figure.tight_layout()
        self.canvas.draw_idle()
        self.RefreshTable()
