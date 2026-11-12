import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue, Empty
import os

import pandas as pd

from Recommendation import BuildRecommendationSummary

#Make Recommendation tab here so MainWindow doesn't blow up more than it already is

class RecommendationTab(ttk.Frame):
    def __init__(self, parent, get_loaded_folder):
        super().__init__(parent, padding = 8)

        self.get_loaded_folder = get_loaded_folder
        self.folder = None
        self.manifest = None
        self.summary = None
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
        table_frame.rowconfigure(0, weight = 1)
        table_frame.columnconfigure(0, weight = 1)

        self.table = ttk.Treeview(table_frame, show = "headings", selectmode = "browse")
        vertical = ttk.Scrollbar(table_frame, orient = "vertical", command = self.table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient = "horizontal", command = self.table.xview)
        self.table.configure(yscrollcommand = vertical.set, xscrollcommand = horizontal.set)

        self.table.grid(row = 0, column = 0, sticky = "nsew")
        vertical.grid(row = 0, column = 1, sticky = "ns")
        horizontal.grid(row = 1, column = 0, sticky ="ew")

        panes.add(table_frame, weight = 3)

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

    def ShowSummary(self):
        children = self.table.get_children()
        if children:
            self.table.delete(*children)

        headings = {"problem": "Problem",
                    "method": "Solver",
                    "N": "N",
                    "dt": "dt",
                    "runtime": "Runtime (s)",
                    "max_L2_error": "Maximum L2 error",
                    "max_norm_error": "Maximum norm drift",
                    "max_energy_error": "Maximum energy drift"}

        self.table.configure(columns = list(headings))

        for column, heading in headings.items():
            self.table.heading(column, text = heading)
            self.table.column(column,
                            width=180 if column == "problem" else 150,
                            minwidth=80,
                            stretch=False)

        for _, row in self.summary.iterrows():
            values = []
            for column in headings:
                value = row[column]
                if pd.isna(value):
                    text = "N/A"
                elif column in ("problem", "method"):
                    text = str(value)
                elif column == "N":
                    text = str(int(value))
                else:
                    text = f"{float(value):.8g}"
                values.append(text)
            self.table.insert("", "end", values = values)