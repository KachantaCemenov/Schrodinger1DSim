from functools import partial
import numpy as np
import json
from dataclasses import replace
from pathlib import Path
import shutil
from datetime import datetime
from tempfile import TemporaryDirectory
from uuid import uuid4
from time import perf_counter


from Simulation import BuildGrid, BuildWaveFunction, BuildPotential, INFINITE_WELL_SSF_MESSAGE
from ComparingMethods.AnalyticalSolutions import (FreeGaussianAnalytical,   #All functions to calculate numerical waves
                                            PlaneWaveAnalytical,
                                            HarmonicOscillatorEigenstateAnalytical,
                                            GaussianHarmonicAnalytical)
from Simulation import SimulationConfig
from ComparingMethods.CompareMethods import RunComparison

#Check if the problem has an analytical reference
def HasBenchmarkReference(config):
    #These are based on what analytical functions I'm having
    #MANUALLY CHANGE THESE RETURNS when implement more analytical functions
    if config.wave_mode != "Preset":
        return False
    if config.potential_type == "Free Particle":
        return config.wave_type in ("Gaussian Packet", "Plane Wave")
    if config.potential_type != "Harmonic Oscillator":
        return False

    omega = config.potential_parameters["omega"]
    if config.wave_type == "Harmonic Oscillator Eigenstate":
        return bool(np.isclose(config.wave_parameters["omega"], omega, rtol=1e-10, atol=0))

    if config.wave_type == "Gaussian Packet":
        required_sigma = np.sqrt(config.hbar / (2 * config.mass * omega))
        return bool(np.isclose(config.wave_parameters["sigma"], required_sigma, rtol=1e-8, atol=0,))
    return False

def BuildBenchmarkProblem(config):
    """
    problem = (config.wave_type, config.potential_type)

    supported = {("Gaussian Packet", "Free Particle"),
                ("Plane Wave", "Free Particle"),
                ("Gaussian Packet", "Harmonic Oscillator"),
                ("Harmonic Oscillator Eigenstate", "Harmonic Oscillator"),}

    if problem not in supported:
        raise ValueError("This wave/potential combination has no supported benchmark reference yet.")

    #Check same omega in HO eigenstate or correct sigma in Gaussian in HO
    parameters = config.wave_parameters
    potential_parameters = config.potential_parameters

    if config.potential_type == "Harmonic Oscillator":
        omega = potential_parameters["omega"]
        if not np.isfinite(omega) or omega <= 0:
            raise ValueError("Potential omega must be finite and positive.")

        if config.wave_type == "Harmonic Oscillator Eigenstate":
            if not np.isclose(parameters["omega"], omega, rtol=1e-10, atol=0):
                raise ValueError("The eigenstate reference requires matching wave and potential omega values.")
        else:
            required_sigma = np.sqrt(config.hbar / (2 * config.mass * omega))
            if not np.isclose(parameters["sigma"], required_sigma, rtol=1e-8, atol=0):
                raise ValueError(f"The Gaussian harmonic reference requires a coherent state with sigma = {required_sigma:.16g}.")
    """

    if config.potential_type == "Infinite Square Well":
        raise ValueError("A benchmark run compares and calculate both Crank–Nicolson and SSF. "
                    "Infinite Square Well is currently available through Crank–Nicolson in Simulation.\n\n"
                    + INFINITE_WELL_SSF_MESSAGE)

    problem = (config.wave_type, config.potential_type)
    parameters = config.wave_parameters
    potential_parameters = config.potential_parameters

    if config.potential_type == "Harmonic Oscillator":
        omega = potential_parameters["omega"]
        if not np.isfinite(omega) or omega <= 0:
            raise ValueError("Potential omega must be finite and positive.")


    grid = BuildGrid(config)
    wave = BuildWaveFunction(config, grid)
    potential = BuildPotential(config, grid)

    if not np.all(np.isfinite(wave.psi)):
        raise ValueError("Initial wave contains infinite values.")
    if not np.all(np.isfinite(potential.values)):
        raise ValueError("The potential contains invalid values.")

    if not HasBenchmarkReference(config):
        return grid, wave, potential, None #No need to configure the reference return in this case

    #Configure the analytical function (reference) to return
    parameters = config.wave_parameters
    if problem == ("Plane Wave", "Free Particle"):
        raw_reference = partial(
            PlaneWaveAnalytical,
            initial_wave=wave.Copy(),
            grid=grid,
            n=parameters["n"],
            mass=config.mass,
            hbar=config.hbar,
        )

    elif problem == ("Gaussian Packet", "Free Particle"):
        raw_reference = partial(
            FreeGaussianAnalytical,
            grid=grid,
            x0=parameters["x0"],
            sigma=parameters["sigma"],
            k0=parameters["k0"],
            mass=config.mass,
            hbar=config.hbar,
        )

    elif config.wave_type == "Harmonic Oscillator Eigenstate":
        raw_reference = partial(
            HarmonicOscillatorEigenstateAnalytical,
            initial_wave=wave.Copy(),
            n=parameters["n"],
            omega=potential_parameters["omega"],
            hbar=config.hbar,
        )

    else:
        raw_reference = partial(
            GaussianHarmonicAnalytical,
            grid=grid,
            x0=parameters["x0"],
            k0=parameters["k0"],
            mass=config.mass,
            omega=potential_parameters["omega"],
            hbar=config.hbar,
        )

    #Save the norm of the initial analytical for normalization 
    initial = raw_reference(t = 0)
    initial_norm = np.sqrt(np.sum(np.abs(initial) ** 2) * grid.dx)
    if not np.isfinite(initial_norm) or initial_norm <= 0:
        raise ValueError("Cannot normalize the analytical initial wave.")

    def reference(t):
        return raw_reference(t = t) / initial_norm

    return grid, wave, potential, reference

def WriteBenchmarkCheckpoint(output_folder, run, results, status, elapsed_seconds): #Write in manifest at a checkpoint mid-run
    total = (len(run["problems"]) * len(run["N_values"]) * len(run["dt_values"]))
    manifest = {
        "configuration": run,
        "results": list(results),
        "status": status,
        "completed_combinations": len(results),
        "total_combinations": total,
        "elapsed_seconds": elapsed_seconds}
    output_folder = Path(output_folder)
    temporary_path = output_folder / "run.json.tmp"
    manifest_path = output_folder / "run.json"

    #write to different file first before replace in case write fail
    temporary_path.write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8") 
    temporary_path.replace(manifest_path)

    return manifest



def RunBenchmarkConfiguration(run, output_folder, progress, stop_event = None): #progress is a queue of progress messages
    start_time = perf_counter()
    output_folder = Path(output_folder)
    total = len(run["problems"]) * len(run["N_values"]) * len(run["dt_values"])
    completed = 0
    results = []
    WriteBenchmarkCheckpoint(output_folder, run, results, status = "running", elapsed_seconds = 0.0)

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
                    "folder": relative_folder.as_posix(),
                    "analytical_available": analytical is not None
                    })
                completed += 1
                if stop_event is not None and stop_event.is_set(): #Got stopped
                    elapsed = perf_counter() - start_time
                    manifest = WriteBenchmarkCheckpoint(
                        output_folder, run, results,
                        status="stopped",
                        elapsed_seconds=elapsed)
                    progress.put(f"Run stopped: {completed}/{total} combinations completed. Elapsed time: {elapsed:.2f} seconds.")
                    return manifest
                WriteBenchmarkCheckpoint(output_folder, run, results, status = "running", elapsed_seconds = perf_counter() - start_time) #Write mid-way
                progress.put(f"[{completed} / {total}] Finished {name}")
    """
    manifest = {"configuration": run, "results": results}
    (output_folder / "run.json").write_text(json.dumps(manifest, indent = 2, allow_nan = False), encoding = "utf-8")
    """
    #Completed so write
    manifest = WriteBenchmarkCheckpoint(output_folder, run, results, status = "completed", elapsed_seconds = perf_counter() - start_time) 

    #report on the total runtime of this run
    elapsed = perf_counter() - start_time
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    progress.put(f"Total benchmark time: {int(hours)}h {int(minutes)}m {seconds:.2f}s ({elapsed:.2f} seconds).")
    
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
