import matplotlib.pyplot as plt

from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential
from Solvers.cranknicolson import CrankNicolsonSolver

#Initialize 1D grid
grid = Grid1D(
    x_min = -30,
    x_max = 30,
    num_points = 2000
)

#Initialize wave function
wave = WaveFunction.gaussian_packet(
    grid=grid,
    x0=-15,
    sigma=1,
    k0=10
)

#Initialize potential function

#potential = Potential.free_particle(grid)
#potential = Potential.harmonic_oscillator(grid, mass=1.0, omega=1.0)

potential = Potential.barrier(
    grid,
    height=25,
    x_left=10,
    x_right=20
)

#Initialize Crank-Nicolson solver
solver = CrankNicolsonSolver(
    grid=grid,
    potential=potential,
    dt=0.001,
    mass=1.0,
    hbar=1.0
)



#Visualization
print("Norm:", wave.norm())
print("<x>:", wave.expectation_x())

"""
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
#Initial shape
probability_line, = ax1.plot(
    grid.x,
    wave.probability_density(),
    label="|ψ|²"
)

potential_line, = ax2.plot(
    grid.x,
    potential.values,
    "--",
    label="V(x)"
)
ax1.set_xlabel("x")
ax1.set_ylabel("|ψ|²")
ax2.set_ylabel("V(x)")

plt.ion()

# Advance 1000 time steps
for i in range(10000):
    solver.step(wave)

    probability_line.set_ydata(wave.probability_density())
    
    ax1.set_title(f"Time step: {i :.3f}, Norm: {wave.norm():.3f}, <x>: {wave.expectation_x():.3f}")
    print("Norm:", f"{wave.norm():.18f}")
    print("<x>:", f"{wave.expectation_x():.18f}")


    plt.draw()
    plt.pause(0.01)

plt.ioff()
plt.show()
"""
frames = []

for i in range(50000):
    solver.step(wave)

    # Only save every 20th timestep
    if i % 20 == 0:
        frames.append({
            "probability": wave.probability_density().copy(),
            "norm": wave.norm(),
            "expected_x": wave.expectation_x(),
            "time": i * solver.dt,
            "step": i
        })

from matplotlib.animation import FuncAnimation

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