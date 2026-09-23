import numpy as np


class WaveFunction:
    def __init__(self, grid, psi):
        """
        grid is a Grid1D object
        psi is an array containing the wave function values at the grid points
        """

        #self.grid has x and dx
        self.grid = grid

        self.psi = np.asarray(psi, complex);
       
        #Include a check for sizes of these two arrays

    
    def ProbabilityDensity(self):
        # |psi(x)|^2 
        return np.abs(self.psi) ** 2

    def Norm(self):
        # |psi(x)|^2 dx  ; should approximate 1 for a normalized wave function
        # Consider using a np trapezoid for this
        return np.sqrt(np.sum(self.ProbabilityDensity() * (self.grid.dx)))

    def Normalize(self):
        # Normalize the wave function so that the integral of |psi(x)|^2 dx = 1
        # DO NOT CALL THIS AT EVERY TIME STEP
        self.psi /= self.Norm()

    def Expectation_x(self):
        # <x> = integral of x * |psi(x)|^2 dx
        # Can't use norm method here cus x is array
        return np.sum(self.grid.x * self.ProbabilityDensity() * (self.grid.dx))

    @classmethod
    def GaussianPacket(cls, grid, x0, sigma, k0):

        x = grid.x

        
        envelope = np.exp(
            -(x - x0)**2 / (4 * sigma**2)
            #sigma is the width here, in Shankar 154 it is 2*delta^2
        )

        phase = np.exp(
            1j * k0 * x
        ) #k0 is the wave number, related to momentum by p0 = hbar * k0 (Planck relation)

        psi = envelope * phase

        wave = cls(grid, psi)

        wave.Normalize()

        return wave