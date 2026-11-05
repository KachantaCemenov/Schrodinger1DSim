from dataclasses import dataclass
from grid import Grid1D
import numpy as np
import pandas as pd

from potential import Potential
from wavefunction import WaveFunction
from WaveFuncParser import ParseWaveFunction
from Solvers.cranknicolson import CrankNicolsonSolver
from Solvers.SSFSolver import SplitStepFourierSolver

@dataclass
class SimulationConfig:

    mass: float
    hbar: float

    x_min: float
    x_max: float

    N: int

    dt: float
    T_final: float

    solver: str

    wave_mode: str
    wave_type: str
    wave_parameters: dict

    potential_type: str
    potential_parameters: dict

    wave_expression: str | None = None


def BuildGrid(config):
    return Grid1D(
    x_min = config.x_min,
    x_max = config.x_max,
    num_points = config.N
    )


def BuildWaveFunction(config, grid):

    if config.wave_mode == "Expression":
        return ParseWaveFunction(config.wave_expression.strip(), grid)
    params = config.wave_parameters

    if config.wave_type == "Gaussian Packet":
        if params["sigma"] <= 0:
            raise ValueError("This wave function requires sigma > 0.")
        return WaveFunction.GaussianPacket(grid, **params)

    if config.wave_type == "Plane Wave":
        return WaveFunction.PlaneWave(grid, **params)

    if config.wave_type == "Harmonic Oscillator Eigenstate":
        if params["n"] < 0 or params["omega"] <= 0:
            raise ValueError("This wave function requires n >= 0 and omega > 0.")
        return WaveFunction.HarmonicOscillatorEigenstate(grid, mass = config.mass, hbar = config.hbar, **params)

    raise ValueError(f"Unknown wave function type: {config.wave_type}")


def BuildPotential(config, grid):
    params = config.potential_parameters

    if config.potential_type == "Harmonic Oscillator":
        return Potential.HarmonicOscillator(grid, mass = config.mass, **params)

    if config.potential_type == "Free Particle":
        return Potential.FreeParticle(grid)

    if config.potential_type == "Barrier":
        if params["x_left"] >= params["x_right"]:
            raise ValueError("Barrier potential requires x_left < x_right.")
        return Potential.Barrier(grid, **params)

    raise ValueError(f"Unknown potential type: {config.potential_type}")


def RunSimulation(config):
    #Displayed values
    values = [
            config.x_min, config.x_max, config.mass, config.hbar, 
            config.dt, config.T_final,
            *config.wave_parameters.values(), *config.potential_parameters.values()
        ]

    if not np.all(np.isfinite(values)):
        raise ValueError("All input values must be finite.")
    if config.N < 3 or config.x_max <= config.x_min:
        raise ValueError("Use N >= 3 and x_max > x_min.")
    if min(config.mass, config.hbar, config.dt, config.T_final) <= 0:
        raise ValueError("Mass, reduced Planck constant, time step, and final time must be positive.")

    ratio = config.T_final / config.dt
    num_steps = round(ratio)
    if num_steps <= 0 or abs(ratio - num_steps) > 1e-10:
        raise ValueError("Final time must be an integer multiple of the time step.")

    grid = BuildGrid(config)
    wave = BuildWaveFunction(config, grid)
    potential = BuildPotential(config, grid)

    #Initialize the selected solver
    solver_classes = {
        "Crank-Nicolson": CrankNicolsonSolver,
        "SSF": SplitStepFourierSolver}
    solver = solver_classes[config.solver](grid, potential, dt = config.dt, 
                                           hbar = config.hbar, mass = config.mass)

    # Keep every table rows but only 400 frames for the animation
    frame_steps = np.linspace(0, num_steps, min(num_steps + 1, 400), dtype=int)
    frame_lookup = set(frame_steps)
    densities = []
    rows = []

    for step in range(num_steps + 1):
        time = step * config.dt

        rows.append((
            time, 
            wave.Norm(),
            wave.Expectation_x(),
            wave.Expectation_p(hbar = config.hbar),
            wave.Expectation_energy(potential, mass = config.mass, hbar = config.hbar)
        ))

        if step in frame_lookup:
            densities.append(wave.ProbabilityDensity())
        if step < num_steps:
            solver.Step(wave) #propagate the wave function to the next time step

    res = pd.DataFrame(rows, columns = ["Time", "Norm", "<x>", "<p>", "<E>"])
    return res, grid.x, np.array(frame_steps) * config.dt, np.array(densities)