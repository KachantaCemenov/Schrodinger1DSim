import csv
from pathlib import Path
from datetime import datetime
from time import perf_counter
import numpy as np

from Solvers.cranknicolson import CrankNicolsonSolver
from Solvers.SSFSolver import SplitStepFourierSolver
from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential
from TimeSteps import CountTimeSteps


"""
For a specified grid, wave fucntion, and potential (a combination of 3 is thereby called a "problem"). The problem is only taken as argument for this script.
This script contains methods to run a problem using both solvers on a specific combination of N and dt specified outside of this script (taken as arguments) and write out resulting data.
This script is meant to be used in another scripts that read the data as comparison.

"""




def RunComparison(setting_folder : Path,
                  N, dt, T_final, grid, wave_func, potential, analytical,
                  mass: float = 1.0, hbar: float = 1.0, *, steps: int | None = None #BenchmarkTab will pass the steps
                  ):
    if steps is None:
        steps = CountTimeSteps(T_final, dt)

    #Initialize solvers
    CN_solver = CrankNicolsonSolver(grid=grid, potential=potential, dt=dt, mass=mass, hbar=hbar)
    SSF_solver = SplitStepFourierSolver(grid=grid, potential=potential, dt=dt, mass=mass, hbar=hbar)

            
    #These two functions change the parameter wave function, need a copy
    wave_cn = wave_func.Copy()  # Create a copy of the wave function for the CN solver
    wave_ssf = wave_func.Copy()  # Create a copy of the wave function for the SSF solver

    RunSolvers_AndWriteToFile(N = N, dt = dt, T_final = T_final, grid = grid, mass = mass, hbar = hbar, 
                              wave_cn = wave_cn, wave_ssf = wave_ssf, potential = potential, analytical = analytical,
                                CN_solver = CN_solver, SSF_solver = SSF_solver, setting_folder = setting_folder, steps=steps)

    wave_cn = wave_func.Copy()  
    wave_ssf = wave_func.Copy()  

    RunSolvers_AndWriteRuntime(N = N, dt = dt, T_final = T_final, wave_cn = wave_cn, wave_ssf = wave_ssf, potential = potential, 
                                CN_solver = CN_solver, SSF_solver = SSF_solver, setting_folder = setting_folder, steps=steps)



def ReferenceDiagnostics(grid, numerical, reference):
    #convert to np array
    numerical = np.asarray(numerical, dtype = complex)
    reference = np.asarray(reference, dtype = complex)

    if numerical.shape != grid.x.shape or reference.shape != grid.x.shape:
        raise ValueError("Reference and numerical wave dimensions do not match.")
    if not np.all(np.isfinite(numerical)) or not np.all(np.isfinite(reference)):
        raise ValueError("Reference diagnostics require finite wave values.")

    raw_L2 = L2Error(grid, numerical, reference)

    #Normalize for measuring overlap, preserve original amplitudes for L2
    numerical_norm = float(np.linalg.norm(numerical))
    reference_norm = float(np.linalg.norm(reference))

    if not np.isfinite(numerical_norm) or not np.isfinite(reference_norm):
        raise ValueError("Wave norms must be finite.")
    if numerical_norm <= 0 or reference_norm <= 0:
        return raw_L2, "N/A", "N/A"

    overlap = np.vdot(reference / reference_norm, numerical / numerical_norm) # <psi|psi>

    #if overlap too small ignore it
    if abs(overlap) <= 1e-12:
        return raw_L2, "N/A", "N/A"

    phase_difference = float(np.angle(overlap))

    aligned = numerical * np.exp(-1j * phase_difference) #remove the phase different
    aligned_L2 = L2Error(grid, aligned, reference)       #then recalculate L2 error

    return raw_L2, phase_difference, aligned_L2


def CalculateReferenceErrors(grid, wave_cn, wave_ssf, analytical, time):
    if analytical is None:
        return ("N/A",) * 6 #When there is no analytical implemented, btw that comma is important

    reference = analytical(time)

    cn = ReferenceDiagnostics(grid, wave_cn.psi, reference)
    ssf = ReferenceDiagnostics(grid, wave_ssf.psi, reference)

    return (cn[0], ssf[0],
            cn[1], ssf[1],
            cn[2], ssf[2])

def RunSolvers_AndWriteToFile(N, dt, T_final, grid, mass, hbar,
                              wave_cn: WaveFunction, wave_ssf: WaveFunction, potential: Potential, 
                              analytical,
                              CN_solver: CrankNicolsonSolver, SSF_solver: SplitStepFourierSolver, 
                              setting_folder, *, steps):

    metric_path = setting_folder / f"comparison_data.csv" #path for metrics

    #steps = int(T_final / dt) This get passed from RunComparison()


    with open(metric_path, mode='w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(['Setting:', f'dt = {dt}', f'N = {N}'])
            writer.writerow(["step", "time", 
                             "CN_norm", "CN_expected_x", "CN_expected_p", "CN_expected_energy", 
                             "SSF_norm", "SSF_expected_x", "SSF_expected_p", "SSF_expected_energy", 
                             "CN_L2Error", "SSF_L2Error",
                            "CN_phase_difference", "SSF_phase_difference",
                            "CN_phase_aligned_L2Error", "SSF_phase_aligned_L2Error"])

            """ Move this initial writing block into the loop
            cn_L2, ssf_L2 = CalculateReferenceErrors(grid, wave_cn, wave_ssf, analytical, time=0)

            #Write initial state
            writer.writerow(["0", "0", wave_cn.Norm(), wave_cn.Expectation_x(), wave_cn.Expectation_p(hbar = hbar), 
                             #wave_cn.Expectation_energy(potential, mass = mass, hbar = hbar),
                             CN_solver.Expectation_energy(wave_cn),
                             wave_ssf.Norm(), wave_ssf.Expectation_x(), wave_ssf.Expectation_p(hbar = hbar), 
                             wave_ssf.Expectation_energy(potential, mass = mass, hbar = hbar),
                             cn_L2, ssf_L2])
            """

            for step in range(steps + 1):

                time = (step) * dt  #step go from 0 so +1

                reference_errors = CalculateReferenceErrors(grid, wave_cn, wave_ssf, analytical, time)

                writer.writerow([step, time, 
                                wave_cn.Norm(), wave_cn.Expectation_x(), wave_cn.Expectation_p(hbar = hbar), CN_solver.Expectation_energy(wave_cn),
                                wave_ssf.Norm(), wave_ssf.Expectation_x(), wave_ssf.Expectation_p(hbar = hbar), wave_ssf.Expectation_energy(potential, mass = mass, hbar = hbar),
                                #cn_L2, ssf_L2, These are in reference_errors 
                                *reference_errors
                            ])

                if step < steps:
                    CN_solver.Step(wave_cn)
                    SSF_solver.Step(wave_ssf)

def RunSolvers_AndWriteRuntime(N, dt, T_final, 
                               wave_cn: WaveFunction, wave_ssf: WaveFunction, potential: Potential, 
                               CN_solver: CrankNicolsonSolver, SSF_solver: SplitStepFourierSolver, 
                               setting_folder, *, steps):

    
    runtime_path = setting_folder / f"runtime_data.txt"   #path for runtime
    #steps = int(T_final / dt)
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


#L^2 error is integral of (numerical - analytical)^2 over dx
def L2Error(grid, numerical, analytical):
    diff = numerical - analytical 

    #L2err = np.sqrt(np.trapezoid(np.abs(diff)**2, grid.x))
    L2err = np.sqrt(grid.dx * np.sum(np.abs(diff)**2))

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
