import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import math

from ParameterDefinition import WAVE_PARAMETERS, POTENTIAL_PARAMETERS
from ResultTable import ResultTable
from Simulation import SimulationConfig
from WaveAnimation import WaveAnimation
from concurrent.futures import ThreadPoolExecutor
from Simulation import SimulationConfig, RunSimulation, MAX_GRID_POINTS
from ConfigStore import ReadConfigurations, SaveConfiguration, LoadConfiguration, CONFIG_FILE

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("1D Schrodinger Equation Simulator")

        self.geometry("1100x950")
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
        self.CreateBenchmarkTab()

        """
        #Animation testing
        import numpy as np

        x = np.linspace(-10, 10, 4000)
        times = np.linspace(0, 1e-15, 100, endpoint = False)

        centers = 3 * np.sin(2 * np.pi * times / 1e-15)

        densities = np.exp(-((x[None, :] - centers[:, None]) ** 2) / (2 * 0.5 ** 2))

        self.wave_animation.LoadData(x, times, densities)
        """
    """
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

    """
    #Methods for creating the main tabs of the window (IMPORTANT) ----------------------
    def CreateSimulationTab(self):

        self.simulation_panes = ttk.Panedwindow(self.simulation_tab, orient="vertical")
        self.simulation_panes.pack(fill="both", expand=True)

        top_frame = ttk.Frame(self.simulation_panes)

        animation_frame = ttk.LabelFrame(self.simulation_panes, text="Probability Distribution")

        self.simulation_panes.add(top_frame, weight=3)
        self.simulation_panes.add(animation_frame, weight=2)

        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=2)
        top_frame.rowconfigure(0, weight=1)

        self.input_frame = ttk.Frame(top_frame)
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.result_frame = ttk.Frame(top_frame)
        self.result_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.CreateWaveSection()
        self.CreatePotentialSection()
        self.CreateNumericalSection()

        # Pack the button first to reserve space below the table.
        self.save_button = ttk.Button(
            self.result_frame,
            text="Save Results",
            command=self.OnSaveResults,
            state="disabled"
        )
        self.save_button.pack(side="bottom", pady=5)

        self.CreateConfigSection(self.result_frame)

        self.result_table = ResultTable(self.result_frame)
        self.result_table.pack(fill="both", expand=True)

        self.wave_animation = WaveAnimation(animation_frame)
        self.wave_animation.pack(fill="both", expand=True)
    def CreateBenchmarkTab(self):
        tab = self.benchmark_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        top = ttk.Frame(tab, padding=10)
        top.grid(row=0, column=0, sticky="nsew")
        top.columnconfigure(1, weight=1)
        top.rowconfigure(0, weight=1)

        #Right: console for messages
        console_frame = ttk.LabelFrame(top, text="Benchmark Console", padding=5)
        console_frame.grid(row=0, column=1, sticky="nsew", padx= (15, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.benchmark_console = tk.Text(console_frame, width=32, height=32, wrap = "word")
        self.benchmark_console.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.benchmark_console.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.benchmark_console.configure(yscrollcommand=scrollbar.set)
        self.benchmark_console.insert("end", "Ready to configure a benchmark.\n")
        self.benchmark_console.configure(state="disabled")

        #Left: benchmark inputs
        self.benchmark_config_frame = ttk.LabelFrame(top, text="Benchmark Configuration", padding=8)
        self.benchmark_config_frame.grid(row=0, column=0, sticky="nsew")
        self.benchmark_config_frame.columnconfigure(1, weight=1)

        self.benchmark_n_values = tk.StringVar(value="500, 1000")
        self.benchmark_dt_values = tk.StringVar(value="1e-18, 5e-18")

        for row, (label, variable) in enumerate([
            ("N values:", self.benchmark_n_values),
            ("dt values:", self.benchmark_dt_values)
        ]):
            ttk.Label(self.benchmark_config_frame, text=label).grid(row=row, column=0, padx=(0,8), pady=3, sticky="w")
            ttk.Entry(self.benchmark_config_frame, textvariable=variable).grid(row=row, column=1, pady=3, sticky="ew")

        ttk.Label(self.benchmark_config_frame, text= "Seperate values with commas.").grid(row=2, column=1, sticky="w")

        #Make numerical input frame
        numerical_frame = ttk.LabelFrame(self.benchmark_config_frame, text="Numerical Parameters", padding=6)
        numerical_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(10,0))
        numerical_frame.columnconfigure(1, weight = 1)

        self.benchmark_numerical_entries = {}
        for row,name in enumerate(("mass", "hbar", "x_min", "x_max", "T_final")):
            ttk.Label(numerical_frame, text=name).grid(row=row, column=0, sticky="w", padx=(0,8), pady=2)
            entry = ttk.Entry(numerical_frame)
            entry.grid(row=row, column=1, sticky="ew", pady=2)
            self.benchmark_numerical_entries[name] = entry
        
        #Make new self fields here cus self.wave_type depends on entry in simulation tab
        self.benchmark_wave_type, self.benchmark_wave_entries = ( 
            self.CreateBenchmarkPresetSection("Wave Function", WAVE_PARAMETERS, row = 4))
        self.benchmark_potential_type, self.benchmark_potential_entries = ( 
            self.CreateBenchmarkPresetSection("Potential", POTENTIAL_PARAMETERS, row = 5))

        ttk.Button(self.benchmark_config_frame, text="Preview sweep",
                   command=self.PreviewBenchmarkSweep).grid(row=6, columnspan=2, sticky="ew", pady=(10,0))



        #Bottom: table and graph show after user click save

        self.benchmark_results_frame = ttk.LabelFrame(tab, text="Benchmark Results", padding=8)
        self.benchmark_results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0,10))
        self.benchmark_results_frame.grid_remove()

    #Methods for Benchmark Tab -----------------------------------------

    def ReadBenchmarkSweep(self):

        #method for reading the strings of N and dt
        def parse_list(text, label, convert):
            values = []
            seen = set()

            for pos, item in enumerate(text.split(","), start = 1):
                item = item.strip()
                if not item:
                    raise ValueError(f"{label}: value at position {pos} is empty.\nDo not leave comma at the end.")
                try:
                    value = convert(item)
                except ValueError:
                    kind = "an integer" if convert is int else "a number"
                    #Remember to start adding 'from None'
                    raise ValueError(f"{label}: expected {kind} as position {pos}, got {item!r}") from None

                if value in seen:
                    raise ValueError(f"{label}: {item} appears more than once.")
                seen.add(value)
                values.append(value)
            return values

        n_values = parse_list(self.benchmark_n_values.get(), "N", int)
        dt_values = parse_list(self.benchmark_dt_values.get(), "dt", float)

        for n in n_values:
            if not 3 <= n <= MAX_GRID_POINTS:
                raise ValueError(f"N must be between 3 and {MAX_GRID_POINTS}. Got {n} among them.")
        return n_values, dt_values

    def PreviewBenchmarkSweep(self):
        try:
            n_values, dt_values = self.ReadBenchmarkSweep()
        except ValueError as e:
            messagebox.showerror("Invalid benchmark sweep: ", str(e), parent=self) #remember to add parent=self else it spawn new window on taskbar
            return
        
        count = len(n_values) * len(dt_values)
        console = self.benchmark_console
        console.configure(state="normal")
        console.insert("end",f"Sweep: {len(n_values)} N values x {len(dt_values)} dt values = {count} combinations.\n")
        console.see("end") #scroll down to "end" (tk.END)
        console.configure(state="disabled")
        



    def CreateBenchmarkPresetSection(self, title, definitions, row):
        frame = ttk.LabelFrame(self.benchmark_config_frame, text=title, padding= 6)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10,0))
        frame.columnconfigure(0, weight = 1)

        selected = tk.StringVar(master=frame, value=next(iter(definitions))) #Get a random one
        dropdown = ttk.Combobox(frame, textvariable=selected, values= list(definitions), state="readonly")
        dropdown.grid(row=0, column=0, sticky="ew")

        fields = ttk.Frame(frame)
        fields.grid(row=1, column=0, sticky="ew")
        fields.columnconfigure(1, weight=1)
        entries = {}

        def ShowParameters(event=None):
            for widget in fields.winfo_children():
                widget.destroy()
            entries.clear()

            parameters = definitions[selected.get()]

            #Collapse frame if no parameters
            if not parameters:
                fields.grid_remove()
                return
            fields.grid()

            for index, name in enumerate(definitions[selected.get()]):
                ttk.Label(fields, text=name).grid(row=index, column=0, sticky="w", padx=(0,8), pady=2)
                entry = ttk.Entry(fields)
                entry.grid(row=index, column=1, sticky="ew", pady=2)
                entries[name] = entry

        dropdown.bind("<<ComboboxSelected>>", ShowParameters)
        ShowParameters()
        return selected, entries







    #Methods for Saving Configurations ---------------------------------------------------------
    def CreateConfigSection(self, parent):
        frame = ttk.LabelFrame(parent, text="Configuration Management")
        frame.pack(side = "top", fill="x", pady = (0,5))
        frame.columnconfigure(1, weight=1)

        #Save configuration 
        ttk.Label(frame, text="Configuration Name:").grid(row=0, column=0, padx=5, sticky="w")
        self.config_name = tk.StringVar()
        ttk.Entry(frame, textvariable = self.config_name).grid(row=0, column=1, padx=5, pady=3, sticky = "ew")
        ttk.Button(frame, text="Save", command=self.OnSaveConfig).grid(row=0, column=2, padx=5)

        #Load configuration
        ttk.Label(frame, text = "Saved Configurations: ").grid(row=1, column=0, padx=5, sticky="w")
        self.saved_config = tk.StringVar()
        self.config_dropdown = ttk.Combobox(frame, textvariable=self.saved_config, state="readonly")
        self.config_dropdown.grid(row=1, column=1, padx=5, pady = 3, sticky="ew")
        #stick the open folder option to top
        self.config_dropdown.bind("<<ComboboxSelected>>", self.OnConfigSelected)
        ttk.Button(frame, text="Load", command=self.OnLoadConfig).grid(row=1, column=2, padx=5)

        try: 
            self.RefreshConfigList()
        except (OSError, ValueError) as e:
            messagebox.showerror("Cannot read configurations", str(e))

    def RefreshConfigList(self, selected=None):
        names = sorted(ReadConfigurations(), key = str.casefold)
        self.config_dropdown.configure(values = ["Open configuration folder...", *names])

        if selected not in names:
            selected = names[0] if names else ""

        self.last_selected_config = selected
        self.saved_config.set(selected)

    def OnConfigSelected(self, event = None):
        #Save the current config selection when user select the open folder option
        if self.config_dropdown.current() != 0:
            self.last_selected_config = self.saved_config.get()
            return

        self.saved_config.set(self.last_selected_config)

        try:
            folder = CONFIG_FILE.parent
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(folder)
        except (OSError) as e:
            messagebox.showerror("Error Opening Configuration Folder", str(e), parent = self)

    def OnSaveConfig(self):
        name = self.config_name.get().strip()
        if not name:
            messagebox.showerror("Invalid Name", "Configuration name cannot be empty.")
            return
        try:
            config = self.BuildSimulationConfig()
            if name in ReadConfigurations():
                if not messagebox.askyesno("Overwrite Confirmation", f"Configuration '{name}' already exists. Overwrite?"):
                    return

            SaveConfiguration(name, config)
            self.RefreshConfigList(selected = name)
        except (OSError, ValueError, KeyError) as e:
            messagebox.showerror("Error Saving Configuration", str(e))

    def OnLoadConfig(self):
        name = self.saved_config.get()
        if not name:
            messagebox.showerror("No Configuration Selected", "Please select a configuration to load.")
            return

        try:
            config = LoadConfiguration(name)
            self.ApplySimulationConfig(config)
            self.config_name.set(name)
        except (OSError, ValueError, KeyError) as e:
            messagebox.showerror("Error Loading Configuration", str(e))

    def ApplySimulationConfig(self, config):
        def fill(entry, value):
            entry.delete(0, tk.END)
            entry.insert(0, str(value))

        #Apply the values
        for name, entry in self.numerical_entries.items():
            fill(entry, getattr(config, name))

        self.solver_type.set(config.solver)

        self.wave_input_mode.set(config.wave_mode)
        self.OnWaveInputModeChanged()

        if config.wave_mode == "Preset":
            self.wave_type.set(config.wave_type)
            self.OnWaveSelected()

            for name, entry in self.wave_entries.items():
                fill(entry, config.wave_parameters[name])
        else:
            fill(self.wave_expression_entry, config.wave_expression or "")

        self.potential_type.set(config.potential_type)
        self.OnPotentialSelected()

        for name, entry in self.potential_entries.items():
            fill(entry, config.potential_parameters[name])


    #Method for the wave input frame --------------------
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

        self.wave_dropdown.pack(fill="x",padx=5,pady=5)

        self.wave_parameter_frame = ttk.Frame(self.wave_preset_frame)
        self.wave_parameter_frame.pack(fill="x")
        self.wave_dropdown.bind("<<ComboboxSelected>>", self.OnWaveSelected)

        #Give the dropdown a default selection
        self.wave_type.set(next(iter(WAVE_PARAMETERS)))
        self.OnWaveSelected()


        #Make expression frame
        self.wave_expression_frame = ttk.Frame(self.wave_frame)

        ttk.Label(self.wave_expression_frame,text="ψ(x,0) =").pack(anchor="w")

        self.wave_expression_entry = ttk.Entry(self.wave_expression_frame)

        self.wave_expression_entry.pack(fill="x",padx=5,pady=5)
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

            row.pack(fill="x",padx=5,pady=2)

            label = ttk.Label(row,text=f"{name}:",width=12)

            label.pack(side="left")

            entry = ttk.Entry(row)

            entry.pack(side="left",fill="x",expand=True)

            self.wave_entries[name] = entry

    #Methods for the potential input frame --------------------
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

        dropdown.pack(fill="x",padx=5,pady=5)

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

        if not parameters:
            self.potential_parameter_frame.pack_forget()
            return
        self.potential_parameter_frame.pack(fill="x")

        for name in parameters:

            row = ttk.Frame(self.potential_parameter_frame)

            row.pack(fill="x",padx=5,pady=2)

            ttk.Label(row,text=f"{name}:",width=12).pack(side="left")

            entry = ttk.Entry(row)

            entry.pack(side="left",fill="x",expand=True)

            self.potential_entries[name] = entry

    #Methods for the numerical input frame --------------------
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

            row.pack(fill="x",padx=5,pady=2)

            ttk.Label(row,text=f"{name}:",width=12).pack(side="left")

            entry = ttk.Entry(row)

            entry.pack(side="left",fill="x",expand=True)

            self.numerical_entries[name] = entry

        #Solver choice
        solver_row = ttk.Frame(frame)

        solver_row.pack(fill="x",padx=5,pady=5)

        ttk.Label(solver_row,text="Solver:",width=12).pack(side="left")

        self.solver_type = tk.StringVar(value="SSF")
        #Drop down list for Solver
        solver_dropdown = ttk.Combobox(
            solver_row,
            textvariable=self.solver_type,
            values=["Crank-Nicolson", "SSF"],
            state="readonly"
        )

        solver_dropdown.pack(side="left",fill="x",expand=True)

        #Run button
        self.run_button = ttk.Button(frame,text="Run Simulation",command=self.OnRunSimulation)

        self.run_button.pack(pady=10)

    #Methods for the run button ----------------------------------
    def OnRunSimulation(self):
        try:
            config = self.BuildSimulationConfig()

        except (ValueError, KeyError) as error:
            messagebox.showerror("Invalid Input",str(error))
            return
        
        self.run_button.configure(state="disabled", text="Running...")

        #Run in a thread to not freezing the GUI 
        worker = ThreadPoolExecutor(max_workers=1)
        future = worker.submit(RunSimulation, config)
        worker.shutdown(wait=False)

        self.after(50, self.FinishSimulation, future)

    def FinishSimulation(self, future):
        if not future.done():
            self.after(50, self.FinishSimulation, future)
            return
        try:
            res, x, times, densities = future.result()
            self.wave_animation.LoadData(x, times, densities)
            self.result_table.LoadDataFrame(res)

            self.current_results = res
            self.save_button.configure(state="normal")
        
        #Catch ValueError from Simulation so it doesn't crash
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error), parent=self)

        except Exception as error:
            messagebox.showerror("Simulation Error", str(error))

        finally:
            self.run_button.configure(state="normal", text="Run Simulation")

    #The save button ------------------------------------
    def OnSaveResults(self):

        if self.current_results is None:
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV files", "*.csv")])

        if not path:
            return

        self.current_results.to_csv(path,index=False)

    #For detecting empty and wrong entries then convert
    def ReadEntry(self, entry, name, expected_type):
        text = entry.get().strip()
        if not text:
            entry.focus_set()
            raise ValueError(f"Entry for {name} is empty")

        try: 
            return expected_type(text)
        except (ValueError, TypeError):
            entry.focus_set()
            entry.selection_range(0, "end")
            kind = "an integer" if expected_type is int else "a number"
            raise ValueError(f"{name} expected {kind}. You entered '{text}'") from None

    def BuildSimulationConfig(self):
        
        entries = self.numerical_entries
        mass = self.ReadEntry(entries["mass"], "mass", float)

        hbar = self.ReadEntry(entries["hbar"], "hbar", float)
        x_min = self.ReadEntry(entries["x_min"], "x_min", float)
        x_max = self.ReadEntry(entries["x_max"], "x_max", float)
        N = self.ReadEntry(entries["N"], "N", int)
        dt = self.ReadEntry(entries["dt"], "dt", float)
        T_final = self.ReadEntry(entries["T_final"], "T_final", float)

        wave_parameters = {}

        if self.wave_input_mode.get() == "Preset":

            parameter_types = WAVE_PARAMETERS[self.wave_type.get()]

            for name, expected_type in parameter_types.items():

                value = self.wave_entries[name].get()

                wave_parameters[name] = self.ReadEntry(self.wave_entries[name], f"Wave function / {name}", expected_type)

        potential_parameters = {}

        parameter_types = POTENTIAL_PARAMETERS[self.potential_type.get()]

        for name, expected_type in parameter_types.items():

            value = self.potential_entries[name].get()

            potential_parameters[name] = self.ReadEntry(self.potential_entries[name], f"Potential / {name}", expected_type)

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