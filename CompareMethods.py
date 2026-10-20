from Solvers.cranknicolson import CrankNicolsonSolver
from Solvers.SSFSolver import SplitStepFourierSolver
from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential

import csv
from pathlib import Path
from datetime import datetime
from time import perf_counter
import numpy as np


"""
For a specified grid, wave fucntion, and potential (a combination of 3 is thereby called a "problem"). The problem is only taken as argument for this script.
This script contains methods to run a problem using both solvers on a specific combination of N and dt specified outside of this script (taken as arguments) and write out resulting data.
This script is meant to be used in another scripts that read the data as comparison.

"""




def RunComparison(setting_folder : Path,
                  N, dt, T_final, grid, wave_func, potential, analytical,
                  mass: float = 1.0, hbar: float = 1.0
                  ):
    

    #Initialize solvers
    CN_solver = CrankNicolsonSolver(grid=grid, potential=potential, dt=dt, mass=mass, hbar=hbar)
    SSF_solver = SplitStepFourierSolver(grid=grid, potential=potential, dt=dt, mass=mass, hbar=hbar)

            
    #These two functions change the parameter wave function, need a copy
    wave_cn = wave_func.Copy()  # Create a copy of the wave function for the CN solver
    wave_ssf = wave_func.Copy()  # Create a copy of the wave function for the SSF solver

    RunSolvers_AndWriteToFile(N = N, dt = dt, T_final = T_final, grid = grid, wave_cn = wave_cn, wave_ssf = wave_ssf, potential = potential, analytical = analytical,
                                CN_solver = CN_solver, SSF_solver = SSF_solver, setting_folder = setting_folder)

    wave_cn = wave_func.Copy()  
    wave_ssf = wave_func.Copy()  

    RunSolvers_AndWriteRuntime(N = N, dt = dt, T_final = T_final, wave_cn = wave_cn, wave_ssf = wave_ssf, potential = potential, 
                                CN_solver = CN_solver, SSF_solver = SSF_solver, setting_folder = setting_folder)




def RunSolvers_AndWriteToFile(N, dt, T_final, grid, wave_cn: WaveFunction, wave_ssf: WaveFunction, potential: Potential, analytical,
                              CN_solver: CrankNicolsonSolver, SSF_solver: SplitStepFourierSolver,
                setting_folder):

    metric_path = setting_folder / f"comparison_data.csv" #path for metrics

    steps = int(T_final / dt)


    with open(metric_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Setting:', f'dt = {dt}', f'N = {N}'])
            writer.writerow(["step", "time", "CN_norm", "CN_expected_x", "CN_expected_p", "CN_expected_energy", 
                             "SSF_norm", "SSF_expected_x", "SSF_expected_p", "SSF_expected_energy", "CN_L2Error", "SSF_L2Error"])


            #Analytical psi at t = 0
            exact_psi = analytical(0)
            cn_L2 = L2Error(grid, wave_cn.psi, exact_psi)
            ssf_L2 = L2Error(grid,wave_ssf.psi, exact_psi)

            #Write initial state
            writer.writerow(["0", "0", wave_cn.Norm(), wave_cn.Expectation_x(), wave_cn.Expectation_p(), wave_cn.Expectation_energy(potential),
                             wave_ssf.Norm(), wave_ssf.Expectation_x(), wave_ssf.Expectation_p(), wave_ssf.Expectation_energy(potential),
                             cn_L2, ssf_L2])

            for step in range(steps):
                CN_solver.Step(wave_cn)
                SSF_solver.Step(wave_ssf)

                time = (step + 1) * dt  #step go from 0 so +1

                #Calculate L^2 errors for both CN and SSF
                exact_psi = analytical(time)
                cn_L2 = L2Error(grid, wave_cn.psi, exact_psi)
                ssf_L2 = L2Error(grid,wave_ssf.psi, exact_psi)

                writer.writerow([
                    step + 1, time, wave_cn.Norm(), wave_cn.Expectation_x(), wave_cn.Expectation_p(), wave_cn.Expectation_energy(potential),
                    wave_ssf.Norm(), wave_ssf.Expectation_x(), wave_ssf.Expectation_p(), wave_ssf.Expectation_energy(potential),
                    cn_L2, ssf_L2
                ])

def RunSolvers_AndWriteRuntime(N, dt, T_final, wave_cn: WaveFunction, wave_ssf: WaveFunction, potential: Potential, 
                               CN_solver: CrankNicolsonSolver, SSF_solver: SplitStepFourierSolver, setting_folder):

    
    runtime_path = setting_folder / f"runtime_data.txt"   #path for runtime
    steps = int(T_final / dt)
    with open(runtime_path, mode='w', newline='') as file:
            
        start = perf_counter()
        for step in range(steps):
            CN_solver.Step(wave_cn)
        CN_runtime = perf_counter() - start

        start = perf_counter()
        for step in range(steps):
            SSF_solver.Step(wave_ssf)
        SSF_runtime = perf_counter() - start

        file.write(f"N = {N}\n")
        file.write(f"dt = {dt}\n")
        file.write(f"T_final = {T_final}\n")
        file.write(f"steps = {steps}\n")
        file.write(f'CN runtime: {CN_runtime:.6f} seconds\n')
        file.write(f'SSF runtime: {SSF_runtime:.6f} seconds\n')



def L2Error(grid, numerical, analytical):
    diff = numerical - analytical 

    L2err = np.sqrt(np.trapezoid(np.abs(diff)**2, grid.x))

    return L2err

    
"""
for N in N_values:
    for dt in dt_values:
        
        
        setting_folder = run_folder / f"N{N}_dt{dt}"
        setting_folder.mkdir(parents = True, exist_ok = True)

        metric_path = setting_folder / f"comparison_data.csv"
        runtime_path = setting_folder / f"runtime_data.txt"

        #Grid
        grid = Grid1D(
            x_min=-40,
            x_max=40,
            num_points=N
        )
        
        #Wave
        initial_wave = WaveFunction.GaussianPacket(
            grid=grid,
            x0=-15,
            sigma=5,
            k0=9
        )
        wave_cn = initial_wave.Copy()
        wave_ssf = initial_wave.Copy()

        #Pot
        potential = Potential.Barrier(
            grid,
            height=30,
            x_left=10,
            x_right=23
        )
        

        #Solvers
        CN_solver = CrankNicolsonSolver(grid=grid, potential=potential, dt=dt, mass=1.0, hbar=1.0)
        SSF_solver = SplitStepFourierSolver(grid=grid, potential=potential, dt=dt, mass=1.0, hbar=1.0)
        
        steps = int(T_final / dt)

        with open(metric_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Setting:', f'dt = {dt}', f'N = {N}'])
            writer.writerow(["step", "time", "CN_norm", "CN_expected_x", "CN_expected_p", "CN_expected_energy", 
                             "SSF_norm", "SSF_expected_x", "SSF_expected_p", "SSF_expected_energy"])
            #Write initial state
            writer.writerow(["0", "0", wave_cn.Norm(), wave_cn.Expectation_x(), wave_cn.Expectation_p(), wave_cn.Expectation_energy(potential),
                             wave_ssf.Norm(), wave_ssf.Expectation_x(), wave_ssf.Expectation_p(), wave_ssf.Expectation_energy(potential)])

            for step in range(steps):
                CN_solver.Step(wave_cn)
                SSF_solver.Step(wave_ssf)

                time = (step + 1) * dt  #step go from 0 so +1

                writer.writerow([
                    step + 1, time, wave_cn.Norm(), wave_cn.Expectation_x(), wave_cn.Expectation_p(), wave_cn.Expectation_energy(potential),
                    wave_ssf.Norm(), wave_ssf.Expectation_x(), wave_ssf.Expectation_p(), wave_ssf.Expectation_energy(potential)
                ])

        wave_cn = initial_wave.Copy()
        wave_ssf = initial_wave.Copy()

        #Run it again to record runtime
        with open(runtime_path, mode='w', newline='') as file:
            
            start = perf_counter()
            for step in range(steps):
                CN_solver.Step(wave_cn)
            CN_runtime = perf_counter() - start

            start = perf_counter()
            for step in range(steps):
                SSF_solver.Step(wave_ssf)
            SSF_runtime = perf_counter() - start

            file.write(f"N = {N}\n")
            file.write(f"dt = {dt}\n")
            file.write(f"T_final = {T_final}\n")
            file.write(f"steps = {steps}\n")
            file.write(f'CN runtime: {CN_runtime:.6f} seconds\n')
            file.write(f'SSF runtime: {SSF_runtime:.6f} seconds\n')
"""
