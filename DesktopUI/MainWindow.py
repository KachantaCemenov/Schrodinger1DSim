import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
import os
import math
from dataclasses import replace, asdict
from queue import Queue, Empty
from tempfile import TemporaryDirectory
from pathlib import Path
from threading import Event
from concurrent.futures import ThreadPoolExecutor, CancelledError
from scipy.constants import m_e, hbar 

from ParameterDefinition import WAVE_PARAMETERS, POTENTIAL_PARAMETERS
from ResultTable import ResultTable
from Simulation import SimulationConfig, INFINITE_WELL_SSF_MESSAGE, SaveSimulationResults, BOUNDARY_CONDITIONS
from WaveAnimation import WaveAnimation
from concurrent.futures import ThreadPoolExecutor
from Simulation import SimulationConfig, RunSimulation, MAX_GRID_POINTS, MAX_STEPS
from ConfigStore import (ReadConfigurations, SaveConfiguration, LoadConfiguration, 
                    CONFIG_FILE,ReadBenchmarkConfigurations,SaveBenchmarkConfiguration,BENCHMARK_CONFIG_FILE,)
from Benchmark import (BuildBenchmarkProblem, RunBenchmarkConfiguration, SaveBenchmarkResults, 
                    HasBenchmarkReference, ResumeBenchmarkConfiguration,)
from BenchmarkResults import BenchmarkResults, ReadBenchmarkManifest
from BenchmarkRecovery import (BenchmarkWorkingDirectory, AcquireRecoveryLock, 
                        ListRecoveryFolders, IsRecoveryFolder, DeleteRecoveryFolder)
from RecommendationTab import RecommendationTab
from Tooltips import AddToolTip
from TooltipHelpText import (NUMERICAL_HELP, WAVE_HELP, POTENTIAL_HELP, SIMULATION_HELP, 
                             BENCHMARK_HELP, READ_BENCHMARK_HELP, CONSTANT_HELP)
from HelpWindow import HelpWindow
from ScrollableFrame import ScrollableFrame


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        try:
            self.recovery_lock = AcquireRecoveryLock()
        except RuntimeError as error:
            messagebox.showerror("Simulator already open", str(error), parent=self)
            self.destroy()
            raise SystemExit(1)

        self.recovery_window = None

        self.title("1D Schrodinger Equation Simulator")

        self.geometry("1100x950")
        self.current_results = None
        self.simulation_future = None
        self.help_window = None

        #These are for stopping a simulation
        self.simulation_stop_event = None
        self.simulation_save_future = None
        self.simulation_save_stop_event = None
        self.close_requested = False
        self.quit_prompt_open = False

        self.CreateTopBar()
        self.CreateTabs()

        self.protocol("WM_DELETE_WINDOW", self.OnClose) #handle closing amid running simulation/ benchmark
        self.after_idle(self.CheckBenchmarkRecovery)
    
    def CreateTopBar(self):
        top_bar = ttk.Frame(self, padding=(8, 4))
        top_bar.pack(side="top", fill="x")

        ttk.Button(top_bar, text="Help", command=self.OpenHelp).pack(side="left")


    def OpenHelp(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.deiconify()
            self.help_window.lift()
            self.help_window.focus_set()
            return

        self.help_window = HelpWindow(self)


    def CreateTabs(self):
        self.notebook = ttk.Notebook(self)
        self.simulation_tab = ttk.Frame(self.notebook)
        self.benchmark_tab = ttk.Frame(self.notebook)
        self.read_benchmark_tab = ttk.Frame(self.notebook)
        self.recommendation_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.simulation_tab, text="Simulation")

        self.notebook.add(self.benchmark_tab, text="Benchmark")
        self.notebook.add(self.read_benchmark_tab, text="Read Benchmark")

        self.notebook.add( self.recommendation_tab, text="Recommendation")

        self.notebook.pack(expand = True, fill = "both")

        self.CreateSimulationTab()
        self.CreateBenchmarkTab()
        self.CreateReadBenchmarkTab()
        #Create Recommendation Tab
        self.recommendation_view = RecommendationTab(self.recommendation_tab,get_loaded_folder=lambda: self.benchmark_saved_folder)
        self.recommendation_view.pack(fill="both", expand=True)

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

        """ Make this input frame scrollable
        self.input_frame = ttk.Frame(top_frame)
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        """
        self.simulation_input_scroll = ScrollableFrame(top_frame)
        self.simulation_input_scroll.grid(row=0,column=0,
                                         sticky="nsew", padx=10, pady=10)
        self.input_frame = self.simulation_input_scroll.content

        self.result_frame = ttk.Frame(top_frame)
        self.result_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.CreateWaveSection()
        self.CreatePotentialSection()
        self.CreateNumericalSection()

        # Pack the button first to reserve space below the table.
        self.save_button = ttk.Button(self.result_frame, text = "Save Results",
                                command = self.OnSaveResults, state = "disabled")
        self.save_button.pack(side="bottom", pady=5)

        self.CreateConfigSection(self.result_frame)

        self.result_table = ResultTable(self.result_frame, page_size = 500) #Change page_size to determine how many rows displayed at once
        self.result_table.pack(fill="both", expand=True)

        self.wave_animation = WaveAnimation(animation_frame)
        self.wave_animation.pack(fill="both", expand=True)

    def CreateReadBenchmarkTab(self):
        toolbar = ttk.Frame(self.read_benchmark_tab, padding=8)
        toolbar.pack(fill="x")

        #Whenver need button as reference, do not pack it on same line as creation and assign to variable, cus pack return None
        open_run_button = ttk.Button(toolbar, text = "Open run folder", command = self.OnOpenBenchmarkRun)
        open_run_button.pack(side="left", padx=(0, 8))
        AddToolTip(open_run_button, READ_BENCHMARK_HELP["open_run"])

        self.read_benchmark_folder_button = ttk.Button(toolbar, text = "Open results folder", command = self.OpenBenchmarkResultsFolder, state = "disabled")
        self.read_benchmark_folder_button.pack(side = "left")

        #Recover disrupted benchmark button
        recover_button = ttk.Button(toolbar, text = "Recover runs", command = self.ShowBenchmarkRecovery)
        recover_button.pack(side = "left", padx = (8,0))
        AddToolTip(recover_button, READ_BENCHMARK_HELP["recover"])

        #resume benchmark button
        self.resume_benchmark_button = ttk.Button(toolbar, text="Resume loaded run", 
                                                  command=self.OnResumeBenchmarkRun, state="disabled")
        self.resume_benchmark_button.pack(side="left", padx=(8, 0))

        AddToolTip(self.read_benchmark_folder_button, READ_BENCHMARK_HELP["open_folder"])
        AddToolTip(self.resume_benchmark_button, READ_BENCHMARK_HELP["resume"])

        self.read_benchmark_path = tk.StringVar(value = "Open a saved run folder or save a new benchmark run.")
        ttk.Label(toolbar, textvariable = self.read_benchmark_path, wraplength = 650).pack(side = "left", padx = 12)
        self.benchmark_results_view = BenchmarkResults(self.read_benchmark_tab)
        self.benchmark_results_view.pack(fill = "both", expand = True, padx = 8, pady = (0,8))

    def CreateBenchmarkTab(self):
        """
        tab = self.benchmark_tab
        self.benchmark_panes = ttk.Panedwindow(tab, orient = "vertical")
        self.benchmark_panes.pack(fill = "both", expand = True)
        top = ttk.Frame(self.benchmark_panes, padding = 10)
        self.benchmark_panes.add(top, weight = 3)
        """
        top = ttk.Frame(self.benchmark_tab, padding = 10)
        top.pack(fill = "both", expand = True)

        top.columnconfigure(1, weight=1)
        top.rowconfigure(0, weight=1)

        #Right: console for messages
        console_frame = ttk.LabelFrame(top, text="Benchmark Console", padding=5)
        console_frame.grid(row=0, column=1, sticky="nsew", padx= (15, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)

        self.benchmark_console = tk.Text(console_frame, width=32, height=10, wrap = "word")
        self.benchmark_console.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.benchmark_console.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.benchmark_console.configure(yscrollcommand=scrollbar.set)
        self.benchmark_console.insert("end", "Ready to configure a benchmark.\n")
        self.benchmark_console.configure(state="disabled")

        self.benchmark_stop_event = None #Event to stop a benchmark

        #Left: benchmark inputs
        self.benchmark_config_frame = ttk.LabelFrame(top, text="Benchmark Configuration", padding=8)
        self.benchmark_config_frame.grid(row=0, column=0, sticky="nsew")
        self.benchmark_config_frame.columnconfigure(1, weight=1)

        self.benchmark_n_values = tk.StringVar(value="500, 1000")
        self.benchmark_dt_values = tk.StringVar(value="1, 2")

        for row, (label, variable, help_key) in enumerate([
                                ("N values:", self.benchmark_n_values, "N_values"),
                                ("dt values:", self.benchmark_dt_values, "dt_values")]):

            ttk.Label(self.benchmark_config_frame, text=label).grid(row=row, column=0, padx=(0,8), pady=3, sticky="w")
            entry = ttk.Entry(self.benchmark_config_frame, textvariable=variable)
            entry.grid(row = row, column = 1, pady = 3, sticky = "ew")
            AddToolTip(entry, BENCHMARK_HELP[help_key])
            
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
            AddToolTip(entry, NUMERICAL_HELP[name])
            if name in ("mass", "hbar"):
                checkbox = self.CreateConstantCheckbox(numerical_frame, entry, name)
                checkbox.grid(row = row, column = 2, sticky = "w", padx = (6, 0), pady = 2)
        
        #Make the boundary condition dropdown
        ttk.Label(numerical_frame, text = "Boundary").grid(row = 5, column = 0, sticky = "w", padx = (0, 8), pady = 2)

        self.benchmark_boundary = tk.StringVar(value = "Periodic")
        self.benchmark_boundary_dropdown = ttk.Combobox(numerical_frame, textvariable = self.benchmark_boundary,
                                                            values = BOUNDARY_CONDITIONS, state = "readonly")
        self.benchmark_boundary_dropdown.grid(row = 5, column = 1, columnspan = 2, sticky = "ew", pady = 2)

        AddToolTip(self.benchmark_boundary_dropdown, BENCHMARK_HELP["boundary_condition"])

        #Make new self field for wave/ pot types cus self.wave_type depends on entry in simulation tab
        self.benchmark_wave_type, self.benchmark_wave_entries, self.RefreshBenchmarkWaveFields = ( 
            self.CreateBenchmarkPresetSection("Wave Function", WAVE_PARAMETERS, row = 4))

        self.benchmark_potential_type, self.benchmark_potential_entries, self.RefreshBenchmarkPotentialFields = ( 
            self.CreateBenchmarkPresetSection("Potential", POTENTIAL_PARAMETERS, row = 5))

        #Make self.RefreshBenchmarkBoundary() a listener to self.benchmark_potential_type
        self.benchmark_potential_type.trace_add("write", lambda *_: self.RefreshBenchmarkBoundary()) 
        self.RefreshBenchmarkBoundary()


        ttk.Button(self.benchmark_config_frame, text="Preview problem",
                   command=self.PreviewBenchmarkSweep).grid(row=6, columnspan=2, sticky="ew", pady=(10,0))

        #Put problem frame beneath console on the right (row 1)
        self.benchmark_problems = {}
        self.benchmark_problem_name = tk.StringVar()

        problems_frame = ttk.LabelFrame(console_frame, text = "Problems in this run", padding = 6)
        problems_frame.grid(row = 1, column = 0, columnspan = 2, sticky = "ew", pady = (8,0))
        problems_frame.columnconfigure(1, weight = 1)

        ttk.Label(problems_frame, text = "Problem name").grid(row = 0, column = 0, sticky = "w", padx = (0, 8))
        problem_name_entry = ttk.Entry(problems_frame, textvariable = self.benchmark_problem_name)
        problem_name_entry.grid(row=0, column=1, sticky="ew")
        AddToolTip(problem_name_entry, BENCHMARK_HELP["problem_name"])
        
        ttk.Button(problems_frame, text = "Add / Update",
                   command = self.AddBenchmarkProblem).grid(row = 0, column = 2, padx = (8,0))

        self.benchmark_problem_list = tk.Listbox(problems_frame, height = 5, exportselection = False)
        self.benchmark_problem_list.grid(row = 1, column = 0, columnspan = 3, sticky = "ew", pady = 6)
        AddToolTip(self.benchmark_problem_list, BENCHMARK_HELP["problem_list"])

        ttk.Button(problems_frame, text = "Load selected into form", command = self.LoadSelectedBenchmarkProblem).grid(row = 2, column = 0, columnspan = 2, sticky = 'w')
        ttk.Button(problems_frame, text = "Remove selected", command = self.RemoveBenchmarkProblem).grid(row = 2, column = 2, sticky = 'e')
        ttk.Button(problems_frame, text = "Preview run", command = self.PreviewBenchmarkRun).grid(row = 3, column = 0, columnspan = 3, sticky = "ew", pady = (6, 0))
        
        #Frame that collect the entire benchmark run 
        self.benchmark_run_config_frame = ttk.LabelFrame(console_frame, text="Run Configuration", padding=6)
        self.benchmark_run_config_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.benchmark_run_config_frame.columnconfigure(1, weight=1)

        self.benchmark_run_name = tk.StringVar()

        ttk.Label(self.benchmark_run_config_frame, text="Configuration name").grid(row=0, column=0, sticky="w", padx=(0, 8))
        run_name_entry = ttk.Entry(self.benchmark_run_config_frame,textvariable=self.benchmark_run_name)
        run_name_entry.grid(row=0, column=1, sticky="ew")
        AddToolTip(run_name_entry, BENCHMARK_HELP["configuration_name"])
        ttk.Button(self.benchmark_run_config_frame,text="Save run configuration",command=self.OnSaveBenchmarkConfig).grid(row=0, column=2, padx=(8, 0))

        self.benchmark_saved_config = tk.StringVar()
        self.benchmark_last_selected_config = ""

        ttk.Label(self.benchmark_run_config_frame,text="Saved configurations").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)

        self.benchmark_config_dropdown = ttk.Combobox(self.benchmark_run_config_frame, textvariable=self.benchmark_saved_config, state="readonly")
        self.benchmark_config_dropdown.grid(row=1, column=1, sticky="ew", pady=5)
        self.benchmark_config_dropdown.bind("<<ComboboxSelected>>", self.OnBenchmarkConfigSelected)
        AddToolTip(self.benchmark_config_dropdown, BENCHMARK_HELP["saved_configuration"])

        #Button to load benchmark
        ttk.Button(self.benchmark_run_config_frame, text = "Load", command = self.OnLoadBenchmarkConfig).grid(row = 1, column = 2, padx = (8,0), pady = 5)
        


        #Button to run benchmark
        self.benchmark_future = None
        self.benchmark_save_future = None
        self.benchmark_temp_directory = None
        self.benchmark_manifest = None

        self.start_benchmark_button = ttk.Button(self.benchmark_run_config_frame, text = "Start run", command = self.OnStartBenchmarkRun)
        self.start_benchmark_button.grid(row = 2, column = 0, columnspan = 3, sticky = "ew", pady = (8, 0))

        #Stop benchmark button
        self.stop_benchmark_button = ttk.Button(self.benchmark_run_config_frame, text="Stop after current combination",
                                            command=self.OnStopBenchmarkRun, state="disabled")
        self.stop_benchmark_button.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(5, 0))

        try:
            self.RefreshBenchmarkConfigList()
        except (OSError, ValueError) as error:
            messagebox.showerror("Cannot read benchmark configurations", str(error), parent=self)

        #Button to save results
        self.benchmark_saved_folder = None
        self.benchmark_saved_manifest = None
        self.open_benchmark_folder_button = ttk.Button(self.benchmark_run_config_frame, text = "Open results folder",
                                                       command = self.OpenBenchmarkResultsFolder, state = "disabled")
        self.open_benchmark_folder_button.grid(row = 4, column = 0, columnspan = 3, sticky = "ew", pady = (5,0))


        #Result frame has been moved to ReadBenchmark tab
        """
        self.benchmark_results_frame = ttk.LabelFrame(self.benchmark_panes, text="Benchmark Results", padding=8)
        self.benchmark_results_view = BenchmarkResults(self.benchmark_results_frame)
        self.benchmark_results_view.pack(fill="both", expand=True)
        """

    #Methods for Benchmark Tab -----------------------------------------

    #Save, delete and load benchmark configs
    def RefreshBenchmarkProblems(self, selected_name = None): #Refresh problem list (called when add, delete, or load)
        problem_list = self.benchmark_problem_list
        problem_list.delete(0, tk.END) #reset the list

        for idx, name in enumerate(self.benchmark_problems):
            problem_list.insert(tk.END, name)
            if name == selected_name:
                problem_list.selection_set(idx)
                problem_list.see(idx)

    def AddBenchmarkProblem(self):
        name = self.benchmark_problem_name.get().strip()

        if not name:
            messagebox.showerror("Missing problem name", parent = self)
            return

        try:
            config, n_values, dt_values = self.BuildBenchmarkConfig()
             
            config = self.Check_SSF_Limitation_BenchmarkProblem(config, n_values)
            if config is None:
                return
            """
            for n in n_values:
                BuildBenchmarkProblem(replace(config, N = n)) #Try build it
            """  #These are built inside Check_SSF_Limitation_BenchmarkProblem
            
        except ValueError as e:
            messagebox.showerror("Invalid benchmark problem,", str(e), parent = self)
            return

        #If already in
        if name in self.benchmark_problems:
            overwrite = messagebox.askyesno("Update problem", f"Replace '{name}' with current values?", parent = self)
            if not overwrite:
                return
        
        self.benchmark_problems[name] = config
        self.RefreshBenchmarkProblems(selected_name = name)

    def ApplyBenchmarkProblem(self, config): #Fill the blanks
        def fill(entry, value):
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
        
        for name, entry in self.benchmark_numerical_entries.items():
            fill(entry, getattr(config, name))

        self.benchmark_wave_type.set(config.wave_type)
        self.RefreshBenchmarkWaveFields()

        for name, entry in self.benchmark_wave_entries.items():
            fill(entry, config.wave_parameters[name])

        self.benchmark_potential_type.set(config.potential_type)
        self.RefreshBenchmarkPotentialFields()

        for name, entry in self.benchmark_potential_entries.items():
            fill(entry, config.potential_parameters[name])

        self.benchmark_boundary.set(config.boundary_condition)
        self.RefreshBenchmarkBoundary()

    def LoadSelectedBenchmarkProblem(self):
        selection = self.benchmark_problem_list.curselection()
        if not selection:
            return
        
        name = self.benchmark_problem_list.get(selection[0])
        config = self.benchmark_problems[name]

        self.ApplyBenchmarkProblem(config)
        self.benchmark_problem_name.set(name)


    def RemoveBenchmarkProblem(self):
        selection = self.benchmark_problem_list.curselection()
        if not selection:
            return

        name = self.benchmark_problem_list.get(selection[0])
        del self.benchmark_problems[name]
        self.RefreshBenchmarkProblems()

    def RefreshBenchmarkConfigList(self, selected=None): #Refresh the run list (called when a run is saved or removed)
        names = sorted(ReadBenchmarkConfigurations(), key=str.casefold)

        self.benchmark_config_dropdown.configure(values=["Open configuration folder...", *names])

        if selected not in names:
            selected = names[0] if names else ""

        self.benchmark_last_selected_config = selected
        self.benchmark_saved_config.set(selected)

    def OnBenchmarkConfigSelected(self, event=None):
        if self.benchmark_config_dropdown.current() != 0:
            self.benchmark_last_selected_config = (self.benchmark_saved_config.get())
            return

        self.benchmark_saved_config.set(self.benchmark_last_selected_config)

        try:
            folder = BENCHMARK_CONFIG_FILE.parent
            folder.mkdir(parents=True, exist_ok=True)
            os.startfile(folder)
        except OSError as error:
            messagebox.showerror("Cannot open configuration folder", str(error), parent=self)


    def ReadSavedBenchmarkRun(self, name):
        saved = ReadBenchmarkConfigurations()

        if name not in saved:
            raise ValueError(f"Can't find name '{name}' among saved configurations.")

        run = saved[name]
        if not isinstance(run, dict) or run.get("version") != 1:
            raise ValueError("This benchmark configuration format is not supported.")

        n_values = run["N_values"]
        dt_values = run["dt_values"]
        
        #Check N and dt
        if not isinstance(n_values, list) or not n_values:
            raise ValueError("Saved list of N must be a list and must contain values.")
        if not isinstance(dt_values, list) or not dt_values:
            raise ValueError("Saved list of dt must be a list and must contain values.")

        for n in n_values:
            if type(n) is not int or not 3 <= n <= MAX_GRID_POINTS:
                raise ValueError(f"Saved N must be integers from 3 to {MAX_GRID_POINTS}.")
        for dt in dt_values:
            if type(dt) not in (int, float) or not math.isfinite(dt) or dt <= 0:
                raise ValueError(f"Saved dt must be finite and positive numbers.")

        if len(set(n_values)) != len(n_values):
            raise ValueError("The saved N list contains duplicates.")
        if len(set(dt_values)) != len(dt_values):
            raise ValueError("The saved dt list contains duplicates.")

        saved_problems = run["problems"]
        if not isinstance(saved_problems, dict) or not saved_problems:
            raise ValueError("The saved run must contain at least one problem.")

        problems = {}

        #Check numericals in each problem
        for problem_name, data in saved_problems.items():

            if not isinstance(problem_name, str) or not problem_name.strip():
                raise ValueError("Each saved problem needs a name.")
            if not isinstance(data, dict):
                raise ValueError(f"Invalid configuration for '{problem_name}'.")

            config = SimulationConfig(**data)

            for field in ("mass", "hbar", "x_min", "x_max", "T_final"):
                value = getattr(config, field)
                if type(value) not in (int, float) or not math.isfinite(value):
                    raise ValueError(f"Problem '{problem_name}': {field} must be finite.")
            
            if min(config.mass, config.hbar, config.T_final) <= 0:
                raise ValueError(f"Problem '{problem_name}': mass, hbar, T_final must be positive.")

            if config.x_max <= config.x_min:
                raise ValueError(f"Problem '{problem_name}': use x_max > x_min.")

            if config.wave_mode != "Preset":
                raise ValueError("Benchmark loading currently only supports presets.")

            #Now check the parameters
            for selected, parameters, definitions in ((config.wave_type, config.wave_parameters, WAVE_PARAMETERS),
                                                      (config.potential_type, config.potential_parameters, POTENTIAL_PARAMETERS)):
                
                expected = definitions[selected] #the dict of expected parameter types
                if not isinstance(parameters, dict) or parameters.keys() != expected.keys():
                    raise ValueError(f"Problem '{problem_name}': invalid parameters for {selected}.")

                for field, expected_type in expected.items():
                    value = parameters[field]
                    allowed = (int,) if expected_type is int else (int, float) #Need (int,) so it's a tuple and not just... int, got an exception cus of that
                    if type(value) not in allowed or not math.isfinite(value):
                        raise ValueError(f"Problem '{problem_name}': {field} needs to be {allowed} and finite.")

            for dt in dt_values:
                self.BenchmarkStepCheck(config.T_final, dt) #Check T_final to be whole number of dt

            for n in n_values:
                BuildBenchmarkProblem(replace(config, N=n, dt=dt_values[0])) #Try building it with any dt to catch the errors

            problems[problem_name] = replace(config, N=n_values[0], dt=dt_values[0]) #[0] here is only to fill the SimulationConfig type

        return problems, n_values, dt_values

    def OnLoadBenchmarkConfig(self):
        name = self.benchmark_saved_config.get()
        if not name:
            messagebox.showerror("No configuration selected","Select a saved run configuration.",parent=self)
            return
        try:
            problems, n_values, dt_values = self.ReadSavedBenchmarkRun(name)
        except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
            messagebox.showerror("Cannot load benchmark configuration", str(error), parent=self)
            return

        if self.benchmark_problems:
            replace_current = messagebox.askyesno("Load configuration", "Replace current problem list and form values with this saved run?", parent = self)

            if not replace_current:
                return
        #Fill
        self.benchmark_problems = problems
        self.benchmark_n_values.set(", ".join(map(str, n_values)))
        self.benchmark_dt_values.set(", ".join(map(str, dt_values)))
        self.benchmark_run_name.set(name)

        first_name = next(iter(problems)) #Select one problem to show
        self.RefreshBenchmarkProblems(selected_name=first_name)
        self.ApplyBenchmarkProblem(problems[first_name])
        self.benchmark_problem_name.set(first_name)
 
        console = self.benchmark_console
        console.configure(state="normal")
        console.insert("end",f"Loaded run configuration '{name}' with {len(problems)} problems.\n")
        console.see("end")
        console.configure(state="disabled")

    def OnSaveBenchmarkConfig(self):
        name = self.benchmark_run_name.get().strip()
        if not name:
            messagebox.showerror("Missing configuration name", "Enter a name for this run configuration.",parent=self)
            return

        try:
            run = self.BuildBenchmarkRunConfig()

            if name in ReadBenchmarkConfigurations():
                overwrite = messagebox.askyesno("Replace configuration",
                        f"Replace the saved run configuration '{name}'?",parent=self,)
                if not overwrite:
                    return

            SaveBenchmarkConfiguration(name, run)
            self.RefreshBenchmarkConfigList(selected = name)

        except (OSError, ValueError, TypeError) as error:
            messagebox.showerror(
                "Cannot save benchmark configuration", str(error), parent=self
            )
            return

        console = self.benchmark_console
        console.configure(state="normal")
        console.insert("end",f"Saved run configuration '{name}' with {len(run['problems'])} problems.\nFile: {BENCHMARK_CONFIG_FILE}\n")
        console.see("end")
        console.configure(state="disabled")

    
    def AppendBenchmarkConsoleMessage(self, message):
        console = self.benchmark_console
        console.configure(state = "normal")
        console.insert("end", message + "\n")
        console.see("end")
        console.configure(state = "disabled")

    def OnStartBenchmarkRun(self):
        if self.benchmark_future is not None: #something is already running
            return

        try: 
            run = self.BuildBenchmarkRunConfig()

            #Handle problems without analytical reference
            missing_references = [name for name, data in run["problems"].items() 
                                  if not HasBenchmarkReference(SimulationConfig(**data))]
            if missing_references:
                problem_list = "\n".join(f"- {name}" for name in missing_references)
                proceed = messagebox.askyesno("Analytical reference unavailable",
                    "No analytical reference is implemented for these problem settings:\n\n"
                    f"{problem_list}\n\n"
                    "Their CN and SSF L2 error columns will contain N/A. L2 error graphs and L2-based accuracy comparisons will be unavailable.\n\n"
                    "Norm, position, momentum, energy, and execution time will still be calculated and available for inspection and comparison.\n\n"
                    "Proceed with this run?", parent = self)
                if not proceed:
                    return


            #self.benchmark_temp_directory = TemporaryDirectory(prefix = "SchorodingerBenchmark_") #temporary until user save
            self.benchmark_temp_directory = BenchmarkWorkingDirectory()
        except (OSError, ValueError) as e:
            messagebox.showerror("Cannot start benchmark", str(e), parent = self)
            return

        self.benchmark_progress = Queue()
        self.benchmark_stop_event = Event()
        self.start_benchmark_button.configure(state = "disabled", text = "Running...")
        self.AppendBenchmarkConsoleMessage(f"Starting run with {len(run["problems"])} problems")

        worker = ThreadPoolExecutor(max_workers = 1) #Run in a thread as not to freeze app (beware some runs can take up to an hour)
        try: 
            self.benchmark_future = worker.submit(
                    RunBenchmarkConfiguration,
                    run,
                    self.benchmark_temp_directory.name, #output path
                    self.benchmark_progress,
                    self.benchmark_stop_event)
            self.stop_benchmark_button.configure(state = "normal", text = "Stop after current combination")
        except Exception as e:
            self.benchmark_temp_directory.cleanup()
            self.benchmark_temp_directory = None
            self.start_benchmark_button.configure(state = "normal", text = "Start run")
            messagebox.showerror("Cannot start benchmark", str(e), parent = self)
            return
        finally:
            worker.shutdown(wait = False)
        self.after(100, self.PollBenchmarkRun)
    

    def PollBenchmarkRun(self):

        #Display 100 messages per call  
        for _ in range(100):
            try: 
                message = self.benchmark_progress.get_nowait() #retrive first from queue
            except Empty:
                break
            self.AppendBenchmarkConsoleMessage(message)

        #if haven't finished running benchmarks or not printing the progress queue out
        if not self.benchmark_future.done() or not self.benchmark_progress.empty(): 
            self.after(100, self.PollBenchmarkRun)
            return

        self.stop_benchmark_button.configure(state = "disabled", text = "Stop after current combination")
        try:
            self.benchmark_manifest = self.benchmark_future.result()
        except Exception as e:
            #Run fails, reset variables except cleaning the temp_directory  
            recovery_folder = self.benchmark_temp_directory.name
            self.AppendBenchmarkConsoleMessage(f"Run failed: {e}\nRecovery files retained at \n{recovery_folder}")
            
            self.benchmark_temp_directory = None
            self.benchmark_future = None
            self.benchmark_manifest = None
            self.benchmark_stop_event = None

            self.start_benchmark_button.configure(state="normal", text="Start run", command = self.OnStartBenchmarkRun)

            messagebox.showerror("Benchmark failed", f"{str(e)}\n\nCompleted checkpoints have been retained at\n{recovery_folder}", parent=self)
            return
            
        if self.benchmark_manifest["status"] == "stopped":
            self.AppendBenchmarkConsoleMessage("Partial results are ready to save.")
        else:
            self.AppendBenchmarkConsoleMessage("Run completed.")
        self.start_benchmark_button.configure(state = "normal", text = "Save / discard completed run", command = self.OfferBenchmarkSave)
        self.OfferBenchmarkSave()

    def OfferBenchmarkSave(self): #When save button is pressed
        stopped = self.benchmark_manifest.get("status") == "stopped" #check if run was stopped
        completed = len(self.benchmark_manifest["results"])
        total = self.benchmark_manifest["total_combinations"]


        save = messagebox.askyesno("Benchmark stopped" if stopped else "Benchmark completed",
                    f"{completed}/{total} combinations completed.\n\nSave this run's results and configuration?\n\n"
                    "Choose No to discard the temporary results.", parent=self)
        if not save:
            self.AppendBenchmarkConsoleMessage("Completed run discarded.")
            self.ReleaseCompletedBenchmark()
            return

        parent_folder = filedialog.askdirectory(title = "Choose where to save the benchmark run", parent = self, mustexist = True)
        if not parent_folder:
            #Do nothing, user can open that again through the button
            return
        self.start_benchmark_button.configure(state = "disabled", text = "Saving results...")

        #Try save
        worker = ThreadPoolExecutor(max_workers=1)
        try:
            self.benchmark_save_future = worker.submit(SaveBenchmarkResults, self.benchmark_temp_directory.name, parent_folder)
        except Exception as error:
            self.start_benchmark_button.configure(state="normal", text="Save / discard completed run")
            messagebox.showerror("Cannot start saving", str(error), parent=self)
            return
        finally:
            worker.shutdown(wait=False)
        self.after(100, self.PollBenchmarkSave)


    def OnOpenBenchmarkRun(self):
        selected_folder = filedialog.askdirectory(title = "Select the run folder containing run.json", parent = self, mustexist = True)
        if not selected_folder:
            return

        folder = Path(selected_folder)

        try:
            manifest = ReadBenchmarkManifest(folder)
        except (OSError, ValueError, TypeError, OverflowError) as error:
            messagebox.showerror("Cannot open benchmark run",str(error),parent=self)
            return

        self.DisplayBenchmarkRun(folder, manifest)



    def DisplayBenchmarkRun(self, folder, manifest): #Method to let this script know the folder and results
        self.benchmark_saved_folder = folder
        self.benchmark_saved_manifest = manifest

        self.benchmark_results_view.LoadRun(folder, manifest)

        #Check if benchmark is completed
        configuration = manifest["configuration"]
        total = (len(configuration["problems"]) * len(configuration["N_values"]) * len(configuration["dt_values"]))
        completed = len(manifest["results"])

        #open up the resume button if the benchmark is incompleted
        self.resume_benchmark_button.configure(state="normal" if completed < total else "disabled")

        status = "Completed" if completed == total else "Partial"
        self.read_benchmark_path.set(
            f"{folder}\n{status}: {completed}/{total} combinations"
        )

        self.open_benchmark_folder_button.configure(state="normal")
        self.read_benchmark_folder_button.configure(state="normal")
        self.notebook.select(self.read_benchmark_tab) #jump to ReadBenchmark tab

    def PollBenchmarkSave(self):
        if not self.benchmark_save_future.done():
            self.after(100, self.PollBenchmarkSave)
            return

        try:
            saved_folder = self.benchmark_save_future.result()
        except Exception as e:
            self.benchmark_save_future = None
            self.AppendBenchmarkConsoleMessage(f"Saving failed: {e}")
            messagebox.showerror("Cannot save results", f"{e}\n\nThe temporary results are available for retry.", parent=self)
            self.start_benchmark_button.configure(state = "normal", text = "Save / discard completed run")
            return

        
        """self.benchmark_saved_folder = saved_folder
        self.benchmark_saved_manifest = self.benchmark_manifest
        self.open_benchmark_folder_button.configure(state="normal")

        self.AppendBenchmarkConsoleMessage(f"Results saved to:\n{saved_folder}")
        self.ReleaseCompletedBenchmark()

        #Show the graph selection frame
        if str(self.benchmark_results_frame) not in self.benchmark_panes.panes():
            self.benchmark_panes.add(self.benchmark_results_frame, weight=2)
            self.after_idle(self.PositionBenchmarkDivider)

        self.benchmark_results_view.LoadRun(self.benchmark_saved_folder, self.benchmark_saved_manifest)"""

        manifest = self.benchmark_manifest
        self.AppendBenchmarkConsoleMessage(f"Results saved to:\n{saved_folder}")
        self.ReleaseCompletedBenchmark()
        self.DisplayBenchmarkRun(saved_folder, manifest)

    """ NOT NEEDED after result_view was removed from Benchmark tab
    def PositionBenchmarkDivider(self):  
        height = self.benchmark_panes.winfo_height()
        self.benchmark_panes.sashpos(0, int(height * 0.60))
    """

    #Method to reset the temporary folder
    def ReleaseCompletedBenchmark(self):
        try:
            self.benchmark_temp_directory.cleanup()
        except OSError as error:
            self.AppendBenchmarkConsoleMessage(f"Could not fully remove temporary files: {error}")

        self.benchmark_save_future = None
        self.benchmark_temp_directory = None
        self.benchmark_future = None
        self.benchmark_manifest = None
        self.benchmark_stop_event = None
        self.start_benchmark_button.configure(state="normal", text="Start run", command=self.OnStartBenchmarkRun)

    def OpenBenchmarkResultsFolder(self):
        if self.benchmark_saved_folder is None:
            return
        try:
            os.startfile(self.benchmark_saved_folder)
        except OSError as error:
            messagebox.showerror("Cannot open results folder", str(error), parent=self)




    def PreviewBenchmarkRun(self):
        try:
            run = self.BuildBenchmarkRunConfig()
        except ValueError as e:
            messagebox.showerror("Invalid benchmark run,", str(e), parent = self)
            return

        problem_count = len(run["problems"])
        combinations = (problem_count * len(run["N_values"]) * len(run["dt_values"]))

        console = self.benchmark_console
        console.configure(state="normal")
        console.insert("end",f"Run preview: {problem_count} problems, {combinations} problem/N/dt combinations.\n")
        for name, data in run["problems"].items():
            console.insert("end", f"  {name} — Boundary: {data['boundary_condition']}\n")
        console.see("end")
        console.configure(state="disabled")
        

    def BuildBenchmarkRunConfig(self):
        if not self.benchmark_problems:
            raise ValueError("Add at least one problem to the run.")

        n_values, dt_values = self.ReadBenchmarkSweep()
        problems = {}

        #Check each
        for name, config in self.benchmark_problems.items():
            try:
                for dt in dt_values:
                    self.BenchmarkStepCheck(config.T_final, dt)

                for n in n_values:
                    BuildBenchmarkProblem(replace(config, N=n))

            except ValueError as error:
                raise ValueError(f"Problem '{name}': {error}") from None

            # Store current initial sweep values in config.
            saved_config = replace(config, N=n_values[0], dt=dt_values[0])
            problems[name] = asdict(saved_config) #Need asdict so can save to json

        return {
            "version": 1,
            "N_values": n_values,
            "dt_values": dt_values,
            "problems": problems,
        }

    
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

        #Check the parsed N and dt 
        for n in n_values:
            if not 3 <= n <= MAX_GRID_POINTS:
                raise ValueError(f"N must be between 3 and {MAX_GRID_POINTS}. Got {n} among them.")
        for dt in dt_values:
            if not math.isfinite(dt) or dt <= 0: #Use math not np cus dt is scalar
                raise ValueError(f"dt must be finite and positive. Got {dt}.")

        return n_values, dt_values

    #Check T and dt are valid
    def BenchmarkStepCheck(self, T, dt):
        if not math.isfinite(T) or T <= 0:
            raise ValueError("T_final must be finite and positive.")
        ratio = T / dt
        if not math.isfinite(ratio) or ratio > MAX_STEPS:
            #:g is useful, it drop trailing zeroes
            raise ValueError(f"dt = {dt:g} exceeds the limit of {MAX_STEPS} steps.\nPlease reduce T_final or increase dt.") 
        
        steps = round(ratio)
        if steps < 1 or abs(ratio - steps) > 1e-10:
            raise ValueError(f"T_final must be whole number of steps for dt = {dt:g}.")
        return steps

    def BuildBenchmarkConfig(self):

        n_values, dt_values = self.ReadBenchmarkSweep()

        #Read out the numericals
        numerical = {}
        for name, entry in self.benchmark_numerical_entries.items():
            numerical[name] = self.ReadEntry(entry, name, float)

        #Read out the wave inputs
        wave_type = self.benchmark_wave_type.get()
        wave_parameters = {}
        for name, expected_type in WAVE_PARAMETERS[wave_type].items():
            wave_parameters[name] = self.ReadEntry(self.benchmark_wave_entries[name], f"Wave function / {name}", expected_type)
        
        #Read out the potential inputs
        potential_type = self.benchmark_potential_type.get()
        potential_parameters = {}
        for name, expected_type in POTENTIAL_PARAMETERS[potential_type].items():
            potential_parameters[name] = self.ReadEntry(self.benchmark_potential_entries[name], f"Potential / {name}", expected_type)
        
        #Checking the numbers
        for name, value in numerical.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
        for parameters in (wave_parameters, potential_parameters):
            for name, value in parameters.items():
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError(f"{name} must be finite.")
        for name in ("mass", "hbar", "T_final"):
            if numerical[name] <= 0:
                raise ValueError(f"{name} must be positive.")
        if numerical["x_max"] <= numerical["x_min"]:
            raise ValueError("Use x_max > x_min")
        for dt in dt_values:
            self.BenchmarkStepCheck(numerical["T_final"], dt)
        if wave_type == "Gaussian Packet" and wave_parameters["sigma"] <= 0:
            raise ValueError("Gaussian Packet requires sigma > 0.")
        if wave_type == "Harmonic Oscillator Eigenstate" and (wave_parameters["n"] < 0 or wave_parameters["omega"] <= 0):
            raise ValueError("Harmonic Oscillator Eigenstate requires n >= 0 and omega > 0.")
        if potential_type == "Harmonic Oscillator" and potential_parameters["omega"] <= 0:
            raise ValueError("Harmonic Oscillator potential requires omega > 0.")
        if potential_type in ("Barrier", "Infinite Square Well") and (potential_parameters["x_left"] >= potential_parameters["x_right"]):
            raise ValueError("This potential type requires x_left < x_right.")


        config = SimulationConfig(
            **numerical,
            N = n_values[0],
            dt = dt_values[0],
            solver = "SSF",  #This is just to fill the field required by SimulationConfig (I want to reuse it)
            wave_mode = "Preset",
            wave_type = wave_type,
            wave_parameters = wave_parameters,
            potential_type = potential_type,
            potential_parameters = potential_parameters,
            boundary_condition = self.benchmark_boundary.get()
            )

        return config, n_values, dt_values

    def PreviewBenchmarkSweep(self):
        try:
            config, n_values, dt_values = self.BuildBenchmarkConfig()
            config = self.Check_SSF_Limitation_BenchmarkProblem(config, n_values)
            if config is None:
                return

            step_lines = []

            for dt in dt_values:
                steps = self.BenchmarkStepCheck(config.T_final, dt)
                step_lines.append(f"dt = {dt:g}: {steps} steps per solver.\n")

        except ValueError as e:
            messagebox.showerror("Invalid benchmark configuration: ", str(e), parent=self) #remember to add parent=self else it spawn new window on taskbar
            return
        
        count = len(n_values) * len(dt_values)
        console = self.benchmark_console
        console.configure(state="normal")
        console.insert("end",f"{config.wave_type} & {config.potential_type}\n"
                             f"Boundary: {config.boundary_condition}\n"
                             f"Sweep: {len(n_values)} N values x {len(dt_values)} dt values = {count} combinations.\n")
        console.insert("end", "".join(step_lines))
        console.see("end") #scroll down to "end" (tk.END)
        console.configure(state="disabled")
        
    def CreateBenchmarkPresetSection(self, title, definitions, row):
        frame = ttk.LabelFrame(self.benchmark_config_frame, text=title, padding= 6)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10,0))
        frame.columnconfigure(0, weight = 1)

        selected = tk.StringVar(master=frame, value=next(iter(definitions))) #Get a random one
        dropdown = ttk.Combobox(frame, textvariable=selected, values= list(definitions), state="readonly")
        dropdown.grid(row=0, column=0, sticky="ew")

        #Get the tooltip in
        if title == "Wave Function":
            parameter_help = WAVE_HELP
            selection_help = BENCHMARK_HELP["wave_type"]
        else:
            parameter_help = POTENTIAL_HELP
            selection_help = BENCHMARK_HELP["potential_type"]

        AddToolTip(dropdown, selection_help)

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
                AddToolTip(entry, parameter_help[selected.get()][name])

        dropdown.bind("<<ComboboxSelected>>", ShowParameters)
        ShowParameters()
        return selected, entries, ShowParameters #Get the ShowParameters so I can call it when loading a preset


    def OnStopBenchmarkRun(self):
        #if things are done
        if self.benchmark_future is None or self.benchmark_future.done() or self.benchmark_stop_event is None:
            return

        self.benchmark_stop_event.set()
        self.stop_benchmark_button.configure(state="disabled", text="Stopping after current combination...")
        self.AppendBenchmarkConsoleMessage("Stop command received. Waiting for the current combination to finish.")

    
    def OnResumeBenchmarkRun(self, source_folder = None):
        # Block resuming while results await save/discard.
        if self.benchmark_future is not None:
            messagebox.showinfo("Benchmark busy",
                "Finish the current run and save or discard its results first.", parent=self)
            return
        """
        if self.benchmark_saved_folder is None:
            return
        source_folder = Path(self.benchmark_saved_folder)
        """
        if source_folder is None:
            source_folder = self.benchmark_saved_folder
        if source_folder is None:
            return

        source_folder = Path(source_folder)
        recovering = IsRecoveryFolder(source_folder)

        try:
            #Read the saved file
            manifest = ReadBenchmarkManifest(source_folder, allow_running = recovering)
            if manifest["status"] == "completed" and not recovering:
                messagebox.showinfo("Run already completed",
                    "No missing combination to continue.", parent=self)
                return
            run = manifest["configuration"]
            
            for n in run["N_values"]:
                if not 3 <= n <= MAX_GRID_POINTS:
                    raise ValueError(f"N={n} is outside current supported range: 3-{MAX_GRID_POINTS}")
            
            for data in run["problems"].values():
                config = SimulationConfig(**data)
                for dt in run["dt_values"]:
                    self.BenchmarkStepCheck(config.T_final, dt)

            #self.benchmark_temp_directory = TemporaryDirectory(prefix="SchrodingerBenchmark_")
            self.benchmark_temp_directory = BenchmarkWorkingDirectory()


        except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
            messagebox.showerror("Cannot resume benchmark", str(error), parent=self)
            return

        self.benchmark_manifest = None
        self.benchmark_progress = Queue()
        self.benchmark_stop_event = Event()

        self.start_benchmark_button.configure(state = "disabled", text = "Resuming...")

        worker = None
        try: #resume the run
            worker = ThreadPoolExecutor(max_workers=1)
            self.benchmark_future = worker.submit(ResumeBenchmarkConfiguration,
                                                source_folder,
                                                self.benchmark_temp_directory.name,
                                                manifest,
                                                self.benchmark_progress,
                                                self.benchmark_stop_event)
        except Exception as e:
            self.ReleaseCompletedBenchmark() #reset everything
            messagebox.showerror("Cannot start resume", str(e), parent=self)
            return
        finally:
            if worker is not None:
                worker.shutdown(wait=False)

        #Allow stopping midrun, again
        self.stop_benchmark_button.configure(state="normal", text="Stop after current combination")
        self.AppendBenchmarkConsoleMessage(f"Resuming saved run:\n{source_folder}")
        self.notebook.select(self.benchmark_tab)
        self.after(100, self.PollBenchmarkRun)



    #Methods for Saving Configurations ---------------------------------------------------------
    def CreateConfigSection(self, parent):
        frame = ttk.LabelFrame(parent, text="Configuration Management")
        frame.pack(side = "top", fill="x", pady = (0,5))
        frame.columnconfigure(1, weight=1)

        #Save configuration 
        ttk.Label(frame, text="Configuration Name:").grid(row=0, column=0, padx=5, sticky="w")
        self.config_name = tk.StringVar()
        name_entry = ttk.Entry(frame, textvariable = self.config_name)
        name_entry.grid(row=0, column=1, padx=5, pady=3, sticky = "ew")
        AddToolTip(name_entry, SIMULATION_HELP["configuration_name"])
        ttk.Button(frame, text="Save", command=self.OnSaveConfig).grid(row=0, column=2, padx=5)

        #Load configuration
        ttk.Label(frame, text = "Saved Configurations: ").grid(row=1, column=0, padx=5, sticky="w")
        self.saved_config = tk.StringVar()
        self.config_dropdown = ttk.Combobox(frame, textvariable=self.saved_config, state="readonly")
        self.config_dropdown.grid(row=1, column=1, padx=5, pady = 3, sticky="ew")
        #stick the open folder option to top
        self.config_dropdown.bind("<<ComboboxSelected>>", self.OnConfigSelected)
        AddToolTip(self.config_dropdown, SIMULATION_HELP["saved_configuration"])
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

        self.simulation_boundary.set(config.boundary_condition)
        self.RefreshSimulationBoundary()

    #Methods for recoveing disrupted benchmark runs
    def CheckBenchmarkRecovery(self):
        try:
            folders = ListRecoveryFolders()
        except OSError as e:
            messagebox.showerror("Cannot check recovery files", str(e), parent = self)
            return
        if folders:
            self.ShowBenchmarkRecovery()

    def ShowBenchmarkRecovery(self):
        if self.benchmark_future is not None:
            messagebox.showinfo("Benchmark busy", "Finish current run and save or discard first.", parent = self)
            return

        if self.recovery_window is not None and self.recovery_window.winfo_exists():
            self.recovery_window.lift()
            return

        try:
            folders = ListRecoveryFolders()
        except OSError as e:
            messagebox.showerror("Cannot list recovery files", str(e), parent = self)
            return
        
        if not folders:
            messagebox.showinfo("Benchmark recovery", "No unfinished runs were found.", parent = self)
            return
        window = tk.Toplevel(self)
        self.recovery_window = window
        window.title("Recover benchmark runs")
        window.geometry("850x380")
        window.transient(self)
        ttk.Label(window, text = "Choose a recovery folder. Resume calculates missing combinations.\nFor a completed run, Resume / save opens the save workflow.",
                    padding = 10).pack(fill = "x")
        

        tree = ttk.Treeview(window, columns=("folder", "progress"), show="headings", selectmode="browse")
        tree.heading("folder", text="Recovery folder")
        tree.heading("progress", text="Checkpoint")
        tree.column("folder", width=380)
        tree.column("progress", width=400)
        tree.pack(fill="both", expand=True, padx=10)

        #Make tooltips for long checkpoint entries
        tooltip = None
        tooltip_item = None

        font_name = ttk.Style(tree).lookup("Treeview", "font")
        checkpoint_font = tkfont.Font(root = tree, font = font_name or "TkDefaultFont")
        def HideTooltip(event=None):
            nonlocal tooltip, tooltip_item
            if tooltip is not None:
                tooltip.destroy()
                tooltip = None
            tooltip_item = None

        def ShowCheckpointTooltip(event):
            nonlocal tooltip, tooltip_item

            item = tree.identify_row(event.y)
            column = tree.identify_column(event.x)

            if not item or column != "#2":
                HideTooltip()
                return

            bounds = tree.bbox(item, "progress")
            if not bounds:
                HideTooltip()
                return

            text = tree.set(item, "progress")
            cell_x, _, cell_width, _ = bounds
            visible_width = min(cell_width, tree.winfo_width() - cell_x)

            # No tooltip needed when whole message fits
            if checkpoint_font.measure(text) <= visible_width - 12:
                HideTooltip()
                return

            if tooltip_item == item:
                return

            HideTooltip()
            tooltip_item = item
            tooltip = tk.Toplevel(window)
            tooltip.withdraw()
            tooltip.overrideredirect(True)

            tk.Label(tooltip, text=text, justify="left", wraplength=500, background="#fff8d6", 
                     foreground="black", relief="solid", borderwidth=1, padx=8, pady=6).pack()

            tooltip.update_idletasks()

            x = event.x_root + 16
            y = event.y_root + 20

            # Keep the tooltip inside the recovery window.
            right = window.winfo_rootx() + window.winfo_width()
            bottom = window.winfo_rooty() + window.winfo_height()

            x = max(window.winfo_rootx(), min(x, right - tooltip.winfo_reqwidth()))
            if y + tooltip.winfo_reqheight() > bottom:
                y = max(window.winfo_rooty(), event.y_root - tooltip.winfo_reqheight() - 8)

            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()



        entries = {} #Look into the runs
        for index, folder in enumerate(folders):
            item_id = str(index)
            entries[item_id] = folder
            try:
                manifest = ReadBenchmarkManifest(folder, allow_running=True)
                description = (f"{manifest['completed_combinations']} / {manifest['total_combinations']} completed")
            except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
                description = f"Cannot recover: {error}"

            tree.insert("", "end", iid=item_id, values=(folder.name, description))

        def SelectedFolder():
            selection = tree.selection()
            return entries[selection[0]] if selection else None

        def CloseWindow():
            HideTooltip()
            window.grab_release()
            window.destroy()
            self.recovery_window = None

        def Inspect():
            folder = SelectedFolder()
            if folder is None:
                return
            try:
                manifest = ReadBenchmarkManifest(folder, allow_running=True)
            except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
                messagebox.showerror("Cannot inspect checkpoint", str(error), parent=window)
                return
            CloseWindow()
            self.DisplayBenchmarkRun(folder, manifest)

        def Resume():
            folder = SelectedFolder()
            if folder is None:
                return
            CloseWindow()
            self.OnResumeBenchmarkRun(source_folder=folder)

        def DeleteItems(item_ids):
            HideTooltip()
            errors = []

            for item_id in item_ids:
                folder = entries[item_id]
                try:
                    DeleteRecoveryFolder(folder)
                except (OSError, ValueError) as error:
                    errors.append(f"{folder.name}: {error}")
                    continue
                # Clear the viewer if its source was deleted.
                if self.benchmark_saved_folder is not None and Path(self.benchmark_saved_folder).resolve() == folder.resolve():
                    self.benchmark_saved_folder = None
                    self.benchmark_saved_manifest = None
                    self.benchmark_results_view.LoadRun(folder, {"results": []})
                    self.read_benchmark_path.set("No run loaded.")
                    self.resume_benchmark_button.configure(state="disabled")
                    self.open_benchmark_folder_button.configure(state="disabled")
                    self.read_benchmark_folder_button.configure(state="disabled")

                tree.delete(item_id)
                del entries[item_id]

            if errors:
                messagebox.showerror("Some recovery folders could not be deleted","\n\n".join(errors), parent=window)

            remaining = tree.get_children()
            if remaining:
                tree.selection_set(remaining[0])
            else:
                CloseWindow()

        def Delete():
            selection = tree.selection()
            if not selection:
                return
            folder = entries[selection[0]]
            if messagebox.askyesno("Delete recovery files?", f"Permanently delete this recovery folder?\n\n{folder}", parent=window):
                DeleteItems(list(selection))

        def DeleteAll():
            item_ids = list(tree.get_children())
            if not item_ids:
                return

            if messagebox.askyesno("Delete all recovery files?",
                f"Permanently delete all {len(item_ids)} recovery folders shown in this window?\n\n"
                "This includes any completed results stored in them.\nSeparately saved result folders will not be deleted.", parent=window):
                DeleteItems(item_ids)

        buttons = ttk.Frame(window, padding=10)
        buttons.pack(fill="x")

        ttk.Button(buttons, text="Resume / save", command = Resume).pack(side = "left")
        ttk.Button(buttons, text="Inspect", command = Inspect).pack(side = "left", padx = 8)
        ttk.Button(buttons, text="Delete", command = Delete).pack(side = "left")
        ttk.Button(buttons, text="Delete all", command = DeleteAll).pack(side = "left", padx = 8)
        ttk.Button(buttons, text="Later", command = CloseWindow).pack(side = "right")

        tree.selection_set(tree.get_children()[0])
        window.protocol("WM_DELETE_WINDOW", CloseWindow)
        window.grab_set()





    #Method for the wave input frame --------------------
    def CreateWaveSection(self):

        self.wave_frame = ttk.LabelFrame(self.input_frame,text="Wave Function")

        self.wave_frame.pack( fill="x", pady=5)

        #ttk.Label(self.wave_frame, text="Wave Function:").pack(anchor="w")

        self.wave_type = tk.StringVar()

        self.wave_input_mode = tk.StringVar(value="Preset")

        mode_row = ttk.Frame(self.wave_frame)
        mode_row.pack(fill="x", padx=5, pady=5)

        preset_button = ttk.Radiobutton(mode_row,
                    text="Preset",
                    variable=self.wave_input_mode,
                    value="Preset",
                    command=self.OnWaveInputModeChanged)
        preset_button.pack(side="left")
        AddToolTip(preset_button, SIMULATION_HELP["preset_mode"])

        expression_button = ttk.Radiobutton(mode_row,
                    text="Expression",
                    variable=self.wave_input_mode,
                    value="Expression",
                    command=self.OnWaveInputModeChanged)
        expression_button.pack(side="left", padx=10)
        AddToolTip(expression_button, SIMULATION_HELP["expression_mode"])

        self.wave_preset_frame = ttk.Frame(self.wave_frame)
        self.wave_preset_frame.pack(fill="x")

        self.wave_dropdown = ttk.Combobox(self.wave_preset_frame,
                                    textvariable=self.wave_type,
                                    values=list(WAVE_PARAMETERS.keys()),
                                    state="readonly")
        self.wave_dropdown.pack(fill="x",padx=5,pady=5)
        AddToolTip(self.wave_dropdown, SIMULATION_HELP["wave_type"])

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
        AddToolTip(self.wave_expression_entry, SIMULATION_HELP["expression"])

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
            AddToolTip(entry, WAVE_HELP[selected_wave][name])

    #Methods for the potential input frame --------------------
    def CreatePotentialSection(self):

        self.potential_frame = ttk.LabelFrame(self.input_frame,text="Potential")

        self.potential_frame.pack(fill="x", pady=5)
        self.potential_type = tk.StringVar()

        dropdown = ttk.Combobox(self.potential_frame,
                            textvariable=self.potential_type,
                            values=list(POTENTIAL_PARAMETERS.keys()),
                            state="readonly")
        dropdown.pack(fill="x",padx=5,pady=5)
        AddToolTip(dropdown, SIMULATION_HELP["potential_type"])

        self.potential_parameter_frame = (ttk.Frame(self.potential_frame))

        self.potential_parameter_frame.pack(fill="x")

        dropdown.bind("<<ComboboxSelected>>", self.OnPotentialSelected)

        self.potential_type.set(next(iter(POTENTIAL_PARAMETERS)))
        self.OnPotentialSelected()



    def OnPotentialSelected(self,event=None):

        self.RefreshSimulationBoundary()

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
            AddToolTip(entry, POTENTIAL_HELP[selected][name])

    #Methods for the numerical input frame --------------------
    def CreateNumericalSection(self):

        frame = ttk.LabelFrame(self.input_frame,text="Numerical Parameters")
        frame.pack(fill="x",pady=5)

        self.numerical_entries = {}

        parameters = ["mass",
                    "hbar",
                    "x_min",
                    "x_max",
                    "N",
                    "dt",
                    "T_final"]

        for name in parameters:

            row = ttk.Frame(frame)

            row.pack(fill="x",padx=5,pady=2)

            ttk.Label(row,text=f"{name}:",width=12).pack(side="left")

            entry = ttk.Entry(row)

            entry.pack(side="left",fill="x",expand=True)

            self.numerical_entries[name] = entry
            AddToolTip(entry, NUMERICAL_HELP[name])

            if name in ("mass", "hbar"): #Make constant checkboxes for mass and hbar
                checkbox = self.CreateConstantCheckbox(row, entry, name)
                checkbox.pack(side = "left", padx = (6, 0))


        #Boundary condition choice
        boundary_row = ttk.Frame(frame)
        boundary_row.pack(fill = "x", padx = 5, pady = 5)

        ttk.Label(boundary_row, text = "Boundary:", width = 12).pack(side = "left")

        self.simulation_boundary = tk.StringVar(master = self, value = "Periodic")

        self.simulation_boundary_dropdown = ttk.Combobox(boundary_row, textvariable = self.simulation_boundary, values = BOUNDARY_CONDITIONS, state = "readonly")
        self.simulation_boundary_dropdown.pack(side = "left", fill = "x", expand = True)

        AddToolTip(self.simulation_boundary_dropdown, SIMULATION_HELP["boundary_condition"])

        self.RefreshSimulationBoundary()
                
        #Solver choice
        solver_row = ttk.Frame(frame)

        solver_row.pack(fill="x",padx=5,pady=5)

        ttk.Label(solver_row,text="Solver:",width=12).pack(side="left")

        self.solver_type = tk.StringVar(value="SSF")
        #Drop down list for Solver
        solver_dropdown = ttk.Combobox(solver_row,
                            textvariable=self.solver_type,
                            values=["Crank-Nicolson", "SSF"],
                            state="readonly")
        solver_dropdown.pack(side="left",fill="x",expand=True)
        AddToolTip(solver_dropdown, SIMULATION_HELP["solver"])

        #Run button
        self.run_button = ttk.Button(frame,text="Run Simulation",command=self.OnRunSimulation)

        self.run_button.pack(pady=10)

    def RefreshSimulationBoundary(self):
        # Potential fields are created before the numerical section
        if not hasattr(self, "simulation_boundary_dropdown"):
            return
        #So set boundary condition automatically when ISW is selected
        if self.potential_type.get() == "Infinite Square Well":
            self.simulation_boundary.set("Dirichlet")
            self.simulation_boundary_dropdown.configure(state = "disabled")
        else:
            self.simulation_boundary_dropdown.configure(state = "readonly")

    def RefreshBenchmarkBoundary(self): #Force Dirichlet when ISW
        if self.benchmark_potential_type.get() == "Infinite Square Well":
            self.benchmark_boundary.set("Dirichlet")
            self.benchmark_boundary_dropdown.configure(state = "disabled")
        else:
            self.benchmark_boundary_dropdown.configure(state = "readonly")

    def Check_SSF_Limitation_BenchmarkProblem(self, config, n_values): #For Benchmark
        if config.potential_type == "Infinite Square Well":
            raise ValueError("Benchmark currently compares both CN and SSF. Use CN in Simulation for Infinite Square Well.\n\n" + INFINITE_WELL_SSF_MESSAGE)

        periodic_config = replace(config, boundary_condition = "Periodic")

        #Validate the proposed configuration 
        for n in n_values:
            BuildBenchmarkProblem(replace(periodic_config, N = n))

        if config.boundary_condition == "Dirichlet": #Ask for confirmation
            proceed = messagebox.askyesno("Change benchmark boundary?",
                                "FFT-based SSF uses periodic boundaries.\n\n"
                                "For a fair comparison, this benchmark must use periodic boundaries for both CN and SSF.\n\n"
                                "Switch this problem to periodic boundaries? The two ends will be connected instead of fixing the wave to zero at the ends. The grid spacing also changes for the same N and spatial limits.",
                                icon = "warning", default = "no", parent = self)
            if not proceed:
                return None

            self.benchmark_boundary.set("Periodic")

        return periodic_config

    #Methods for the run button ----------------------------------

    """
    Behavior involves Solver and boundary conditions:
    CN + Periodic	                        Runs periodically
    CN + Dirichlet	                        Runs with zero endpoints
    SSF + Periodic	                        Runs periodically
    SSF + Dirichlet -> Yes	                Changes the dropdown and calculation to Periodic, then runs
    SSF + Dirichlet -> No or close dialog	Does not run, preserves Dirichlet
    SSF + Infinite Square Well	            Shows the existing explanation and does not run
    """

    def OnRunSimulation(self):
        #If it should be stopped, don't run
        if self.close_requested or self.quit_prompt_open or self.simulation_future is not None or self.simulation_save_future is not None:
            return

        try:
            config = self.BuildSimulationConfig()

        except (ValueError, KeyError) as error:
            messagebox.showerror("Invalid Input",str(error))
            return

        if config.potential_type == "Infinite Square Well" and config.solver == "SSF":
            messagebox.showwarning(
                "Infinite Square Well requires Crank–Nicolson", INFINITE_WELL_SSF_MESSAGE, parent=self)
            return
        
        if config.solver == "SSF" and config.boundary_condition == "Dirichlet":
            proceed = messagebox.askyesno("SSF requires periodic boundaries",
                    "The current Split-Step Fourier solver cannot enforce zero-value Dirichlet boundaries.\n\n"
                    "Proceeding will change this simulation to Periodic boundaries. A wave leaving one domain edge will re-enter through the other, instead of reflecting from a zero-value boundary.\n\n"
                    "The grid spacing will also change because the periodic grid excludes the right endpoint.\n\n"
                    "Switch to Periodic boundaries and run?", icon = "warning", default = "no", parent = self)

            if not proceed:
                return

            # Update both the actual configuration and the displayed choice.
            config = replace(config, boundary_condition = "Periodic")
            self.simulation_boundary.set("Periodic")


        self.run_button.configure(state="disabled", text="Running...")

        #Run in a thread to not freezing the GUI 
        #And track future as self variable
        """
        worker = ThreadPoolExecutor(max_workers=1)
        future = worker.submit(RunSimulation, config)
        worker.shutdown(wait=False)


        self.after(50, self.FinishSimulation, future)
        """
        worker = None
        self.simulation_stop_event = Event()
        try: 
            worker = ThreadPoolExecutor(max_workers = 1)
            self.simulation_future = worker.submit(RunSimulation, config, self.simulation_stop_event) 
        except Exception as e:
            self.simulation_future = None
            self.simulation_stop_event = None
            self.run_button.configure(state = "normal", text = "Run simulation")
            messagebox.showerror("Cannot start simulation", str(e), parent = self)
            return
        finally:
            if worker is not None: 
                worker.shutdown(wait = False)
        self.after(50, self.FinishSimulation, self.simulation_future)



    def FinishSimulation(self, future):
        if future is not self.simulation_future: #passed wrong parameter
            return
        if self.close_requested:
            return
        #The close dialog DOES NOT pause the calculation, it just prevent the results from being loaded
        if self.quit_prompt_open or not future.done():  
            self.after(50, self.FinishSimulation, future) #50ms
            return

        try:
            (res, x, times, densities, potential_values, 
             momentum_grid, momentum_densities) = future.result()

            self.wave_animation.LoadData(x, times, densities, 
                                         potential_values, momentum_grid, momentum_densities,)
            self.result_table.LoadDataFrame(res)

            self.current_results = res
            self.save_button.configure(state="normal")
        except CancelledError:  #If receiver canceled event, just ignore it here
            pass
        #Catch ValueError from Simulation so it doesn't crash
        except ValueError as error:
            messagebox.showerror("Invalid input", str(error), parent=self)

        except Exception as error:
            messagebox.showerror("Simulation Error", str(error))

        finally:
            self.simulation_future = None
            self.simulation_stop_event = None
            self.run_button.configure(state="normal", text="Run Simulation")

    #The save button ------------------------------------
    def OnSaveResults(self):

        if (self.current_results is None or self.simulation_future is not None or self.simulation_save_future is not None
                or self.close_requested or self.quit_prompt_open):
            return


        path = filedialog.asksaveasfilename(defaultextension = ".csv",filetypes = [("CSV files", "*.csv")], parent = self)

        if not path:
            return

        self.simulation_save_stop_event = Event()
        self.save_button.configure(state = "disabled", text = "Saving...")
        self.run_button.configure(state = "disabled")

        worker = None

        try: #Make saving operation a worker, use the save method in Simulation.py
            worker = ThreadPoolExecutor(max_workers = 1)
            self.simulation_save_future = worker.submit(SaveSimulationResults, self.current_results, path, self.simulation_save_stop_event)
        except Exception as e:
            self.simulation_save_future = None
            self.simulation_save_stop_event = None
            self.save_button.configure(state = "normal", text = "Save Results")
            self.run_button.configure(state = "normal")

            messagebox.showerror("Cannot start saving", str(e),parent = self)
            return
        finally:
            if worker is not None:
                worker.shutdown(wait = False)
        self.after(50, self.PollSimulationSave)

    def PollSimulationSave(self): #And a poll function to handle stopping that saving simulation thread
        if self.close_requested:
            return #don't do anything
        future = self.simulation_save_future
        if future is None:
            return

        if self.quit_prompt_open or not future.done():
            self.after(50, self.PollSimulationSave)
            return

        try:
            future.result()
        except CancelledError:
            pass
        except Exception as e:
            messagebox.showerror("Cannot save simulation results", str(e), parent = self)
        finally:
            self.simulation_save_future = None
            self.simulation_save_stop_event = None
            self.save_button.configure(state = "normal", text = "Save Results")
            self.run_button.configure(state = "normal")

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
                                x_min = x_min,
                                x_max = x_max,
                                N = N,
                                dt = dt,
                                T_final = T_final,
                                solver = self.solver_type.get(),

                                wave_mode = self.wave_input_mode.get(),
                                wave_type = self.wave_type.get(),
                                wave_parameters = wave_parameters,

                                potential_type = self.potential_type.get(),
                                potential_parameters = potential_parameters,

                                wave_expression = (self.wave_expression_entry.get() if self.wave_input_mode.get() == "Expression"
                                               else None),
                                boundary_condition = self.simulation_boundary.get(),
                                )

    #Checkboxes to fill in constants
    def CreateConstantCheckbox(self, parent, entry, name):
        presets = {"mass": ("Electron", m_e),
                   "hbar": ("ħ", hbar)}
        label, preset = presets[name]

        text = tk.StringVar(master = self, value = entry.get())
        selected = tk.BooleanVar(master = self, value = False)
        entry.configure(textvariable = text)

        def SyncCheckbox(*_):
            try:
                matches = float(text.get()) == preset
            except (ValueError, OverflowError):
                matches = False
            selected.set(matches)

        def ApplyPreset():
            if selected.get():
                text.set(repr(preset))
            else:
                text.set("")
        checkbox = ttk.Checkbutton(parent, text = label, variable = selected, command = ApplyPreset)

        text.trace_add("write", SyncCheckbox)
        SyncCheckbox()

        # Retain the Tkinter variables for the widget's lifetime.
        entry.constant_text = text
        checkbox.constant_selected = selected

        AddToolTip(checkbox, CONSTANT_HELP[name])
        return checkbox
    
    
    
    #Custom dialog to ask close confirmation when user click close window during a simulation
    def ConfirmSimulationQuit(self):
        self.quit_prompt_open = True
        confirmed = False

        dialog = tk.Toplevel(self)
        dialog.title("Quit application?")
        dialog.transient(self)
        dialog.resizable(False, False)

        def Finish(answer):
            nonlocal confirmed
            confirmed = answer
            dialog.destroy()
        body = ttk.Frame(dialog, padding=20)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text = ("A simulation is underway, its results are being loaded, or its results are being saved.\n\n"
                "Are you sure you want to quit?\n\nQuitting will stop the operation. Unsaved simulation data "
                "will be lost and cannot be recovered.\n\nFiles whose saves have already completed will remain."),
                wraplength = 460, justify = "left").pack(fill = "x")
        buttons = ttk.Frame(body)
        buttons.pack(anchor = "e", pady = (16, 0))

        ttk.Button(buttons, text = "Yes, quit", command = lambda: Finish(True)).pack(side = "left", padx = (0, 8))

        no_button = ttk.Button(buttons, text = "No", command = lambda: Finish(False))
        no_button.pack(side = "left")

        dialog.protocol("WM_DELETE_WINDOW", lambda: Finish(False))
        dialog.bind("<Escape>", lambda event: Finish(False))

        try:
            dialog.wait_visibility()
            dialog.grab_set()
            no_button.focus_set()
            self.wait_window(dialog)
        finally:
            self.quit_prompt_open = False

        return confirmed


    #Method for handling closing window (mostly for preventing closing)
    def OnClose(self):
        #if simulation is running
        """ Unneeded, ConfirmSimulationQuit handles this case
        if self.simulation_future is not None:
            messagebox.showinfo("Simulation busy", "A simulation is running or its results are being loaded.\n\nPlease wait until it finishes before closing the application.", parent = self)
            return
        """
        if self.close_requested or self.quit_prompt_open:
            return

        if self.recommendation_view.IsLoading():
            messagebox.showinfo("Benchmark analysis running", "Please wait until the benchmark summary has finished loading.", parent = self)
            return

        run_pending = (self.benchmark_future is not None and self.benchmark_manifest is None)
        save_pending = self.benchmark_save_future is not None

        if run_pending or save_pending:
            messagebox.showinfo("Benchmark busy",
            "A benchmark is still running or its results are being saved.\n\n"
            "Please wait until it finishes or stop it before closing the application.", parent = self)
            return

        simulation_pending = self.simulation_future is not None or self.simulation_save_future is not None
        if simulation_pending and not self.ConfirmSimulationQuit(): #turn on the close ask dialog here
            return

        if self.benchmark_temp_directory is not None:
            discard = messagebox.askyesno("Unsaved benchmark results",
                "The completed benchmark has unsaved results.\n\n"
                "Discard these results and close?\n\n"
                "Choose No to return and save them.", parent = self)
            if not discard:
                return

            try:
                self.benchmark_temp_directory.cleanup()
            except OSError as error:
                messagebox.showerror("Cannot remove temporary results",
                    f"{error}\n\nThe application will remain open.", parent = self)
                return

            self.benchmark_temp_directory = None

        self.close_requested = True

        if self.simulation_stop_event is not None:
            self.simulation_stop_event.set()

        if self.simulation_save_stop_event is not None:
            self.simulation_save_stop_event.set()

        self.run_button.configure(state = "disabled", text = "Stopping...")
        self.save_button.configure(state = "disabled")
        self.wave_animation.Pause()
        self.title("Stopping Simulation — closing application…")

        self.WaitForSimulationShutdown()


    def WaitForSimulationShutdown(self):
        futures = (self.simulation_future, self.simulation_save_future)

        if any(future is not None and not future.done() for future in futures):
            self.after(50, self.WaitForSimulationShutdown)
            return

        self.destroy()