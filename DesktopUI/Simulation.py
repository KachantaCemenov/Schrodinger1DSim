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
    """
    if config.potential_type = "Infinite Square Well":
        x_left = config.potential_parameters["x_left"]
        x_right = config.potential_parameters["x_right"]
        if x_left >= x_right:
            raise ValueError("Infinite square well potential requires x_left < x_right.")
        if config.solver != "Crank-Nicolson":
            raise ValueError("Only Crank-Nicolson is currently supported for Infinite Square Well potential.")

        return Grid1D(x_left, x_right, config.N, periodic = False)
    return Grid1D(config.x_min, config.x_max, config.N, periodic = True)
    """
    return Grid1D(config.x_min, config.x_max, config.N, 
            periodic = (config.potential_type != "Infinite Square Well"))



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

    if config.potential_type == "Infinite Square Well":
        return Potential.InfiniteSquareWell(grid, **params)

    raise ValueError(f"Unknown potential type: {config.potential_type}")


#Getting error when N or T_final / dt is too large, linspace failed.
#These constraints are arbitrary for now
MAX_STEPS = 100_000
MAX_GRID_POINTS = 20_000


def RunSimulation(config):
    #Displayed values
    values = [
            config.x_min, config.x_max, config.mass, config.hbar, 
            config.dt, config.T_final,
            *config.wave_parameters.values(), *config.potential_parameters.values()
        ]
    if not 3 <= config.N <= MAX_GRID_POINTS:
        raise ValueError(f"Number of grid points N must be between 3 and {MAX_GRID_POINTS}.")
    if not np.all(np.isfinite(values)):
        raise ValueError("All input values must be finite.")
    if config.potential_type != "Infinite Square Well" and config.x_max <= config.x_min:
        raise ValueError("Use x_max > x_min.")
    if min(config.mass, config.hbar, config.dt, config.T_final) <= 0:
        raise ValueError("Mass, reduced Planck constant, time step, and final time must be positive.")

    ratio = config.T_final / config.dt

    if not np.isfinite(ratio) or ratio > MAX_STEPS:
        raise ValueError(f"This run exceed the limit of {MAX_STEPS} time steps.\nPlease reduce T_final or increase dt.")

    num_steps = round(ratio)
    if num_steps <= 0 or abs(ratio - num_steps) > 1e-10:
        raise ValueError("Final time must be an integer multiple of the time step.")
    
    """
    grid = BuildGrid(config)
    wave = BuildWaveFunction(config, grid)
    potential = BuildPotential(config, grid)

    #Initialize the selected solver
    solver_classes = {
        "Crank-Nicolson": CrankNicolsonSolver,
        "SSF": SplitStepFourierSolver}
    solver = solver_classes[config.solver](grid, potential, dt = config.dt, 
                                           hbar = config.hbar, mass = config.mass)
    """

    display_grid = BuildGrid(config)
    is_well = config.potential_type == "Infinite Square Well"
    active = slice(None)

    if is_well:
        if config.solver != "Crank-Nicolson":
            raise ValueError("Only Crank-Nicolson is currently supported for Infinite Square Well potential.")

        params = config.potential_parameters
        left = params["x_left"]
        right = params["x_right"]
        
        if not (config.x_min < left < right < config.x_max):
            raise ValueError("Infinite square well potential requires x_min < x_left < x_right < x_max.")

        #Find the grid point the wall positions land on
        wall_indicies = (np.array([left, right]) - config.x_min) / display_grid.dx 
        nearest = np.round(wall_indicies).astype(int)

        if not np.allclose(wall_indicies, nearest, rtol = 0, atol = 1e-10):
            raise ValueError(f"Wall must fall on grid points. Grid spacing is {display_grid.dx:.6g}. Adjust N or wall positions.")
        w_left, w_right = nearest
        if w_right - w_left < 2:
            raise ValueError("Infinite square well potential requires at least one grid point between the walls.")
        
        active = slice(w_left, w_right + 1) #Only the interior points are active for the solver
        grid = Grid1D(left, right, w_right - w_left + 1, periodic = False) #Only need the interior for the grid
        
        full_potential = Potential.InfiniteSquareWell(display_grid, grid.x[0], grid.x[-1])
        potential = Potential(grid, full_potential.values[active]) #Only the interior points are active for the solver
    else:
        grid = display_grid
        potential = BuildPotential(config, grid)

    wave = BuildWaveFunction(config, grid)
    if is_well:
        wave.psi[[0,-1]] = 0.0 #Enforce the boundary conditions for the infinite square well
        norm = wave.Norm()
        if not np.isfinite(norm) or norm <= 0:
            raise ValueError("Wave function must be nonzero inside well")
        wave.Normalize() #Normalize ONCE

    solver_args = dict(dt = config.dt, hbar = config.hbar, mass = config.mass)

    if config.solver == "Crank-Nicolson":
        solver = CrankNicolsonSolver(grid, potential, periodic = grid.periodic, **solver_args)
    elif config.solver == "SSF":
        solver = SplitStepFourierSolver(grid, potential, **solver_args)
    else:
        raise ValueError(f"Unknown solver: {config.solver}")

    # Keep every table rows but only 400 frames for the animation
    frame_steps = np.linspace(0, num_steps, min(num_steps + 1, 400), dtype=int)
    frame_lookup = set(frame_steps)
    densities = []
    rows = []

    for step in range(num_steps + 1):
        time = step * config.dt

        """rows.append((
            time, 
            wave.Norm(),
            wave.Expectation_x(),
            wave.Expectation_p(hbar = config.hbar),
            wave.Expectation_energy(potential, mass = config.mass, hbar = config.hbar)
        ))"""

        if is_well:
            #Calculate the metrics here without assuming periodicity
            psi = wave.psi.copy()
            dx = grid.dx

            derivative = (psi[2:]-psi[:-2])/(2*dx)
            momentum = (dx * np.vdot(psi[1:-1], -1j * config.hbar * derivative)).real
            differences = np.diff(psi)
            energy = (config.hbar**2 / (2 * config.mass * dx) 
                     * np.vdot(differences, differences).real )
        else:
            momentum = wave.Expectation_p(hbar = config.hbar)
            energy = wave.Expectation_energy(potential, mass = config.mass, hbar = config.hbar)
        rows.append((time, wave.Norm(), wave.Expectation_x(), momentum, energy))

        if step in frame_lookup:
            density = np.zeros_like(display_grid.x, dtype=float)
            density[active] = wave.ProbabilityDensity()
            densities.append(density) #Only update the active part
        if step < num_steps:
            solver.Step(wave) #propagate the wave function to the next time step

    res = pd.DataFrame(rows, columns = ["Time", "Norm", "<x>", "<p>", "<E>"])
    return res, display_grid.x, np.array(frame_steps) * config.dt, np.array(densities)