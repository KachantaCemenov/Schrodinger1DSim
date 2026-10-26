import sys
print(sys.executable)

from pathlib import Path
from datetime import datetime
from spicy.constants import hbar, m_e

from CompareMethods import RunComparison
from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential
from AnalyticalSolutions import FreeGaussianAnalytical, HarmonicOscillatorEigenstateAnalytical, PlaneWaveAnalytical


HBAR = hbar
ELECTRON_MASS = m_e

N_values = [500, 1000, 2000]
dt_values = [1e-17,       #0.01 fs
             5e-18,       #0.005 fs
             2.5e-18,     #0.0025 fs
             1e-18        #0.001 fs
             ]

timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

comparing_folder = Path(__file__).resolve().parent

run_folder = (comparing_folder/"Results"/f"run_{timestamp}")

run_folder.mkdir(parents=True,exist_ok=True)


#Each of these is a benchmark problem
def GaussianFree(grid): #grid differs on each N

    """
    x0 = -15
    sigma = 5
    k0 = 3
    mass = 1.0
    hbar = 1.0
    """
    mass = ELECTRON_MASS
    hbar = HBAR

    x0 = -20e-9    # 20nm to the left
    sigma = 2e-9   #width 2nm
    k0 =  2e9     #wavelength = 2pi/k0 = about 3nm here, in reasonable range for electron

    #REMEMBER: v = hbar*k0 / m - use that to estimate where the particle end. Best not let it go near the boundary

    wave = WaveFunction.GaussianPacket(grid=grid, x0=x0, sigma=sigma, k0=k0)

    potential = Potential.FreeParticle(grid)

    #python closure to pass this function to CompareMethods
    def analytical(t):
        return FreeGaussianAnalytical(grid=grid, t=t, x0=x0, sigma=sigma,
                                      k0=k0,mass=mass,hbar=hbar)

    return wave, potential, analytical

def HarmonicOscillatorGroundState(grid):
    """
    mass = 1.0
    omega = 1.0
    hbar = 1.0
    n = 0
    """
    mass = ELECTRON_MASS
    omega = 1e15     # T = 2pi / omega = about 6.28 fs
    hbar = HBAR
    n = 0

    wave = WaveFunction.HarmonicOscillatorEigenstate(grid=grid, n=n, mass=mass, 
                                                     omega=omega, hbar=hbar)

    potential = Potential.HarmonicOscillator(grid, mass=mass, omega=omega)

    #python closure to pass this function to CompareMethods
    def analytical(t):
        return HarmonicOscillatorEigenstateAnalytical(initial_wave=wave, t=t, n=n,omega=omega, hbar=hbar)

    return wave, potential, analytical

def PlaneWaveFree(grid):

    n = 4
    mass = ELECTRON_MASS
    hbar = HBAR

    wave = WaveFunction.PlaneWave(grid=grid, n=n)
    potential = Potential.FreeParticle(grid)

    def analytical(t):
        return PlaneWaveAnalytical(initial_wave=wave, grid=grid, t=t, n=n,mass=mass, hbar=hbar)

    return wave, potential, analytical


benchmarks = [
    {
        "name": "Gaussian_Free",
        "function": GaussianFree,
        "x_min": -50e-9,
        "x_max": 50e-9,
        "T_final": 100e-15
    },

    {
        "name": "HO_Ground",
        "function": HarmonicOscillatorGroundState,
        "x_min": -10e-9,
        "x_max": 10e-9,
        "T_final": 100e-15
    },

    {
        "name": "PlaneWave_Free",
        "function": PlaneWaveFree,
        "x_min": -50e-9,
        "x_max": 50e-9,
        "T_final": 100e-15
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

        wave, potential, analytical = benchmark["function"](grid)

        for dt in dt_values:

            setting_folder = (problem_folder/ f"N{N}_dt{dt}")
            setting_folder.mkdir(parents=True,exist_ok=True)

            print(benchmark["name"],"N =", N,"dt =", dt)

            RunComparison(
                setting_folder=setting_folder,
                N=N,
                dt=dt,
                T_final=benchmark["T_final"],
                grid=grid,
                wave_func=wave,
                potential=potential,
                analytical=analytical,
                mass=1.0, hbar=1.0 #TODO: Make these decleared constants in this script
            )