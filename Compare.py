from Solvers.cranknicolson import CrankNicolsonSolver
from Solvers.SSFSolver import SplitStepFourierSolver
from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential

import csv
from pathlib import Path
from datetime import datetime

folder_path = Path("Results\Comparisons")
file_path = folder_path / f"comparison_data_{datetime.now().date.strftime('%B %d, %Y')}.csv"


N_values = [256, 512, 1024, 2048]
dt_values = [0.01, 0.005, 0.0025, 0.001]

T_final = 5.0 #In seconds

for N in N_values:
    for dt in dt_values:
        
        grid = Grid1D(
            x_min=-40,
            x_max=40,
            num_points=N
        )
        
        initial_wave = WaveFunction.GaussianPacket(
            grid=grid,
            x0=-15,
            sigma=5,
            k0=9
        )
        wave_cn = initial_wave.copy()
        wave_ssf = initial_wave.copy()
        """
        potential = Potential.Barrier(
            grid,
            height=30,
            x_left=10,
            x_right=23
        )
        """

        CN_solver = CrankNicolsonSolver(grid=grid, potential=potential, dt=dt, mass=1.0, hbar=1.0)
        SSF_solver = SplitStepFourierSolver(grid=grid, potential=potential, dt=dt, mass=1.0, hbar=1.0)
        
        steps = int(T_final / dt)

        for step in range(steps):
            CN_solver.step(wave_cn)
            SSF_solver.step(wave_ssf)
