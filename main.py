import matplotlib.pyplot as plt

from grid import Grid1D
from wavefunction import WaveFunction


grid = Grid1D(
    x_min = -20,
    x_max = 20,
    num_points = 1000
)

wave = WaveFunction.gaussian_packet(
    grid=grid,
    x0=-5,
    sigma=1,
    k0=3
)

print("Norm:", wave.norm())
print("<x>:", wave.expectation_x())

plt.plot(
    grid.x,
    wave.probability_density()
)

plt.xlabel("Position x")
plt.ylabel("Probability density |psi|²")
plt.title("Initial Gaussian Wave Packet")

plt.show()