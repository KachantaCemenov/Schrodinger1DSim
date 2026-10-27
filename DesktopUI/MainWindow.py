import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from ParameterDefinition import WAVE_PARAMETERS, POTENTIAL_PARAMETERS
from ResultTable import ResultTable
from Simulation import SimulationConfig

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("1D Schrodinger Equation Simulator")

        self.geometry("1100x700")
        self.current_results = None

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

        #Make the table on the right
        self.result_table = ResultTable(self.result_frame)
        self.result_table.pack(fill="both",expand=True)

        #Make a save CSV button
        self.save_button = ttk.Button(
            self.result_frame,
            text="Save Results",
            command=self.OnSaveResults,
            state="disabled"
        )

        self.save_button.pack(pady=5)


    def CreateWaveSection(self):

        self.wave_frame = ttk.LabelFrame(self.input_frame,text="Wave Function")

        self.wave_frame.pack( fill="x", pady=5)

        #ttk.Label(self.wave_frame, text="Wave Function:").pack(anchor="w")

        self.wave_type = tk.StringVar()

        self.wave_input_mode = tk.StringVar(value="Preset")

        mode_row = ttk.Frame(self.wave_frame)
        mode_row.pack(fill="x", padx=5, pady=5)

        ttk.Radiobutton(
            mode_row,
            text="Preset",
            variable=self.wave_input_mode,
            value="Preset",
            command=self.OnWaveInputModeChanged
        ).pack(side="left")

        ttk.Radiobutton(
            mode_row,
            text="Expression",
            variable=self.wave_input_mode,
            value="Expression",
            command=self.OnWaveInputModeChanged
        ).pack(side="left", padx=10)

        self.wave_preset_frame = ttk.Frame(self.wave_frame)
        self.wave_preset_frame.pack(fill="x")

        self.wave_dropdown = ttk.Combobox(
            self.wave_preset_frame,
            textvariable=self.wave_type,
            values=list(WAVE_PARAMETERS.keys()),
            state="readonly"
        )

        self.wave_dropdown.pack(
            fill="x",
            padx=5,
            pady=5
        )

        self.wave_parameter_frame = ttk.Frame(self.wave_preset_frame)
        self.wave_parameter_frame.pack(fill="x")
        self.wave_dropdown.bind("<<ComboboxSelected>>", self.OnWaveSelected)

        #Give the dropdown a default selection
        self.wave_type.set(next(iter(WAVE_PARAMETERS)))
        self.OnWaveSelected()


        #Make expression frame
        self.wave_expression_frame = ttk.Frame(self.wave_frame)

        ttk.Label(
            self.wave_expression_frame,
            text="ψ(x,0) ="
        ).pack(anchor="w")

        self.wave_expression_entry = ttk.Entry(self.wave_expression_frame)

        self.wave_expression_entry.pack(
            fill="x",
            padx=5,
            pady=5
        )
    def OnWaveInputModeChanged(self):

        mode = self.wave_input_mode.get()

        if mode == "Preset":

            self.wave_expression_frame.pack_forget()

            self.wave_preset_frame.pack(fill="x")

        else:

            self.wave_preset_frame.pack_forget()

            self.wave_expression_frame.pack(fill="x")

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

        self.potential_type.set(next(iter(POTENTIAL_PARAMETERS)))
        self.OnPotentialSelected()



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
            "mass",
            "hbar",
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
        #Drop down list for Solver
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

        #Run button
        run_button = ttk.Button(
            frame,
            text="Run Simulation",
            command=self.OnRunSimulation
        )

        run_button.pack(pady=10)

    def OnRunSimulation(self):
        """
        print("Wave mode:", self.wave_input_mode.get())
        print("Wave:", self.wave_type.get())
        print("Potential:", self.potential_type.get())
        print("Solver:", self.solver_type.get())

        print("Wave parameters:")
        for name, entry in self.wave_entries.items():
            print(name, entry.get())

        print("Potential parameters:")
        for name, entry in self.potential_entries.items():
            print(name, entry.get())

        print("Numerical:")
        for name, entry in self.numerical_entries.items():
            print(name, entry.get())
        """
        try:
            config = self.BuildSimulationConfig()

        except (ValueError, KeyError) as error:
            messagebox.showerror("Invalid Input",str(error))
            return
        print(config)

    def OnSaveResults(self):

        if self.current_results is None:
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv")
            ]
        )

        if not path:
            return

        self.current_results.to_csv(
            path,
            index=False
        )

    def BuildSimulationConfig(self):
        mass = float(self.numerical_entries["mass"].get())
        hbar = float(self.numerical_entries["hbar"].get())
        x_min = float(self.numerical_entries["x_min"].get())
        x_max = float(self.numerical_entries["x_max"].get())
        N = int(self.numerical_entries["N"].get())
        dt = float(self.numerical_entries["dt"].get())
        T_final = float(self.numerical_entries["T_final"].get())

        wave_parameters = {}

        if self.wave_input_mode.get() == "Preset":

            parameter_types = WAVE_PARAMETERS[self.wave_type.get()]

            for name, expected_type in parameter_types.items():

                value = self.wave_entries[name].get()

                wave_parameters[name] = (expected_type(value))

        potential_parameters = {}

        parameter_types = POTENTIAL_PARAMETERS[self.potential_type.get()]

        for name, expected_type in parameter_types.items():

            value = self.potential_entries[name].get()

            potential_parameters[name] = (expected_type(value))

        return SimulationConfig(
                                mass = mass,
                                hbar = hbar,
                                x_min=x_min,
                                x_max=x_max,
                                N=N,
                                dt=dt,
                                T_final=T_final,
                                solver=self.solver_type.get(),

                                wave_mode=self.wave_input_mode.get(),
                                wave_type=self.wave_type.get(),
                                wave_parameters=wave_parameters,

                                potential_type=self.potential_type.get(),
                                potential_parameters=potential_parameters,

                                wave_expression=(
                                    self.wave_expression_entry.get()
                                    if self.wave_input_mode.get() == "Expression"
                                    else None)
                                )