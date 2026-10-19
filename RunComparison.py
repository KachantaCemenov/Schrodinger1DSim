from pathlib import Path
from datetime import datetime

from Compare import RunComparison
from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential


N_values = [256, 512, 1024, 2048]
dt_values = [0.01, 0.005, 0.0025, 0.001]

timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

run_folder = (
    Path("Results")/"Comparisons"/f"run_{timestamp}"
)

run_folder.mkdir(parents=True,exist_ok=True)


#Each of these is a benchmark problem
def GaussianFree(grid): #grid differs on each N

    wave = WaveFunction.GaussianPacket(
        grid=grid,
        x0=-15,
        sigma=5,
        k0=3
    )

    potential = Potential.FreeParticle(grid)

    return wave, potential

def HarmonicOscillatorGroundState(grid):

    mass = 1.0
    omega = 1.0
    hbar = 1.0

    wave = WaveFunction.HarmonicOscillatorEigenstate(
        grid=grid,
        n=0,
        mass=mass,
        omega=omega,
        hbar=hbar
    )

    potential = Potential.HarmonicOscillator(
        grid,
        mass=mass,
        omega=omega
    )

    return wave, potential

benchmarks = [
    {
        "name": "Gaussian_Free",
        "function": GaussianFree,
        "x_min": -40,
        "x_max": 40,
        "T_final": 5.0
    },

    {
        "name": "HO_Ground",
        "function": HarmonicOscillatorGroundState,
        "x_min": -10,
        "x_max": 10,
        "T_final": 10.0
    }
]

#Run the benchmarks for each N and dt
for benchmark in benchmarks:

    problem_folder = (run_folder / benchmark["name"])

    problem_folder.mkdir(parents=True,exist_ok=True)

    for N in N_values:

        grid = Grid1D(
            x_min=benchmark["x_min"],
            x_max=benchmark["x_max"],
            num_points=N
        )

        wave, potential = benchmark["function"](grid)

        for dt in dt_values:

            setting_folder = (problem_folder/ f"N{N}_dt{dt}")

            print(benchmark["name"],"N =", N,"dt =", dt)

            RunComparison(
                N=N,
                dt=dt,
                T_final=benchmark["T_final"],
                grid=grid,
                wave_func=wave,
                potential=potential,
                setting_folder=setting_folder
            )