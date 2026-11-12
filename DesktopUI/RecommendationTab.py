import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue, Empty
import os
import pandas as pd
import json
import zipfile
from tempfile import TemporaryDirectory

from Recommendation import BuildRecommendationSummary, FindRecommendation

#Make Recommendation tab here so MainWindow doesn't blow up more than it already is

class RecommendationTab(ttk.Frame):
    def __init__(self, parent, get_loaded_folder):
        super().__init__(parent, padding = 8)

        self.get_loaded_folder = get_loaded_folder
        self.folder = None
        self.manifest = None
        self.summary = None
        self.last_recommendation = None
        self.future = None
        self.progress = Queue()

        # Source controls
        source = ttk.LabelFrame(self, text = "Benchmark source", padding = 8)
        source.pack(fill = "x")

        buttons = ttk.Frame(source)
        buttons.pack(fill = "x")

        self.open_button = ttk.Button(buttons, text = "Open run folder", command = self.OpenRun)
        self.open_button.pack(side="left")

        self.use_loaded_button = ttk.Button(buttons, text = "Use run from Read Benchmark", command = self.UseLoadedRun)
        self.use_loaded_button.pack(side = "left", padx = 8)

        self.folder_button = ttk.Button(buttons, text = "Open results folder", command = self.OpenResultsFolder, state="disabled")
        self.folder_button.pack(side = "left")

        self.path_text = tk.StringVar(value = "No benchmark loaded.")
        ttk.Label(source, textvariable = self.path_text, wraplength = 900).pack(anchor = "w", pady = (8, 0))

        self.status_text = tk.StringVar(value = "Open a saved benchmark run to analyze its results.")
        ttk.Label(source, textvariable = self.status_text, wraplength = 900).pack(anchor = "w", pady = (4, 0))

        self.progress_bar = ttk.Progressbar(source, mode = "indeterminate")
        self.progress_bar.pack(fill = "x", pady = (6, 0))

        # Draggable upper/lower sections
        panes = ttk.Panedwindow(self, orient = "vertical")
        panes.pack(fill = "both", expand = True, pady = (8, 0))

        upper = ttk.Frame(panes)
        upper.columnconfigure(1, weight = 1)

        self.requirements_frame = ttk.LabelFrame(upper, text = "Requirements", padding = 10)
        self.requirements_frame.grid(row = 0, column = 0, sticky = "nsew", padx = (0, 8))

        self.recommendation_frame = ttk.LabelFrame(upper, text = "Recommendation", padding = 10)
        self.recommendation_frame.grid(row = 0, column = 1, sticky = "nsew")

        self.result_text = tk.StringVar(value = "Load a run to inspect the available tested candidates.")
        ttk.Label(self.recommendation_frame, textvariable = self.result_text, wraplength = 600, justify = "left").pack(anchor = "nw")

        panes.add(upper, weight = 1)

        # Summary table with both scrollbars
        table_frame = ttk.LabelFrame(panes, text = "Tested candidates", padding = 6)
        table_frame.rowconfigure(1, weight = 1)
        table_frame.columnconfigure(0, weight = 1)

        #Candidate pass/fail table
        table_controls = ttk.Frame(table_frame)
        table_controls.grid(row = 0, column = 0, columnspan = 2, sticky = "ew", pady = (0, 6))
        ttk.Label(table_controls, text = "Show:").pack(side = "left")

        self.candidate_filter = tk.StringVar(value="All candidates")
        self.candidate_filter_box = ttk.Combobox(table_controls, textvariable=self.candidate_filter,
            values = ("All candidates", "Qualifying only", "Rejected only"), state="disabled", width=20)
        self.candidate_filter_box.pack(side="left", padx=8)
        self.candidate_filter_box.bind("<<ComboboxSelected>>", lambda event: self.ShowSummary())

        self.table_count = tk.StringVar(value="No candidates loaded.")
        ttk.Label(table_controls, textvariable=self.table_count).pack(side="left", padx=8)

        """ Export button?
        self.export_button = ttk.Button(table_controls, text="Export report", command=self.ExportRecommendation, state="disabled")
        self.export_button.pack(side="right")
        """

        #Total candidates table
        self.table = ttk.Treeview(table_frame, show = "headings", selectmode = "browse")
        vertical = ttk.Scrollbar(table_frame, orient = "vertical", command = self.table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient = "horizontal", command = self.table.xview)
        self.table.configure(yscrollcommand = vertical.set, xscrollcommand = horizontal.set)

        self.table.grid(row = 1, column = 0, sticky = "nsew")
        vertical.grid(row = 1, column = 1, sticky = "ns")
        horizontal.grid(row = 2, column = 0, sticky ="ew")

        panes.add(table_frame, weight = 3)

        self.CreateRequirements()

    def IsLoading(self):
        # Includes a finished worker whose result hasn't been processed yet.
        return self.future is not None

    def OpenRun(self):
        if self.IsLoading():
            return

        selected = filedialog.askdirectory(title = "Choose a saved run containing run.json", parent = self, mustexist = True)
        if selected:
            self.StartLoading(selected)

    def UseLoadedRun(self):
        if self.IsLoading():
            return

        folder = self.get_loaded_folder()
        if folder is None:
            messagebox.showinfo("No benchmark loaded", "Open a saved run in Read Benchmark first.", parent = self)
            return

        self.StartLoading(folder)

    def OpenResultsFolder(self):
        if self.folder is None:
            return

        try:
            os.startfile(self.folder)
        except OSError as error:
            messagebox.showerror("Cannot open results folder", str(error), parent = self)

    def StartLoading(self, folder):
        if self.IsLoading():
            return

        self.pending_folder = Path(folder).resolve()
        self.progress = Queue()

        self.open_button.configure(state = "disabled")
        self.use_loaded_button.configure(state = "disabled")
        self.status_text.set(f"Analyzing saved run: {self.pending_folder.name}")
        self.progress_bar.start(15)

        worker = None
        try:
            worker = ThreadPoolExecutor(max_workers = 1)
            self.future = worker.submit(BuildRecommendationSummary, self.pending_folder, self.progress)
            self.RefreshRequirementControls()
        except Exception as error:
            self.future = None
            self.FinishLoadingControls()
            self.status_text.set("Could not start analysis.")
            messagebox.showerror("Cannot analyze benchmark", str(error), parent = self)
            return
        finally:
            if worker is not None:
                worker.shutdown(wait = False)

        self.after(100, self.PollLoading)

    def PollLoading(self):
        # Limit queue processing so UI remains responsive.
        for _ in range(100):
            try:
                message = self.progress.get_nowait()
            except Empty:
                break
            self.status_text.set(message)

        if not self.future.done() or not self.progress.empty():
            self.after(100, self.PollLoading)
            return

        future = self.future
        self.future = None
        self.FinishLoadingControls()

        try:
            manifest, summary = future.result()
        except Exception as error:
            # Keep the previously loaded summary if the new load fails.
            self.status_text.set("Analysis failed. The previously loaded run is unchanged."
                                    if self.summary is not None else "Analysis failed. No run is loaded.")
            messagebox.showerror("Cannot analyze benchmark", str(error), parent = self)
            return

        self.folder = self.pending_folder
        self.manifest = manifest
        self.summary = summary
        self.InitializeRequirements()

        self.path_text.set(str(self.folder))
        self.folder_button.configure(state = "normal")

        completed = manifest["completed_combinations"]
        total = manifest["total_combinations"]
        state = "Complete run" if completed == total else "Partial run"

        self.status_text.set(f"{state}: {completed}/{total} combinations analyzed; {len(summary)} solver candidates.")

        if summary.empty:
            self.result_text.set("This run has no completed combinations to recommend from.")
        else:
            self.result_text.set(f"{len(summary)} tested solver candidates are available.\nOnly completed combinations are included.\n"
                                        "No recommendation has been calculated yet.")

        self.ShowSummary()

    def FinishLoadingControls(self):
        self.progress_bar.stop()
        self.open_button.configure(state = "normal")
        self.use_loaded_button.configure(state = "normal")
        self.RefreshRequirementControls()

    def ShowSummary(self):
        children = self.table.get_children()
        if children:
            self.table.delete(*children)

        evaluated = self.last_recommendation is not None
        if evaluated:   #Showing filtered candidates
            data = self.last_recommendation["candidates"]
            total = len(data)
            selection = self.candidate_filter.get()
            if selection == "Qualifying only":
                data = data.loc[data["passes"]]
            elif selection == "Rejected only":
                data = data.loc[~data["passes"]]
            self.table_count.set(f"Showing {len(data)} / {total} evaluated candidates")
        else:
            data = self.summary
            count = 0 if data is None else len(data)
            self.table_count.set(f"{count} candidates; not evaluated")
            self.candidate_filter.set("All candidates")


        headings = {"problem": "Problem",
                    "method": "Solver",
                    "N": "N",
                    "dt": "dt",
                    "runtime": "Runtime (s)",
                    "max_L2_error": "Maximum L2 error",
                    "max_norm_error": "Maximum norm drift",
                    "max_energy_error": "Maximum energy drift"}
        if evaluated:
            headings.update({"passes": "Meet requirements",
                             "reason": "Rejection reason"})

        self.table.configure(columns = list(headings))

        for column, heading in headings.items(): #Customize the columns width
            self.table.heading(column, text = heading)
            width = 350 if column == "reason" else 150
            if column == "problem":
                width = 180
            self.table.column(column,
                            width = width,
                            minwidth = 80,
                            stretch = False)
        if data is not None:
            for _, row in data.iterrows():
                values = []
                for column in headings:
                    value = row[column]
                    if column == "passes":
                        text = "Yes" if value else "No"
                    elif pd.isna(value):
                        text = "N/A"
                    elif column in ("problem", "method", "reason"):
                        text = str(value)
                    elif column == "N":
                        text = str(int(value))
                    else:
                        text = f"{float(value):.8g}"
                    values.append(text)
                self.table.insert("", "end", values = values)

    def CreateRequirements(self):
        frame = self.requirements_frame
        frame.columnconfigure(1, weight=1)

        self.selection_vars = {}
        self.selection_boxes = {}

        for row, label in enumerate(("Problem", "N", "dt")):
            ttk.Label(frame, text=f"{label}:").grid(row = row, column = 0, sticky = "w", pady = 4)

            variable = tk.StringVar()
            box = ttk.Combobox(frame, textvariable=variable, state="disabled", width = 26)
            box.grid(row = row, column = 1, sticky = "ew", pady = 4)

            self.selection_vars[label] = variable
            self.selection_boxes[label] = box

        self.selection_boxes["Problem"].bind("<<ComboboxSelected>>", lambda event: self.UpdateRequirements(problem_changed = True),)
        self.selection_boxes["N"].bind("<<ComboboxSelected>>", lambda event: self.UpdateRequirements())
        self.selection_boxes["dt"].bind("<<ComboboxSelected>>", lambda event: self.InvalidateRecommendation())

        ttk.Label(frame, text="Maximum allowed:").grid(row = 3, column = 0, columnspan = 2, sticky="w", pady=(10, 4))

        self.tolerance_enabled = {}
        self.tolerance_values = {}
        self.tolerance_checks = {}
        self.tolerance_entries = {}

        for row, (key, label) in enumerate((("l2", "L2 error"), ("norm", "Norm drift"), ("energy", "Energy drift")), start = 4):
            enabled = tk.BooleanVar(value = False)
            value = tk.StringVar()

            check = ttk.Checkbutton(frame, text = label, variable = enabled, command = self.OnToleranceToggle, state="disabled")
            check.grid(row = row, column=0, sticky="w", pady=4)

            entry = ttk.Entry(frame, textvariable = value, state = "disabled", width=18)
            entry.grid(row = row, column=1, sticky="ew", pady=4)
            value.trace_add("write", lambda *_: self.InvalidateRecommendation())

            self.tolerance_enabled[key] = enabled
            self.tolerance_values[key] = value
            self.tolerance_checks[key] = check
            self.tolerance_entries[key] = entry

        self.reference_note = tk.StringVar()
        ttk.Label(frame, textvariable = self.reference_note, wraplength = 300).grid(row=7, column=0, columnspan=2, sticky="w", pady=6)

        self.find_button = ttk.Button(frame, text="Find recommendation", command = self.CalculateRecommendation, state="disabled")
        self.find_button.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        self.reset_button = ttk.Button(frame, text="Reset requirements", command=self.ResetRequirements, state="disabled")
        self.reset_button.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    def RequirementsReady(self):
        return (not self.IsLoading() and self.summary is not None and not self.summary.empty)


    def InvalidateRecommendation(self): 
        self.last_recommendation = None
        if self.summary is not None and not self.summary.empty:
            self.result_text.set("Requirements changed. Click Find recommendation.")
        self.ShowSummary()

    def RefreshReportControls(self): 
        available = self.last_recommendation is not None and not self.IsLoading()
        self.candidate_filter_box.configure(state = "readonly" if available else "disabled")
        #self.export_button.configure(state = "normal" if available else "disabled")

    def RefreshRequirementControls(self): #Refresh boxes and checks
        ready = self.RequirementsReady()

        for box in self.selection_boxes.values():
            box.configure(state="readonly" if ready else "disabled")

        for key, check in self.tolerance_checks.items():
            allowed = ready
            if key == "l2":
                allowed = ready and getattr(self, "l2_available", False)

            check.configure(state="normal" if allowed else "disabled")
            self.tolerance_entries[key].configure(state = "normal" if allowed and self.tolerance_enabled[key].get() else "disabled")

        self.find_button.configure(state =  "normal" if ready else "disabled")
        self.reset_button.configure(state = "normal" if ready else "disabled")
        self.RefreshReportControls()


    def OnToleranceToggle(self):
        self.RefreshRequirementControls()
        self.InvalidateRecommendation()


    def InitializeRequirements(self):
        problems = ([] if self.summary.empty else list(self.summary["problem"].drop_duplicates()))

        self.last_recommendation = None

        self.selection_boxes["Problem"].configure(values=problems)
        self.selection_vars["Problem"].set(problems[0] if problems else "")

        self.ResetRequirements()


    def ResetRequirements(self):
        for key in self.tolerance_enabled:
            self.tolerance_enabled[key].set(False)
            self.tolerance_values[key].set("")

        self.selection_vars["N"].set("Any tested value")
        self.selection_vars["dt"].set("Any tested value")
        self.UpdateRequirements()

    def UpdateRequirements(self, problem_changed=False):
        if self.summary is None or self.summary.empty:
            self.l2_available = False
            self.reference_note.set("No completed candidates are available.")

            for label in ("N", "dt"): #reset boxes cus no problems
                self.selection_boxes[label].configure(values=())
                self.selection_vars[label].set("")

            self.RefreshRequirementControls()
            return

        problem = self.selection_vars["Problem"].get()
        data = self.summary.loc[self.summary["problem"] == problem]

        if problem_changed:
            self.selection_vars["N"].set("Any tested value")
            self.selection_vars["dt"].set("Any tested value")

        n_choices = ["Any tested value"] + [str(int(value)) for value in sorted(data["N"].unique())]
        self.selection_boxes["N"].configure(values = n_choices)

        if self.selection_vars["N"].get() not in n_choices:
            self.selection_vars["N"].set("Any tested value")

        selected_n = self.selection_vars["N"].get()
        dt_data = data if selected_n == "Any tested value" else data.loc[data["N"] == int(selected_n)]

        
        dt_choices = ["Any tested value"] + [str(float(value)) for value in sorted(dt_data["dt"].unique())]
        self.selection_boxes["dt"].configure(values = dt_choices)

        if self.selection_vars["dt"].get() not in dt_choices:
            self.selection_vars["dt"].set("Any tested value")

        self.l2_available = not data.empty and bool(data["analytical_available"].all())

        if not self.l2_available:
            self.tolerance_enabled["l2"].set(False)
            self.reference_note.set("L2 constraint unavailable: analytical-reference data is not available for every candidate of this problem.")
        else:
            self.reference_note.set("Unchecked constraints are ignored. Energy drift uses the benchmark's energy units.")

        self.RefreshRequirementControls()
        self.InvalidateRecommendation()


    def CalculateRecommendation(self): #And write out the recommendation
        if not self.RequirementsReady():
            return

        def Tolerance(key):
            if not self.tolerance_enabled[key].get():
                return None

            text = self.tolerance_values[key].get().strip()
            if not text:
                raise ValueError(f"Enter a value for the enabled {key} constraint.")
            return text

        try:
            n_text = self.selection_vars["N"].get()
            dt_text = self.selection_vars["dt"].get()

            result = FindRecommendation(self.summary,
                                    self.selection_vars["Problem"].get(),
                                    N = None if n_text == "Any tested value" else int(n_text),
                                    dt = None if dt_text == "Any tested value" else float(dt_text),
                                    l2_tolerance = Tolerance("l2"),
                                    norm_tolerance = Tolerance("norm"),
                                    energy_tolerance = Tolerance("energy"))

        except (ValueError, TypeError, OverflowError) as error:
            messagebox.showerror("Invalid requirements", str(error), parent=self)
            return

        def Describe(row):
            return (f"{row['method']}: N={int(row['N'])}, "
                        f"dt={float(row['dt']):.16g}, "
                        f"runtime={float(row['runtime']):.6g} s")

        def Metric(value):
            return "N/A" if pd.isna(value) else f"{float(value):.8g}"

        best = result["best"]
        lines = []

        if result["candidates"].empty:
            lines.append("No completed candidates match the selected N and dt.")
        elif best is None:
            lines.append("No tested candidate meets all requirements.")
        else:
            lines.extend(["Recommended: " + Describe(best),
                        "",
                        f"Maximum L2 error: {Metric(best['max_L2_error'])}",
                        f"Maximum norm drift: {Metric(best['max_norm_error'])}",
                        f"Maximum energy drift: {Metric(best['max_energy_error'])}",
                        "",
                        "Meets all selected requirements."])

        if not any(value.get() for value in self.tolerance_enabled.values()):
            lines.append("\nNo accuracy or conservation constraints were applied.")

        lines.append("\nBest qualifying candidate per solver:")
        for method, row in result["best_by_method"].items():
            lines.append(f"{method}: no qualifying candidate" if row is None else Describe(row))

        lines.append(f"\nQualifying candidates: {len(result['eligible'])} / {len(result['candidates'])}")

        if (self.manifest["completed_combinations"] < self.manifest["total_combinations"]):
            lines.append("Partial run: uncompleted combinations were not evaluated.")

        lines.append("Ranking uses recorded runtimes; results apply to this tested run.")

        result["requirements"] = {"problem": self.selection_vars["Problem"].get(),
            "N": None if n_text == "Any tested value" else int(n_text),
            "dt": None if dt_text == "Any tested value" else float(dt_text),
            "l2_tolerance": float(self.tolerance_values["l2"].get()) if self.tolerance_enabled["l2"].get() else None,
            "norm_tolerance": float(self.tolerance_values["norm"].get()) if self.tolerance_enabled["norm"].get() else None,
            "energy_tolerance": float(self.tolerance_values["energy"].get()) if self.tolerance_enabled["energy"].get() else None}

        self.result_text.set("\n".join(lines))
        self.last_recommendation = result
        self.candidate_filter.set("All candidates")
        self.ShowSummary()
        self.RefreshReportControls()