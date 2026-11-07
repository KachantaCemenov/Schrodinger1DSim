from functools import partial
import numpy as np
from Simulation import BuildGrid, BuildWaveFunction, BuildPotential
from ComparingMethods.AnalyticalSolutions import FreeGaussianAnalytical,PlaneWaveAnalytical

def BuildBenchmarkProblem(config):
    supported_waves = ("Gaussian Packet", "Plane Wave")
    if config.potential_type != "Free Particle" or config.wave_type not in supported_waves:
        raise ValueError("Currently only supporting Free particle with Gaussian Packet or Plane Wave")

    grid = BuildGrid(config)
    wave = BuildWaveFunction(config, grid)
    potential = BuildPotential(config, grid)

    if not np.all(np.isfinite(wave.psi)):
        raise ValueError("Initial wave contains infinite values.")

    parameters = config.wave_parameters
    
    if config.wave_type == "Plane Wave":
        analytical = partial(  #analytical here is PlaneWaveAnalytical but with frozen parameters
            PlaneWaveAnalytical,
            initial_wave = wave.Copy(),
            grid = grid,
            n = parameters["n"],
            mass = config.mass,
            hbar = config.hbar
            )
    else:
        raw_analytical = partial(  
            FreeGaussianAnalytical,
            grid=grid,
            x0=parameters["x0"],
            sigma=parameters["sigma"],
            k0=parameters["k0"],
            mass=config.mass,
            hbar=config.hbar,
        )

        #Save the norm of the initial analytical for normalization 
        initial = raw_analytical(t = 0)
        initial_norm = np.sqrt(np.sum(np.abs(initial) ** 2) * grid.dx)
        if not np.isfinite(initial_norm) or initial_norm <= 0:
            raise ValueError("Cannot normalize the analytical initial wave.")

        def analytical(t):
            return raw_analytical(t = t) / initial_norm

    return grid, wave, potential, analytical