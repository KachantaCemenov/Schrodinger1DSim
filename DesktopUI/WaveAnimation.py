import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class WaveAnimation(ttk.Frame):

    def __init__(self, parent, interval_ms=40):
        super().__init__(parent)

        self.interval_ms = interval_ms
        self.after_id = None
        self.playing = False
        self.frame_index = 0

        self.x = None
        self.times = None
        self.densities = None

        controls = ttk.Frame(self)
        controls.pack(fill="x")

        self.play_button = ttk.Button(
            controls,
            text="Play",
            command=self.TogglePlayback,
            state="disabled"
        )
        self.play_button.pack(side="left", padx=5, pady=3)

        self.time_text = tk.StringVar(value="No simulation loaded")
        ttk.Label(controls,textvariable=self.time_text).pack(side="left", padx=10)

        self.figure = Figure(figsize=(8, 2.6), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_xlabel("Position x")
        self.axes.set_ylabel(r"$|\psi(x,t)|^2$")

        self.line, = self.axes.plot([], [], linewidth=2)
        self.figure.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.bind("<Destroy>", self.OnDestroy, add="+")

    def LoadData(self, x, times, densities):
        #Load the array of psi values
        x = np.asarray(x, dtype=float)
        times = np.asarray(times, dtype=float)
        densities = np.asarray(densities, dtype=float)

        if x.ndim != 1 or x.size < 2:
            raise ValueError("x must contain at least two grid points.")

        if times.ndim != 1 or times.size == 0:
            raise ValueError("At least one animation time is required.")

        if densities.shape != (times.size, x.size):
            raise ValueError("Probability density dimensions are invalid.")

        if not (
            np.all(np.isfinite(x))
            and np.all(np.isfinite(times))
            and np.all(np.isfinite(densities))
        ):
            raise ValueError("Animation data must be finite.")

        if np.any(np.diff(x) <= 0):
            raise ValueError("Grid positions must increase.")

        if np.any(np.diff(times) <= 0):
            raise ValueError("Animation times must increase.")

        if np.any(densities < 0):
            raise ValueError("Probability densities cannot be negative.")

        self.Pause()

        self.x = x
        self.times = times
        self.densities = densities

        self.axes.set_xlim(x[0], x[-1])

        # Fixed limits prevent the vertical scale jumping during playback.
        peak = float(densities.max())
        self.axes.set_ylim(0, peak * 1.1 if peak > 0 else 1)

        self.play_button.configure(state="normal")
        self.ShowFrame(0)
        self.Play()

    def ShowFrame(self, index):
        #Display a frame
        if self.densities is None:
            return

        self.frame_index = max(0, min(int(index), len(self.times) - 1))

        self.line.set_data(self.x,self.densities[self.frame_index])

        self.time_text.set(f"t = {self.times[self.frame_index]:.6g}")
        self.canvas.draw_idle()

    def Play(self):
        if self.densities is None or self.playing:
            return

        self.playing = True
        self.play_button.configure(text="Pause")
        self.after_id = self.after(self.interval_ms, self.AdvanceFrame)

    def Pause(self):
        self.playing = False

        if self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None

        self.play_button.configure(text="Play")

    def TogglePlayback(self):
        if self.playing:
            self.Pause()
        else:
            self.Play()

    def AdvanceFrame(self):
        self.after_id = None

        if not self.playing:
            return

        next_index = (self.frame_index + 1) % len(self.times)
        self.ShowFrame(next_index)

        self.after_id = self.after(
            self.interval_ms, self.AdvanceFrame
        )

    def OnDestroy(self, event):
        if event.widget is self and self.after_id is not None:
            self.after_cancel(self.after_id)
            self.after_id = None