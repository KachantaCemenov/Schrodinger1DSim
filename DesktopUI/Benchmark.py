from functools import partial
import numpy as np
import json
from dataclasses import replace
from pathlib import Path
import shutil
from datetime import datetime
from tempfile import TemporaryDirectory
from uuid import uuid4


from Simulation import BuildGrid, BuildWaveFunction, BuildPotential
from ComparingMethods.AnalyticalSolutions import FreeGaussianAnalytical,PlaneWaveAnalytical
from Simulation import SimulationConfig
from ComparingMethods.CompareMethods import RunComparison

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

    def reference(t):
        return analytical(t=t) #Because RunComparison call analytical(0) that won't fit the argument list of partial()

    return grid, wave, potential, reference


def RunBenchmarkConfiguration(run, output_folder, progress): #progress is a queue of progress messages
    output_folder = Path(output_folder)
    total = len(run["problems"]) * len(run["N_values"]) * len(run["dt_values"])
    completed = 0
    results = []

    for problem_idx, (name, data) in enumerate(run["problems"].items(), start = 1):
        base_config = SimulationConfig(**data)

        for n_idx, n in enumerate(run["N_values"], start = 1):
            for dt_idx, dt in enumerate(run["dt_values"], start = 1):
                progress.put(f"[{completed + 1} / {total}] Running {name}, N = {n}, dt = {dt:g}")

                config = replace(base_config, N = n, dt = dt)

                grid, wave, potential, analytical = BuildBenchmarkProblem(config)

                relative_folder = Path(f"problem_{problem_idx:03d}") / f"N_{n_idx:03d}_dt_{dt_idx:03d}"
                setting_folder = output_folder / relative_folder
                setting_folder.mkdir(parents = True, exist_ok = False)

                RunComparison(
                    setting_folder = setting_folder,
                    N = n,
                    dt = dt,
                    T_final = config.T_final,
                    grid = grid,
                    wave_func = wave,
                    potential = potential,
                    analytical = analytical,
                    mass = config.mass,
                    hbar = config.hbar,
                    steps = round(config.T_final / dt)
                    )

                results.append({
                    "problem": name,
                    "N": n,
                    "dt": dt,
                    "folder": relative_folder.as_posix()
                    })
                completed += 1
                progress.put(f"[{completed} / {total}] Finished {name}")

    manifest = {"configuration": run, "results": results}
    (output_folder / "run.json").write_text(json.dumps(manifest, indent = 2, allow_nan = False), encoding = "utf-8")
    return manifest


def SaveBenchmarkResults(source_folder, parent_folder):
    parent_folder = Path(parent_folder)
    run_name = f"run_{datetime.now():%Y-%m-%d_%H-%M-%S}_{uuid4().hex[:8]}"
    destination = parent_folder / run_name

    #Keep the folder as temporary until every file is copied
    with TemporaryDirectory(dir = parent_folder, prefix = ".benchmark_saving_") as staging:
        copied_folder = Path(staging) / "results"
        shutil.copytree(source_folder, copied_folder)
        copied_folder.rename(destination)

    return destination
