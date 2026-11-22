import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib import colormaps


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

        self.phases = None
        self.phase_segments = None

        controls = ttk.Frame(self)
        controls.pack(fill="x")

        self.play_button = ttk.Button(controls, text = "Play", command = self.TogglePlayback,state = "disabled")
        self.play_button.pack(side = "left", padx = 5, pady = 3)

        #Buttons for momentum graphs
        self.momentum_full_button = ttk.Button(controls, text = "Full momentum range", command = lambda: self.SetMomentumView(False),
            state = "disabled")
        self.momentum_full_button.pack(side = "right", padx = 5, pady = 3)

        self.momentum_fit_button = ttk.Button(controls, text = "Fit momentum distribution", command = lambda: self.SetMomentumView(True),
            state = "disabled")
        self.momentum_fit_button.pack(side = "right", padx = 5, pady = 3)

        self.time_text = tk.StringVar(value="No simulation loaded")
        ttk.Label(controls,textvariable=self.time_text).pack(side="left", padx=10)

        #Two subplots for position and momentum
        self.figure = Figure(figsize = (8, 6.5), dpi = 100)
        layout = self.figure.add_gridspec(3, 1, height_ratios = (1, 0.06, 1))
        self.axes = self.figure.add_subplot(layout[0])
        self.phase_colorbar_axes = self.figure.add_subplot(layout[1])
        self.momentum_axes = self.figure.add_subplot(layout[2])
        #self.axes = self.figure.add_subplot(111)
        self.axes.set_xlabel("Position x")
        self.axes.set_ylabel(r"$|\psi(x,t)|^2$")

        #self.line, = self.axes.plot([], [], color="tab:blue", linewidth = 2, animated = True)
        #Coloring the phases, gray means negligible densities so hidden phase
        phase_colormap = colormaps["twilight"].copy()
        phase_colormap.set_bad((0.55, 0.55, 0.55, 0.5))

        self.phase_line = LineCollection([], cmap = phase_colormap,
                                        norm = Normalize(vmin = -np.pi, vmax = np.pi), linewidths = 2, animated = True)
        self.axes.add_collection(self.phase_line)

        self.phase_colorbar = self.figure.colorbar(self.phase_line, cax = self.phase_colorbar_axes, orientation = "horizontal")
        self.phase_colorbar.set_label("Phase (rad)")
        self.phase_colorbar.set_ticks([-np.pi, 0, np.pi])
        self.phase_colorbar.set_ticklabels(["−π", "0", "π"])



        """self.axes.set_ylabel(r"$|\psi(x,t)|^2$", color = "tab:blue")
        self.axes.tick_params(axis = "y", labelcolor = "tab:blue")"""
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

        self.figure.tight_layout(pad = 1.2, h_pad = 1.8)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("draw_event", self.OnCanvasDraw)
        self.canvas.mpl_connect("resize_event", self.OnCanvasResize)

        self.canvas.get_tk_widget().bind("<Map>", self.OnCanvasMapped, add = "+")

        self.bind("<Destroy>", self.OnDestroy, add="+")

    def LoadData(self, x, times, densities, potential_values, momentum_grid, momentum_densities, phases):
        #Load the array of psi values
        x = np.asarray(x, dtype=float)
        times = np.asarray(times, dtype=float)
        densities = np.asarray(densities, dtype=float)
        potential_values = np.asarray(potential_values, dtype=float)
        momentum_grid = np.asarray(momentum_grid, dtype=float)
        momentum_densities = np.asarray(momentum_densities, dtype=float)
        phases = np.asarray(phases, dtype = np.float32)

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
        #Check phase
        if phases.shape != densities.shape:
            raise ValueError("Phase and probability density dimensions do not match.")
        if not np.all(np.isfinite(phases)):
            raise ValueError("Animation phases must be finite.")

        self.Pause()

        self.x = x
        self.times = times
        self.densities = densities
        self.phases = phases
        self.momentum_grid = momentum_grid
        self.momentum_densities = momentum_densities
        #Cloring
        midpoint_x = 0.5 * (x[:-1] + x[1:])
        self.phase_segments = np.empty((len(x), 3, 2), dtype = float)
        self.phase_segments[:, 0, 0] = np.r_[x[0], midpoint_x]
        self.phase_segments[:, 1, 0] = x
        self.phase_segments[:, 2, 0] = np.r_[midpoint_x, x[-1]]
        self.UpdatePhaseLine(0)

        self.momentum_line.set_data(self.momentum_grid, self.momentum_densities[0])
        self.background = None

        self.axes.set_xlim(x[0], x[-1])

        # Fixed limits prevent the vertical scale jumping during playback.
        peak = float(densities.max())
        self.axes.set_ylim(0, peak * 1.1 if peak > 0 else 1)
        self.momentum_fit_limits = self.CalculateMomentumLimits() 
        self.momentum_axes.set_xlim(*self.momentum_fit_limits)
        momentum_peak = float(self.momentum_densities.max())
        self.momentum_axes.set_ylim(0, momentum_peak * 1.1 if momentum_peak > 0 else 1)
        self.UpdatePotential(x, potential_values)
        self.figure.tight_layout(pad = 1.2, h_pad = 1.8)
        self.background = None

        self.momentum_fit_button.configure(state="normal")
        self.momentum_full_button.configure(state="normal")
        self.play_button.configure(state="normal")
        self.ShowFrame(0)
        self.Play()

    def ShowFrame(self, index):
        #Display a frame
        if self.densities is None:
            return

        self.frame_index = max(0, min(int(index), len(self.times) - 1))

        #Only vertical values change
        self.UpdatePhaseLine(self.frame_index)
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
            self.axes.draw_artist(self.phase_line)
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
        self.axes.draw_artist(self.phase_line)
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

    def CalculateMomentumLimits(self): #Exclude spaces with too small momentum probability densities
        p = self.momentum_grid
        first = len(p) - 1
        last = 0
        found = False

        # Exclude at most 0.05% from each tail of each frame.
        tail = 0.0005

        for density in self.momentum_densities:
            peak = float(density.max())
            if peak <= 0:
                continue

            # Scaling avoids unnecessarily large cumulative sums.
            # The FFT grid is uniformly spaced, so dp cancels when calculating probability fractions.
            cumulative = np.cumsum(density / peak)
            total = cumulative[-1]

            low = int(np.searchsorted(cumulative, tail * total))
            high = int(np.searchsorted(cumulative, (1 - tail) * total))

            first = min(first, low)
            last = max(last, min(high, len(p) - 1))
            found = True

        if not found:
            return float(p[0]), float(p[-1])

        # Add padding, including when all probability occupies one bin.
        spacing = float(p[1] - p[0])
        padding = max(0.1 * float(p[last] - p[first]), 3 * spacing)

        return (max(float(p[0]), float(p[first]) - padding), min(float(p[-1]), float(p[last]) + padding))


    def SetMomentumView(self, fit):
        if self.momentum_grid is None:
            return

        if fit:
            limits = self.momentum_fit_limits
        else:
            limits = (float(self.momentum_grid[0]), float(self.momentum_grid[-1]))

        self.momentum_axes.set_xlim(*limits)

        # Changing axes invalidates the saved blitting background.
        self.background = None
        self.canvas.draw_idle()


    def UpdatePhaseLine(self, index):
        density = self.densities[index]
        midpoint_y = 0.5 * (density[:-1] + density[1:])

        self.phase_segments[:, 0, 1] = np.r_[density[0], midpoint_y]
        self.phase_segments[:, 1, 1] = density
        self.phase_segments[:, 2, 1] = np.r_[midpoint_y, density[-1]]

        self.phase_line.set_segments(self.phase_segments)

        #Relative threshold also works when density has physical units
        peak = float(density.max())
        hidden = density <= 1e-8 * peak #No need to color the points with too small prob density

        displayed_phase = np.ma.masked_where(hidden, self.phases[index])

        self.phase_line.set_array(displayed_phase)