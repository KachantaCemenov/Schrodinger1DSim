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
        self.background = None

        self.x = None
        self.times = None
        self.densities = None
        self.momentum_grid = None
        self.momentum_densities = None  

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

        #Two subplots for position and momentum
        self.figure = Figure(figsize=(8, 5.5), dpi=100)
        self.axes = self.figure.add_subplot(211)
        self.momentum_axes = self.figure.add_subplot(212)
        #self.axes = self.figure.add_subplot(111)
        self.axes.set_xlabel("Position x")
        self.axes.set_ylabel(r"$|\psi(x,t)|^2$")

        self.line, = self.axes.plot([], [], color="tab:blue", linewidth = 2, animated = True)

        self.axes.set_ylabel(r"$|\psi(x,t)|^2$", color = "tab:blue")
        self.axes.tick_params(axis = "y", labelcolor = "tab:blue")
        #Potential
        self.potential_axes = self.axes.twinx()
        self.potential_axes.set_ylabel("Potential energy V(x)", color = "tab:orange")
        self.potential_axes.tick_params(axis = "y", labelcolor = "tab:orange")
        self.potential_axes.patch.set_visible(False)
        self.potential_axes.grid(False)

        self.potential_line, = self.potential_axes.plot([], [], color = "tab:orange", linestyle = "--", linewidth = 1.5)

        self.axes.set_title("Position distribution")
        #Momentum
        self.momentum_axes.set_title("Momentum distribution")
        self.momentum_axes.set_xlabel("Momentum p")
        self.momentum_axes.set_ylabel(r"$|\phi(p,t)|^2$")
        self.momentum_axes.ticklabel_format(axis = "both", style = "sci", scilimits = (-3, 3),
            useOffset = False)
        self.momentum_line, = self.momentum_axes.plot([], [], color = "tab:green", linewidth = 2,
            animated = True)

        self.wall_artists = []

        self.figure.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("draw_event", self.OnCanvasDraw)
        self.canvas.mpl_connect("resize_event", self.OnCanvasResize)

        self.canvas.get_tk_widget().bind("<Map>", self.OnCanvasMapped, add = "+")

        self.bind("<Destroy>", self.OnDestroy, add="+")

    def LoadData(self, x, times, densities, potential_values, momentum_grid, momentum_densities):
        #Load the array of psi values
        x = np.asarray(x, dtype=float)
        times = np.asarray(times, dtype=float)
        densities = np.asarray(densities, dtype=float)
        potential_values = np.asarray(potential_values, dtype=float)
        momentum_grid = np.asarray(momentum_grid, dtype=float)
        momentum_densities = np.asarray(momentum_densities, dtype=float)

        if x.ndim != 1 or x.size < 2:
            raise ValueError("x must contain at least two grid points.")

        if times.ndim != 1 or times.size == 0:
            raise ValueError("At least one animation time is required.")

        if densities.shape != (times.size, x.size):
            raise ValueError("Probability density dimensions are invalid.")

        if not (np.all(np.isfinite(x)) and np.all(np.isfinite(times)) and np.all(np.isfinite(densities))):
            raise ValueError("Animation data must be finite.")

        if np.any(np.diff(x) <= 0):
            raise ValueError("Grid positions must increase.")

        if np.any(np.diff(times) <= 0):
            raise ValueError("Animation times must increase.")

        if np.any(densities < 0):
            raise ValueError("Probability densities cannot be negative.")
        #Check the potential
        if potential_values.shape != x.shape:
            raise ValueError("Potential must have one value per spatial grid point.")

        if np.any(np.isnan(potential_values)) or np.any(np.isneginf(potential_values)): #posinf is allowed
            raise ValueError("Potential contains invalid values.")

        if not np.any(np.isfinite(potential_values)):
            raise ValueError("Potential must contain a finite region.")
        #Check the momentum
        if momentum_grid.ndim != 1 or momentum_grid.size < 2:
            raise ValueError("Momentum grid must contain at least two points.")

        if momentum_densities.shape != (times.size, momentum_grid.size):
            raise ValueError("Momentum density dimensions are invalid.")

        if not (np.all(np.isfinite(momentum_grid)) and np.all(np.isfinite(momentum_densities))):
            raise ValueError("Momentum animation data must be finite.")

        if np.any(np.diff(momentum_grid) <= 0):
            raise ValueError("Momentum grid must be strictly increasing.")

        if np.any(momentum_densities < 0):
            raise ValueError("Momentum densities cannot be negative.")

        self.Pause()

        self.x = x
        self.times = times
        self.densities = densities
        self.momentum_grid = momentum_grid
        self.momentum_densities = momentum_densities
        self.line.set_data(self.x, self.densities[0])
        self.momentum_line.set_data(self.momentum_grid, self.momentum_densities[0])
        self.background = None

        self.axes.set_xlim(x[0], x[-1])

        # Fixed limits prevent the vertical scale jumping during playback.
        peak = float(densities.max())
        self.axes.set_ylim(0, peak * 1.1 if peak > 0 else 1)
        self.momentum_axes.set_xlim(self.momentum_grid[0], self.momentum_grid[-1])
        momentum_peak = float(self.momentum_densities.max())
        self.momentum_axes.set_ylim(0, momentum_peak * 1.1 if momentum_peak > 0 else 1)
        self.UpdatePotential(x, potential_values)
        self.figure.tight_layout()
        self.background = None

        self.play_button.configure(state="normal")
        self.ShowFrame(0)
        self.Play()

    def ShowFrame(self, index):
        #Display a frame
        if self.densities is None:
            return

        self.frame_index = max(0, min(int(index), len(self.times) - 1))

        #Only vertical values change
        self.line.set_ydata(self.densities[self.frame_index])
        self.momentum_line.set_ydata(self.momentum_densities[self.frame_index])

        self.time_text.set(f"t = {self.times[self.frame_index]:.6g}")
        self.DrawCurrentFrame()

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

    def OnCanvasDraw(self, event):
        self.background = self.canvas.copy_from_bbox(self.figure.bbox)

        if self.densities is not None:
            self.axes.draw_artist(self.line)
            self.momentum_axes.draw_artist(self.momentum_line)
            self.canvas.blit(self.figure.bbox)


    def OnCanvasResize(self, event):
        self.background = None


    def OnCanvasMapped(self, event):
        # Refresh after returning to the Simulation tab.
        self.background = None
        self.canvas.draw_idle()


    def DrawCurrentFrame(self):
        # Avoid rendering while the Simulation plot is hidden.
        if not self.canvas.get_tk_widget().winfo_viewable():
            self.background = None
            return

        if self.background is None:
            self.canvas.draw_idle()
            return

        self.canvas.restore_region(self.background)
        self.axes.draw_artist(self.line)
        self.momentum_axes.draw_artist(self.momentum_line)
        self.canvas.blit(self.figure.bbox)

    def UpdatePotential(self, x, values):
        # Remove wall from a previously loaded simulation.
        for artist in self.wall_artists:
            artist.remove()
        self.wall_artists.clear()

        finite = np.isfinite(values)

        # Infinity is represented by wall decorations, not a finite height.
        plotted_values = np.where(finite, values, np.nan)
        self.potential_line.set_data(x, plotted_values)

        finite_values = values[finite]
        low = min(0.0, float(finite_values.min()))
        high = max(0.0, float(finite_values.max()))

        if low == high:
            # Free particle and the interior of an infinite well have V = 0.
            self.potential_axes.set_ylim(-1.0, 1.0)
            self.potential_axes.set_yticks([0.0])
        else:
            # Restore automatic ticks after previously displaying V = 0.
            from matplotlib.ticker import AutoLocator
            self.potential_axes.yaxis.set_major_locator(AutoLocator())

            padding = 0.08 * (high - low)
            self.potential_axes.set_ylim(low - padding, high + padding)

        if np.any(np.isposinf(values)):
            # The current infinite-well potential has one finite interior.
            finite_indices = np.flatnonzero(finite)
            left_wall = x[finite_indices[0]]
            right_wall = x[finite_indices[-1]]

            for start, end in ((x[0], left_wall),(right_wall, x[-1])):
                shading = self.potential_axes.axvspan(start, end, color = "tab:orange", alpha = 0.15)
                self.wall_artists.append(shading)

            for position in (left_wall, right_wall):
                wall = self.potential_axes.axvline(position, color = "tab:orange", linestyle = ":", linewidth = 1.5)
                self.wall_artists.append(wall)

            note = self.potential_axes.text(0.02, 0.95, "Shaded regions: V = ∞", transform = self.potential_axes.transAxes, va = "top", color = "tab:orange")
            self.wall_artists.append(note)