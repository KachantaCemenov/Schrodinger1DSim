import matplotlib.pyplot as plt

from grid import Grid1D
from wavefunction import WaveFunction
from potential import Potential

#Initialize 1D grid
grid = Grid1D(
    x_min = -20,
    x_max = 20,
    num_points = 1000
)

#Initialize wave function
wave = WaveFunction.gaussian_packet(
    grid=grid,
    x0=-5,
    sigma=1,
    k0=3
)

#Initialize potential function

potential = Potential.free_particle(grid)
#potential = Potential.harmonic_oscillator(grid, mass=1.0, omega=1.0)
"""
potential = Potential.barrier(
    grid,
    height=5,
    x_left=0,
    x_right=2
)
"""


#Visualization
print("Norm:", wave.norm())
print("<x>:", wave.expectation_x())


fig, ax1 = plt.subplots()

ax1.plot(
    grid.x,
    wave.probability_density(),
    label="|ψ|²"
)

ax1.set_xlabel("Position x")
ax1.set_ylabel("Probability density |psi|^2")
ax1.set_title("Initial Gaussian Wave Packet")
ax1.legend()

ax2 = ax1.twinx()

ax2.plot(
    grid.x,
    potential.V,
    color='orange',
    label="Potential V(x)"
)
ax2.set_ylabel("Potential V(x)")
ax2.legend()

plt.show()
