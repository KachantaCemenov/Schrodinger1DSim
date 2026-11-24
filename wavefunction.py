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

        self.name = "" #declare in the initialization methods
       
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
        weights = self.ProbabilityDensity()
        total_weight = np.sum(weights)

        if not np.isfinite(total_weight) or total_weight <= 0:
            raise ValueError("Cannot calculate position for a zero or nonfinite wave.")

        return float(np.sum(self.grid.x * weights) / total_weight) #normalized

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

    """Trapezoid was halving the endpoints
    def Expectation_p(self, hbar=1.0):

        k, phi_k = self.Momentum_WaveFunction()

        prob_k = np.abs(phi_k)**2

        expec_k = np.trapezoid(k * prob_k, k) 

        return hbar * expec_k
    """

    def Expectation_p(self, hbar=1.0):
        k, phi_k = self.Momentum_WaveFunction()
        weights = np.abs(phi_k) ** 2

        total_weight = np.sum(weights)
        if not np.isfinite(total_weight) or total_weight <= 0:
            raise ValueError(
                "Cannot calculate momentum for a zero or nonfinite wave."
            )

        return float(hbar * np.sum(k * weights) / total_weight)


    def Expectation_energy(self, potential, mass=1.0, hbar=1.0):

        if not np.isfinite(mass) or mass <= 0:
            raise ValueError("Mass must be finite and positive.")
        #T
        k, phi_k = self.Momentum_WaveFunction()
        momentum_weights = np.abs(phi_k) ** 2
        momentum_total = np.sum(momentum_weights)

        # V
        position_weights = self.ProbabilityDensity()
        position_total = np.sum(position_weights)

        if not np.isfinite(momentum_total) or momentum_total <= 0 or not np.isfinite(position_total) or position_total <= 0:
            raise ValueError("Cannot calculate energy for a zero or nonfinite wave.")

        potential_values = np.asarray(potential.values, dtype=float)
        if potential_values.shape != self.psi.shape:
            raise ValueError("Potential and wave dimensions do not match.")
        if not np.all(np.isfinite(potential_values)):
            raise ValueError("This energy calculation requires a finite potential.")

        kinetic = np.sum((hbar**2 * k**2 / (2 * mass)) * momentum_weights) / momentum_total

        potential_energy = np.sum(potential_values * position_weights) / position_total

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

        wave.name = "GaussianPacket"

        return wave


    """
    This one has an analytically defined energy formula: 
    E = h_bar^2 * k^2 / (2 * m)
    k is wave number, it's dependent on n
    """
    @classmethod
    def PlaneWave(cls, grid, n: int = 1): #n is state number (-/+ 1, -/+2, ...)
       
        #L = grid.x[-1] - grid.x[0]
        L = len(grid.x) * grid.dx #Acommodating the periodic position space

        k = 2 * np.pi * n / L

        psi = np.exp(1j * k * grid.x)

        wave = cls(grid, psi)
        wave.Normalize()

        wave.name = "PlaneWave"

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

        if not isinstance(n, (int, np.integer)) or n < 0:
            raise ValueError("n must be a nonnegative integer.")

        if not np.all(np.isfinite([mass, omega, hbar, center])) or min(mass, omega, hbar) <= 0:
            raise ValueError("Use finite parameters and positive mass, omega, and hbar.")

        x = grid.x

        #bunch of constants
        const = np.sqrt(mass * omega / hbar) * (x - center)

        psi = np.exp(-0.5 * const**2)

        if n > 0:
            previous = psi
            psi = np.sqrt(2.0) * const * previous

            for order in range(1, n):
                following = (np.sqrt(2.0 / (order + 1)) * const * psi - np.sqrt(order / (order + 1)) * previous)
                previous, psi = psi, following

        wave = cls(grid, psi)

        norm = wave.Norm()
        if not np.isfinite(norm) or norm <= 0:
            raise ValueError("Cannot represent this eigenstate on the selected grid.")

        wave.Normalize()
        wave.name = "HarmonicOscillatorEigenstate"

        return wave
