import numpy as np
from scipy.special import eval_hermite
from math import factorial


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

    def Copy(self):
        # Return a copy 
        return WaveFunction(self.grid, self.psi.copy())


    #Do Fourier transform
    #https://www.geeksforgeeks.org/maths/fourier-transform/

    def Momentum_WaveFunction(self):
        #phi(k) = 1/sqrt(2pi) * integral of psi(x) * exp(-ikx) dx

        dx = self.grid.dx
        N = len(self.psi)

        # Array of k corresponding to Fourier transform of array of x
        k = 2 * np.pi * np.fft.fftfreq(N, d=dx)

        # Fourier on psi(x) <- This is the Amplitude array, must match with k array above
        phi_k = (
            dx / np.sqrt(2 * np.pi) *
            np.fft.fft(self.psi)
        )

        # Shift the zero component to center (matching my position space)
        k = np.fft.fftshift(k)
        phi_k = np.fft.fftshift(phi_k)

        return k, phi_k
    
    def Expectation_p(self, hbar=1.0):

        k, phi_k = self.Momentum_WaveFunction()

        prob_k = np.abs(phi_k)**2

        expec_k = np.trapezoid(
            k * prob_k,
            k
        )

        return hbar * expec_k


    def Expectation_energy(self, potential, mass=1.0, hbar=1.0):

        # T
        k, phi_k = self.Momentum_WaveFunction()

        prob_k = np.abs(phi_k)**2

        norm_k = np.trapezoid(prob_k, k)

        kinetic = np.trapezoid((hbar**2 * k**2 / (2 * mass)) * prob_k, k) / norm_k


        # V
        x = self.grid.x
        prob_x = self.ProbabilityDensity()

        norm_x = np.trapezoid(prob_x, x)

        potential_energy = np.trapezoid(potential.values * prob_x, x) / norm_x


        return (kinetic + potential_energy).real


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


    """
    This one has an analytically defined energy formula: 
    E = h_bar^2 * k^2 / (2 * m)
    k is wave number, it's dependent on n
    """
    @classmethod
    def PlaneWave(cls, grid, n: int): #n is state number (-/+ 1, -/+2, ...)
        L = grid.x[-1] - grid.x[0]

        k = 2 * np.pi * n / L

        psi = np.exp(1j * k * grid.x)

        wave = cls(grid, psi)
        wave.Normalize()

        return wave



    """
    https://phys.libretexts.org/Bookshelves/University_Physics/University_Physics_%28OpenStax%29/University_Physics_III_-_Optics_and_Modern_Physics_%28OpenStax%29/07%3A_Quantum_Mechanics/7.06%3A_The_Quantum_Harmonic_Oscillator
    https://en.wikipedia.org/wiki/Quantum_harmonic_oscillator

    H = h_bar * omega * (n + 1/2)
    n is wave number, n = 0, 1, 2, ...

    In a harmonic potential the shape should hold
    """
    @classmethod
    def HarmonicOscillatorEigenstate(cls, grid, n: int, mass=1.0, omega=1.0, hbar=1.0, center=0.0):
        x = grid.x

        #bunch of constants
        const = np.sqrt(mass * omega / (hbar * 2)) * (x - center)

        #normalization term
        normalization = (mass * omega / (hbar * np.pi))**(1/4) * (1 / np.sqrt(2**n * factorial(n)))
        
        psi = normalization * eval_hermite(n, const) * np.exp(-mass * omega * (x - center)**2 / (2 * hbar))

        wave = cls(grid, psi)
        wave.Normalize()

        return wave
