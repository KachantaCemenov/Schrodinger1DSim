import tkinter as tk
from tkinter import ttk

from ParameterDefinition import WAVE_PARAMETERS, POTENTIAL_PARAMETERS

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("1D Schrodinger Equation Simulator")

        self.geometry("1100x700")
        self.CreateTabs()

    def CreateTabs(self):
        self.notebook = ttk.Notebook(self)
        self.simulation_tab = ttk.Frame(self.notebook)
        self.benchmark_tab = ttk.Frame(self.notebook)
        self.recommendation_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.simulation_tab, text="Simulation")

        self.notebook.add(self.benchmark_tab, text="Benchmark Data")

        self.notebook.add( self.recommendation_tab, text="Recommendation")

        self.notebook.pack(expand = True, fill = "both")

        self.CreateSimulationTab()

    def CreateSimulationTab(self):

        self.input_frame = ttk.Frame(self.simulation_tab)

        self.result_frame = ttk.Frame( self.simulation_tab)

        self.input_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.result_frame.pack(
            side="right",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.CreateWaveSection()
        self.CreatePotentialSection()
        self.CreateNumericalSection()

    def CreateWaveSection(self):

        self.wave_frame = ttk.LabelFrame(self.input_frame,text="Wave Function")

        self.wave_frame.pack( fill="x", pady=5)

        ttk.Label(self.wave_frame, text="Wave Function:").pack(anchor="w")

        self.wave_type = tk.StringVar()

        self.wave_dropdown = ttk.Combobox(
            self.wave_frame,
            textvariable=self.wave_type,
            values=list(WAVE_PARAMETERS.keys()),
            state="readonly"
        )

        self.wave_dropdown.pack(
            fill="x",
            padx=5,
            pady=5
        )

        self.wave_parameter_frame = ttk.Frame(self.wave_frame)

        self.wave_parameter_frame.pack(fill="x")

        self.wave_dropdown.bind("<<ComboboxSelected>>",self.OnWaveSelected)

    def OnWaveSelected(self, event=None):

        for widget in (self.wave_parameter_frame.winfo_children()):
            widget.destroy()

        selected_wave = (self.wave_type.get())

        parameters = WAVE_PARAMETERS[selected_wave]

        self.wave_entries = {}

        for name in parameters:

            row = ttk.Frame(self.wave_parameter_frame)

            row.pack(
                fill="x",
                padx=5,
                pady=2
            )

            label = ttk.Label(
                row,
                text=f"{name}:",
                width=12
            )

            label.pack(side="left")

            entry = ttk.Entry(row)

            entry.pack(
                side="left",
                fill="x",
                expand=True
            )

            self.wave_entries[name] = entry

    def CreatePotentialSection(self):

        self.potential_frame = ttk.LabelFrame(self.input_frame,text="Potential")

        self.potential_frame.pack(fill="x", pady=5)
        self.potential_type = tk.StringVar()

        dropdown = ttk.Combobox(
            self.potential_frame,
            textvariable=self.potential_type,
            values=list(POTENTIAL_PARAMETERS.keys()),
            state="readonly"
        )

        dropdown.pack(
            fill="x",
            padx=5,
            pady=5
        )

        self.potential_parameter_frame = (ttk.Frame(self.potential_frame))

        self.potential_parameter_frame.pack(fill="x")

        dropdown.bind("<<ComboboxSelected>>", self.OnPotentialSelected)



    def OnPotentialSelected(self,event=None):

        for widget in (self.potential_parameter_frame.winfo_children()):
            widget.destroy()

        selected = (self.potential_type.get())

        parameters = (POTENTIAL_PARAMETERS[selected])

        self.potential_entries = {}

        for name in parameters:

            row = ttk.Frame(self.potential_parameter_frame)

            row.pack(
                fill="x",
                padx=5,
                pady=2
            )

            ttk.Label(
                row,
                text=f"{name}:",
                width=12
            ).pack(side="left")

            entry = ttk.Entry(row)

            entry.pack(
                side="left",
                fill="x",
                expand=True
            )

            self.potential_entries[
                name
            ] = entry

    def CreateNumericalSection(self):

        frame = ttk.LabelFrame(self.input_frame,text="Numerical Parameters")
        frame.pack(fill="x",pady=5)

        self.numerical_entries = {}

        parameters = [
            "x_min",
            "x_max",
            "N",
            "dt",
            "T_final"
        ]

        for name in parameters:

            row = ttk.Frame(frame)

            row.pack(
                fill="x",
                padx=5,
                pady=2
            )

            ttk.Label(
                row,
                text=f"{name}:",
                width=12
            ).pack(side="left")

            entry = ttk.Entry(row)

            entry.pack(
                side="left",
                fill="x",
                expand=True
            )

            self.numerical_entries[
                name
            ] = entry

        #Solver choice
        solver_row = ttk.Frame(frame)

        solver_row.pack(
            fill="x",
            padx=5,
            pady=5
        )

        ttk.Label(
            solver_row,
            text="Solver:",
            width=12
        ).pack(side="left")

        self.solver_type = tk.StringVar(value="SSF")

        solver_dropdown = ttk.Combobox(
            solver_row,
            textvariable=self.solver_type,
            values=["Crank-Nicolson", "SSF"],
            state="readonly"
        )

        solver_dropdown.pack(
            side="left",
            fill="x",
            expand=True
        )