import numpy as np


"""
https://archive.org/details/SchultenNotesOnQuantumMechanicsFreescience1877/page/n27/mode/2up
eq 2.71, p. 21, chapter 2.4
TO DO: Write a document in LaTex about how that equation was manipulated (they use a different convention for the packet width)
"""
def FreeGaussianAnalytical(grid, t, x0, sigma, k0, mass=1.0, hbar=1.0):
    x = grid.x

    tau = hbar * t / (2 * mass * sigma**2) #Just a substitution term for a frequently-appear constant term

    velocity = hbar * k0 / mass #p = mv then de Broglie relation p = hbar * k0 

    A = (1 / (2 * np.pi * sigma**2))**0.25

    envelope = np.exp(-(x - x0 - velocity * t)**2 / (4 * sigma**2 * (1 + 1j * tau)))

    phase = np.exp(1j * k0 * x - 1j * hbar * k0**2 * t / (2 * mass))

    psi = (A / np.sqrt(1 + 1j * tau) * envelope * phase)

    return psi

"""
E_n = h_bar * omega * (n + 1/2)
psi_n(x,t) = psi_n(x,0) * exp(-i * E_n * t / h_bar)
"""
def HarmonicOscillatorEigenstateAnalytical(initial_wave, t, n, omega, hbar=1.0):
    energy = hbar * omega * (n + 0.5)

    phase = np.exp(-1j * energy * t / hbar)

    return initial_wave.psi * phase



def PlaneWaveAnalytical(initial_wave, grid, t, n, mass = 1.0, hbar = 1.0):
    L = len(grid.x) * grid.dx

    k = 2 * np.pi * n / L

    #E of free particle = p^2 / 2m = hbar^2*k^2 / 2m
    #de Broglie relation p = hbar * k 
    energy = (hbar**2 * k**2) / (2*mass)
    
    propagator = np.exp(-1j * energy * t / hbar)

    return initial_wave.psi * propagator

#https://arxiv.org/abs/quant-ph/9810036
#TODO: Address this in the writeup
def GaussianHarmonicAnalytical(grid, t, x0, k0, mass, omega, hbar):
    #Assuming coherent state
    # sigma = sqrt(hbar / (2*m*omega))

    x = grid.x

    #initial momentum
    p0 = hbar * k0
    #width
    sigma = np.sqrt(hbar / (2 * mass * omega))

    #Classicle position and momentum
    x_center = x0 * np.cos(omega * t) + (p0 / (mass * omega)) * np.sin(omega * t)
    p_center = p0 * np.cos(omega * t) - mass * omega * x0 * np.sin(omega * t)

    normalization_term = (1/(2 * np.pi * sigma**2))**0.25
    envelope = np.exp(-(x - x_center)**2 / (4 * sigma**2))

    phase = np.exp(1j / hbar * (p_center * (x - x_center / 2) + p0 * x0/2) - 1j * omega * t/2)

    return normalization_term * envelope * phase