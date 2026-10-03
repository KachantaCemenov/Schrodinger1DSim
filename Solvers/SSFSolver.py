import numpy as np


class SplitStepFourierSolver:

    def __init__(self,grid,potential,dt,mass=1.0,hbar=1.0):
        self.grid = grid
        self.potential = potential
        self.dt = dt
        self.mass = mass
        self.hbar = hbar

        self._build_operators()


    def _build_operators(self):

        dx = self.grid.dx
        N = len(self.grid.x)

        # Fourier frequencies
        k = 2 * np.pi * np.fft.fftfreq(N,d=dx)

        # Half potential step: exp[-i V dt / (2 hbar)]
        self.V_half = np.exp(-1j * self.potential.values * self.dt / (2 * self.hbar))

        # Kinetic energy: T = p^2 / 2m = hbar^2 k^2 / 2m
        # Kinetic step: exp[-i T dt / hbar]
        self.T_full = np.exp(-1j * self.hbar * k**2 * self.dt / (2 * self.mass))


    def Step(self, wave):

        psi = wave.psi

        # 1/2 potential propagator
        psi = self.V_half * psi

        # To momentum space
        psi_k = np.fft.fft(psi)

        # 1 kinetic propagator
        psi_k = self.T_full * psi_k

        # To x space
        psi = np.fft.ifft(psi_k)

        # 1/2 potential propagator
        psi = self.V_half * psi

        wave.psi = psi