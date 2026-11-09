import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

        self.figure = Figure(figsize=(8, 3), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

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
            self.axes.clear()
            self.axes.set_title("Unable to load selected results")
            self.canvas.draw_idle()
            messagebox.showerror("Cannot display benchmark results", str(e), parent=self)
            return

        self.axes.clear()
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
