import numpy as np

from scipy.sparse import diags, identity
from scipy.sparse.linalg import splu

class CrankNicolsonSolver:

    def __init__(self, grid,potential,dt,mass = 1.0,hbar = 1.0):
        self.grid = grid
        self.potential = potential
        self.dt = dt
        self.mass = mass
        self.hbar = hbar

        self._build_matrices()


    def _build_matrices(self):

        dx = self.grid.dx
        V = self.potential.values[1:-1]  # Exclude boundary points
        N = len(V)  # Number of interior points

        # Construct the tridiagonal Hamiltonian

        diagonal = (self.hbar**2 / (self.mass * dx**2) + V) 
        off_diagonal = (-self.hbar**2 / (2 * self.mass * dx**2)) 

        #Hamiltonian
        H = diags([off_diagonal * np.ones(N - 1), 
                   diagonal, 
                   off_diagonal * np.ones(N - 1)], 
                  offsets=[-1, 0, 1], format='csc') #csc for the scipy splu

        I = identity(N, dtype = complex, format='csc')

        factor = 1j * self.dt / (2 * self.hbar)

        self.A = I + factor * H
        self.B = I - factor * H

        self.A_lu = splu(self.A)  # LU decomposition 

    def step(self, wave):

        # A * psi(t+1) = B * psi(t)

        psi = wave.psi
        psi_inside = psi[1:-1]  # Exclude boundary points

        rhs = self.B @ psi_inside

        psi_new_inside = self.A_lu.solve(rhs)
        new_psi = np.zeros_like(psi, dtype=complex)
        new_psi[1:-1] = psi_new_inside  # Exclude boundary points

        wave.psi = new_psi