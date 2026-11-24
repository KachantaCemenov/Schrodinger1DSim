import matplotlib.pyplot as plt

from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential
from Solvers.cranknicolson import CrankNicolsonSolver
from datetime import datetime
from matplotlib.animation import FuncAnimation
import csv
from pathlib import Path

#Initialize 1D grid
grid = Grid1D(
    x_min = -30,
    x_max = 30,
    num_points = 2000
)

#Initialize wave function
"""
wave = WaveFunction.GaussianPacket(
    grid=grid,
    x0=-15,
    sigma=5,
    k0=9
)
wave = wave.Normalize()
"""
wave = WaveFunction.HarmonicOscillatorEigenstate(
    grid=grid,
    n=0,
    mass=1.0,
    omega=1.0,
    hbar=1.0
)

#Initialize potential function

#potential = Potential.FreeParticle(grid)
potential = Potential.HarmonicOscillator(grid, mass=1.0, omega=1.0)
"""
potential = Potential.Barrier(
    grid,
    height=30,
    x_left=0,
    x_right=23
)
"""
#Initialize Crank-Nicolson solver
solver = CrankNicolsonSolver(
    grid=grid,
    potential=potential,
    dt=0.001,
    mass=1.0,
    hbar=1.0
)



#Visualization and save



frames = []

date = datetime.now()
fd = date.strftime("%B %d, %Y")
print(fd)
print("CN")

output_folder = Path(__file__).resolve().parent / "Results" / "CSV"
output_folder.mkdir(parents=True, exist_ok=True)
output_path = output_folder / f"wavefunction_data_{fd}_CN.csv"

with output_path.open(mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["step", "time", "norm", "expected_x", "expected_p"])

    #Write in initial state because loop only return results after propagation
    writer.writerow([
        0, 
        0.0,
        wave.Norm(),
        wave.Expectation_x(),
        wave.Expectation_p()
        ])

    for i in range(50000):
        solver.Step(wave)
        step = i + 1

        time = step * solver.dt

        writer.writerow([
            step,
            time,
            wave.Norm(),
            wave.Expectation_x(),
            wave.Expectation_p()
        ])

        # Only save every 20th timestep for the visualization
        if step % 20 == 0:
            frames.append({
                "probability": wave.ProbabilityDensity().copy(),
                "norm": wave.Norm(),
                "expected_x": wave.Expectation_x(),
                "expected_p": wave.Expectation_p(),
                "time": time,
                "step": step
            })


fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

pot_line = ax2.plot(
    grid.x,
    potential.values,
    "--",
)

line, = ax1.plot(
    grid.x,
    frames[0]["probability"]
)
ax1.set_ylim(
    0,
    1.1 * max(
        frame["probability"].max()
        for frame in frames
    )
)

def update(frame):

    line.set_ydata(frame["probability"])

    print('\b' +
        f"t = {frame['time']:.3f}   "
        f"Norm = {frame['norm']:.12f}   "
        f"<x> = {frame['expected_x']:.3f}   "
        f"<p> = {frame['expected_p']:.3f}   "
        f"step = {frame['step']}"
        , end='\r'
    )

    return line,

animation = FuncAnimation(
    fig,
    update,
    frames=frames,
    interval=20,
    blit=True
)

plt.show()