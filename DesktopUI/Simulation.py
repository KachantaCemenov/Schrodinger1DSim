from dataclasses import dataclass
from grid import Grid1D
import numpy as np
import pandas as pd
from concurrent.futures import CancelledError
from pathlib import Path
from tempfile import NamedTemporaryFile
import os

from potential import Potential
from wavefunction import WaveFunction
from WaveFuncParser import ParseWaveFunction
from Solvers.cranknicolson import CrankNicolsonSolver
from Solvers.SSFSolver import SplitStepFourierSolver
from TimeSteps import CountTimeSteps

BOUNDARY_CONDITIONS = ("Periodic", "Dirichlet")
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

    boundary_condition: str | None = None #New field

    def __post_init__(self):
        # Old configurations don't contain a boundary condition. Preserve the behavior they had before it was added
        if self.boundary_condition is None:
            if self.potential_type == "Infinite Square Well":
                self.boundary_condition = "Dirichlet"
            else:
                self.boundary_condition = "Periodic"

        if self.boundary_condition not in BOUNDARY_CONDITIONS:
            raise ValueError("Boundary condition must be Periodic or Dirichlet.")

        # The current infinite-well implementation uses zero-value walls.
        if self.potential_type == "Infinite Square Well" and self.boundary_condition != "Dirichlet":
            raise ValueError("Infinite Square Well currently requires Dirichlet boundary conditions.")


def BuildGrid(config):
    if config.boundary_condition not in BOUNDARY_CONDITIONS:
        raise ValueError("Boundary condition must be Periodic or Dirichlet.")

    if config.potential_type == "Infinite Square Well" and config.boundary_condition != "Dirichlet":
        raise ValueError("Infinite Square Well currently requires Dirichlet boundary conditions.")

    return Grid1D(config.x_min, config.x_max, config.N, periodic = (config.boundary_condition == "Periodic"))



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
MAX_STEPS = 1_000_000
MAX_GRID_POINTS = 50_000
INFINITE_WELL_SSF_MESSAGE = (
    "The current Split-Step Fourier implementation uses periodic Fourier boundary conditions.\n\n"
    "An Infinite Square Well requires the wave function to remain zero "
    "at its walls. This SSF implementation does not enforce those boundary conditions.\n\n"
    "Use Crank–Nicolson in the Simulation tab for this potential."
    #In future put a new line here pointing to a section in the Help page
)

def CheckSimulationCancelled(stop_event): #Just check if it should be stopped
    if stop_event is not None and stop_event.is_set():
        raise CancelledError("Simulation cancelled.")


#Need a function to calculate observables because cannot use FFT to get momentum in Dirichlet config
def CalculateDirichletObservables(wave, potential, mass, hbar): 
    psi = wave.psi
    dx = wave.grid.dx

    inside = psi[1:-1]
    weights = np.abs(inside) ** 2
    probability = float(dx * np.sum(weights)) #psi^2 * dx

    if not np.isfinite(probability) or probability <= 0:
        raise ValueError("Cannot calculate observables for a zero or nonfinite wave.")

    pot_values = np.asarray(potential.values, dtype = float)

    if pot_values.shape != psi.shape:
        raise ValueError("Potential and wave dimensions do not match.")

    # Infinite-well walls have infinite pot_values, but inside must be finite
    if not np.all(np.isfinite(pot_values[1:-1])):
        raise ValueError("Potential must be finite inside the boundaries.")

    # Central difference for the interior momentum expectation.
    derivative = (psi[2:] - psi[:-2]) / (2 * dx)
    expected_momentum = float((dx * np.vdot(inside, -1j * hbar * derivative)).real / probability) #momentum operator p = -i*hbar*(d/dx)

    # Kinetic energy matching CN's finite-difference Hamiltonian.
    differences = np.diff(psi)
    kinetic = (hbar**2 / (2 * mass * dx) * np.vdot(differences, differences).real) #kinetic part of Hamiltonian

    # Include potential energy for harmonic and barrier problems.
    potential_energy = dx * np.sum(weights * pot_values[1:-1])

    energy = float((kinetic + potential_energy) / probability)

    return expected_momentum, energy


def RunSimulation(config, stop_event = None):
    CheckSimulationCancelled(stop_event) 
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
    if config.x_max <= config.x_min:
        raise ValueError("Use x_max > x_min.")
    if min(config.mass, config.hbar, config.dt, config.T_final) <= 0:
        raise ValueError("Mass, reduced Planck constant, time step, and final time must be positive.")

    num_steps = CountTimeSteps(config.T_final, config.dt, max_steps = MAX_STEPS)
    
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

    if not display_grid.periodic and config.solver == "SSF": #Guard these, SSF never accepts Dirichlet
        if is_well:
            raise ValueError(INFINITE_WELL_SSF_MESSAGE)
        raise ValueError("The current SSF solver requires periodic boundaries. Use Crank-Nicolson for Dirichlet boundaries.")

    if is_well:
        if config.solver != "Crank-Nicolson":
            raise ValueError(INFINITE_WELL_SSF_MESSAGE)

        params = config.potential_parameters
        left = params["x_left"]
        right = params["x_right"]
        
        if not (config.x_min < left < right < config.x_max):
            raise ValueError("Infinite square well potential requires x_min < x_left < x_right < x_max.")

        #Find the grid point the wall positions land on
        wall_indicies = (np.array([left, right]) - config.x_min) / (config.x_max - config.x_min) * (len(display_grid.x) - 1)

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
    if not grid.periodic: #if Dirichlet
        # Enforce zero-value boundaries before starting evolution
        wave.psi[[0, -1]] = 0.0
        norm = wave.Norm()
        if not np.isfinite(norm) or norm <= 0:
            raise ValueError("The initial wave must be finite and nonzero inside Dirichlet boundaries.")
        # Normalize ONCE
        wave.Normalize()

    CheckSimulationCancelled(stop_event)
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
    momentum_densities = []
    phases = []
    rows = []

    #Use the same spatial grid for every frame
    display_count = len(display_grid.x)
    display_dx = display_grid.dx

    #FFT the grid, momentum axis is p = hbar*k, unit kg*m/s
    momentum_grid = (2 * np.pi * config.hbar * np.fft.fftshift(np.fft.fftfreq(display_count, d = display_dx)))

    momentum_spacing = (2 * np.pi * config.hbar / (display_count * display_dx))

    for step in range(num_steps + 1):
        CheckSimulationCancelled(stop_event) 
        time = step * config.dt

        """if is_well:
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
        """

        if not grid.periodic:
            momentum, energy = CalculateDirichletObservables(wave, potential, config.mass, config.hbar)
        else:
            #These expectation values functions in wave_function use FFT
            momentum = wave.Expectation_p(hbar = config.hbar)
            if config.solver == "Crank-Nicolson":
                energy = solver.Expectation_energy(wave)
            else:
                energy = wave.Expectation_energy(potential, mass = config.mass, hbar = config.hbar)
        rows.append((time, wave.Norm(), wave.Expectation_x(), momentum, energy))

        if step in frame_lookup:
            display_psi = np.zeros(display_count, dtype = complex)
            display_psi[active] = wave.psi

            densities.append(np.abs(display_psi) ** 2)
            #Save the phase
            phases.append(np.angle(display_psi).astype(np.float32))
            #Perform FFT in here only for the saved frames
            transformed = np.fft.fftshift(np.fft.fft(display_psi, norm = "ortho"))
            #Probability density per unit momentum.
            #sum(momentum_density) * dp equals sum(position_density) * dx.
            momentum_density = (np.abs(transformed) ** 2 * display_dx / momentum_spacing)

            momentum_densities.append(momentum_density)

        if step < num_steps:
            solver.Step(wave) #propagate the wave function to the next time step

    CheckSimulationCancelled(stop_event) 
    res = pd.DataFrame(rows, columns = ["Time", "Norm", "<x>", "<p>", "<E>"])
    display_potential = full_potential.values if is_well else potential.values

    return (res, display_grid.x, np.array(frame_steps) * config.dt, 
            np.array(densities), display_potential.copy(), 
            momentum_grid, np.array(momentum_densities),
            np.array(phases, dtype = np.float32))



def SaveSimulationResults(dataframe, filename, stop_event): #Have this operation here so it can be stopped
    destination = Path(filename)
    temporary_path = None
    try:
        CheckSimulationCancelled(stop_event)

        with NamedTemporaryFile(mode = "w", encoding = "utf-8", newline = "", dir = destination.parent,
            prefix = ".simulation_", suffix = ".tmp", delete = False) as stream:
            temporary_path = Path(stream.name)
            # write headers 
            dataframe.iloc[:0].to_csv(stream, index=False)
            #then the rows
            for start in range(0, len(dataframe), 5000):
                CheckSimulationCancelled(stop_event)

                dataframe.iloc[start:start + 5000].to_csv(stream,index = False, header = False)

        CheckSimulationCancelled(stop_event)

        # Replace to destination only after the entire CSV is written
        os.replace(temporary_path, destination)
        temporary_path = None

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok = True)