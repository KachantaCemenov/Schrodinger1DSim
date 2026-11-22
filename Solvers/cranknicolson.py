import numpy as np

from scipy.sparse import diags, identity
from scipy.sparse.linalg import splu

class CrankNicolsonSolver:

    def __init__(self, grid,potential,dt,mass = 1.0,hbar = 1.0, periodic = True):
        self.grid = grid
        self.potential = potential
        self.dt = dt
        self.mass = mass
        self.hbar = hbar
        self.periodic = periodic

        self._BuildMatrices(periodic)


    def _BuildMatrices(self, periodic):

        dx = self.grid.dx
        if periodic:
            V = self.potential.values
        else: 
            V = self.potential.values[1:-1]  # Exclude boundary points
        N = len(V)  # Number of interior points

        # Construct the tridiagonal Hamiltonian

        diagonal = (self.hbar**2 / (self.mass * dx**2) + V) 
        off_diagonal = (-self.hbar**2 / (2 * self.mass * dx**2)) 

        #Hamiltonian
        if periodic:
            H = diags([off_diagonal * np.ones(N - 1), 
                       diagonal, 
                       off_diagonal * np.ones(N - 1)], 
                      offsets=[-1, 0, 1], format='lil') 


            H[0, N - 1] = off_diagonal
            H[N - 1, 0] = off_diagonal
            H = H.tocsc()
        else: 
            H = diags([off_diagonal * np.ones(N - 1), 
                       diagonal, 
                       off_diagonal * np.ones(N - 1)], 
                      offsets=[-1, 0, 1], format='csc') 

        self.H = H 
        I = identity(N, dtype = complex, format='csc')

        factor = 1j * self.dt / (2 * self.hbar)

        self.A = I + factor * H
        self.B = I - factor * H

        self.A_lu = splu(self.A)  # LU decomposition 

    def Step(self, wave):

        # A * psi(t+1) = B * psi(t)

        psi = wave.psi
        if self.periodic:
            psi_inside = psi
        else:
            psi_inside = psi[1:-1]  # Exclude boundary points

        rhs = self.B @ psi_inside

        psi_new_inside = self.A_lu.solve(rhs)
        new_psi = np.zeros_like(psi, dtype=complex)
        if self.periodic:
            new_psi = psi_new_inside
        else:
            new_psi[1:-1] = psi_new_inside  # Exclude boundary points]

        wave.psi = new_psi


    #A method that calculates the energy using CN built Hamiltonian
    #E = (psi* H psi) / (psi* psi)
    def Expectation_energy(self, wave):
        psi = np.asarray(wave.psi, dtype = complex)

        if psi.shape != self.grid.x.shape:
            raise ValueError("Wave and solver grid dimensions do not match.")

        #The Dirichlet Hamiltonian contains only interior points
        inside = psi if self.periodic else psi[1:-1]

        probability = float(np.vdot(inside, inside).real)
        if not np.isfinite(probability) or probability <= 0:
            raise ValueError("Cannot calculate energy for a zero or nonfinite wave.")

        H_psi = self.H @ inside
        energy = float(np.vdot(inside, H_psi).real / probability)

        if not np.isfinite(energy):
            raise ValueError("Calculated energy is not finite.")

        return energy