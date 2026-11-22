# Crank–Nicolson method

This document derives the Crank–Nicolson (CN) update used by this program and describes how the update is implemented in [`cranknicolson.py`](../../Solvers/cranknicolson.py). The method evolves a one-dimensional wavefunction under a time-independent, real potential on a uniform spatial grid.

## 1. Starting equation

The time-dependent Schrödinger equation is

$$
i\hbar \frac{\partial \Psi(x,t)}{\partial t} = -\frac{\hbar^2}{2m}\frac{\partial^2 \Psi(x,t)}{\partial x^2} + V(x)\Psi(x,t).
$$

Here, $m$ is the particle mass, $\hbar$ is the reduced Planck constant ($\frac{h}{2\pi}$), and $V(x)$ is the potential energy. In the current implementation, the potential does not vary with time. The code represents the wavefunction at grid points as a one-dimensional complex NumPy array.

## 2. Spatial discretization

Let the spatial grid be uniformly spaced by $\Delta x$. Write

$$
x_j = x_{\min} + j\Delta x,
\qquad \Psi_j(t) \approx \Psi(x_j,t),
$$

where $j$ indexes the grid points. 

Now, we turn to Taylor expansion to approximate the second order derivative with space in Hamiltonian.Let $h=\Delta x$. Taylor-expand the wavefunction around $x_j$:

$$
\begin{aligned}
\Psi(x_j+h) &= \Psi_j + h\Psi'_j + \frac{h^2}{2}\Psi''_j + \frac{h^3}{6}\Psi'''_j + \frac{h^4}{24}\Psi^{(4)}_j + \frac{h^5}{120}\Psi^{(5)}_j + O(h^6), \\
\Psi(x_j-h) &= \Psi_j - h\Psi'_j + \frac{h^2}{2}\Psi''_j - \frac{h^3}{6}\Psi'''_j + \frac{h^4}{24}\Psi^{(4)}_j - \frac{h^5}{120}\Psi^{(5)}_j + O(h^6).
\end{aligned}
$$

Add the them together and subtract $2\Psi_j$. The odd-derivative terms cancel:

$$
\Psi(x_j+h)-2\Psi_j+\Psi(x_j-h)
= h^2\Psi''_j+\frac{h^4}{12}\Psi^{(4)}_j+O(h^6).
$$

Divide by $h^2$:

$$
\frac{\Psi(x_j+h)-2\Psi_j+\Psi(x_j-h)}{h^2}
= \Psi''_j+\frac{h^2}{12}\Psi^{(4)}_j+O(h^4).
$$

Therefore, the centered finite-difference approximation is

$$
\left.\frac{\partial^2\Psi}{\partial x^2}\right|_{x_j}
\approx
\frac{\Psi_{j+1}-2\Psi_j+\Psi_{j-1}}{(\Delta x)^2},
$$

The term $\frac{h^2}{12}\Psi^{(4)}_j$ was the leading error, since it was proportional to $h^2$, I omitted it and consider the approximation has a second-order accuracy. Hence the error of this approximation after omitting that term is $O((h)^2)$ or $O((\Delta x)^2)$ for sufficiently smooth wavefunctions.

Now we substituting that approximation of $\frac{\partial^2\Psi}{\partial x^2}$ into the Hamiltonian expression:

$$
{H}\Psi(x_j) = -\frac{\hbar^2}{2m(\Delta x)^2}\Psi(x_{j-1})
					+ \frac{\hbar^2}{m(\Delta x)^2}\Psi(x_j)+V_j\Psi(x_j)
					-\frac{\hbar^2}{2m(\Delta x)^2}\Psi(x_{j+1})
$$

where $V_j$ is only applied for $\Psi(x_j)$ since this is an approximation for the Hamiltonian at $x_j$. In operator forms I have:

$$
H_{jj} = \frac{\hbar^2}{m(\Delta x)^2}+V_j,
\qquad
H_{j,j-1}=H_{j,j+1}=-\frac{\hbar^2}{2m(\Delta x)^2},
$$

Then the Hamiltonian matrix would look like this: 

$$
{H}=
\begin{bmatrix}
\frac{\hbar^2}{m(\Delta x)^2}+V_0 & -\frac{\hbar^2}{2m(\Delta x)^2}   & 0   & \cdots & 0 \\
-\frac{\hbar^2}{2m(\Delta x)^2}   & \frac{\hbar^2}{m(\Delta x)^2}+V_1 & -\frac{\hbar^2}{2m(\Delta x)^2}   & \ddots & \vdots \\
0   & -\frac{\hbar^2}{2m(\Delta x)^2}   & \frac{\hbar^2}{m(\Delta x)^2}+V_2 & \ddots & 0 \\
\vdots & \ddots & \ddots & \ddots & -\frac{\hbar^2}{2m(\Delta x)^2} \\
0   & \cdots & 0 & -\frac{\hbar^2}{2m(\Delta x)^2} & \frac{\hbar^2}{m(\Delta x)^2}+V_{N-1}
\end{bmatrix}.
$$ 

which is an $N \times N$ tridiagonal matrix. With $\Psi(x)$ being a $N \times 1$ matrix, ${H}\Psi(x)$ would produce a $N \times 1$.


The grid is constructed in [`grid.py`](../../grid.py):

- **Periodic:** the grid has $N$ points and omits the duplicate endpoint $x_{\max}$, so $\Delta x=(x_{\max}-x_{\min})/N$.
- **Dirichlet:** the grid includes both endpoints, so $\Delta x=(x_{\max}-x_{\min})/(N-1)$, with $\Psi_0=\Psi_{N-1}=0$.

## 3. Crank–Nicolson time step

Now that we have found a way to approximate the Hamiltonian, let's go back to the Schrodinger equation. Let $\Psi^n$ denote the vector at time $t_n=n\Delta t$, and let $\Psi^{n+1}$ be the vector one time step later. Crank–Nicolson method approximates the first order time derivative by averaging the change with time:

$$
i\hbar\frac{\Psi^{n+1}-\Psi^n}{\Delta t} = \frac{1}{2}H\left(\Psi^{n+1}+\Psi^n\right).
$$

Multiplying by $\Delta t/(i\hbar)$ and collecting the unknown $\Psi^{n+1}$ terms on the left gives

$$
\left(I+\frac{i\Delta t}{2\hbar}H\right)\Psi^{n+1}
= \left(I-\frac{i\Delta t}{2\hbar}H\right)\Psi^n.
$$

Now define

$$
A = I + \frac{i\Delta t}{2\hbar}H,
\qquad
B = I - \frac{i\Delta t}{2\hbar}H.
$$

Each time step therefore solves the linear system

$$
A\Psi^{n+1} = B\Psi^n.
$$
which because H is tridiagonal, is also a tridiagonal matrix equation.

The Crank–Nicolson time discretization is second-order accurate in $\Delta t$ for a time-independent Hamiltonian and sufficiently smooth solution. Together with the spatial difference approximation, the nominal global discretization error is $O((\Delta t)^2+(\Delta x)^2)$ under the smoothness assumption. Discontinuities in the potential or solution can affect observed convergence rates.

## 4. Boundary conditions and matrix structure

### Periodic boundaries

For periodic boundaries, the finite-difference stencil wraps from the final grid point back to the first:

$$
\Psi_{N-1}=\Psi_0.
$$

Thus, $H$ is cyclic tridiagonal. In addition to the usual tridiagonal entries, the implementation sets

$$
H_{0,N-1}=H_{N-1,0}=-\frac{\hbar^2}{2m(\Delta x)^2}.
$$

Although $x_{\max}$ is not stored as a grid point, it is identified with $x_{\min}$ by periodicity. In code, `Grid1D` makes the periodic grid with `endpoint=False`, and `_BuildMatrices` adds the two corner entries to the sparse Hamiltonian.

### Dirichlet boundaries

For zero-value (Dirichlet) boundaries, the endpoint values are fixed at zero:

$$
\Psi_0 = \Psi_{N-1} = 0 \quad\text{for every }t.
$$

The solver removes the endpoint values from the wavefunction and solves only for the $N-2$ interior values. The resulting interior Hamiltonian is tridiagonal with no periodic corner entries. At each calculation step, the new full-size array is initialized to zero and the solved interior values are assigned to indices `1:-1`. This keeps both endpoints at zero without solving for them.

For the infinite square well in the Simulation tab, the UI constructs a grid between the well walls, enforces zero wavefunction at those walls, and passes the finite interior potential values to CN. The solver does not place infinite-valued potential entries into its interior Hamiltonian. The current benchmark workflow does not support the infinite square well because it runs both CN and SSF, while the SSF implementation requires periodic boundaries.

## 5. How the code constructs and applies the update

The implementation follows these steps:

1. **Select the potential samples.** For periodic boundaries it uses all values in `potential.values`. For Dirichlet boundaries it uses `potential.values[1:-1]`, matching the interior unknowns.
2. **Build the sparse Hamiltonian.** `diags` creates the tridiagonal matrix from the diagonal and off-diagonal formulas above. For periodic boundaries, the two wraparound entries are added. The matrix is converted to CSC sparse format.
3. **Build the CN matrices.** The code creates the complex identity $I$ and constructs $A$ and $B$ using the factors $\pm i\Delta t/(2\hbar)$.
4. **Factor $A$ once.** `splu(self.A)` stores a sparse LU factorization during solver initialization. Since $H$, $\Delta t$, $m$, and $\hbar$ remain fixed for a run, the same factorization is reused at every time step.
5. **Advance the wavefunction.** In `Step`, it computes `rhs = B @ psi_inside`, solves $A\Psi(t = t+dt)=\text{rhs}$ with the stored LU factorization, then writes the result back to the wavefunction. For Dirichlet boundaries, it writes only the interior and leaves the endpoints zero.

The repeated operation is a sparse triangular solve after factorization, rather than a fresh matrix factorization at every step. This reduces the work required across a long run.

## 6. Stability and conservation properties

For a real potential and the stated boundary conditions, the discrete Hamiltonian $H$ is Hermitian. The CN update can be written

$$
\Psi(t+dt)=A^{-1}B\Psi(t).
$$

Because $A$ and $B$ are functions of the same Hermitian matrix, this update is unitary. Consequently, it preserves the discrete norm (up to an extend in this numerical solution). CN is stable for this linear Schrödinger evolution, but that does not imply accuracy: large $\Delta t$ can still produce substantial phase error. Spatial accuracy is likewise limited by $\Delta x$.

In exact arithmetic, the discrete energy associated with $H$ is also conserved because the update commutes with $H$. There is a diagnostic mismatch in the current application: for simulations with periodic bounday condition, the reported energy calculates kinetic energy using Fourier-space $\frac{\hbar^2 k^2}{(2m)}$, while CN advances the state using a finite-difference kinetic Hamiltonian. These are not identical discrete kinetic operators, so the reported CN energy drift need not be zero even when the CN update preserves the energy associated with its own matrix $H$. For Dirichlet simulations, the energy diagnostic uses a finite-difference kinetic expression aligned with the CN discretization.

The code does not renormalize the wavefunction after each CN step, because that would defeat the purpose of measuring the norm deviation.

## 7. Scope and limitations

- CN supports periodic and Dirichlet boundaries in the Simulation tab. The potential is real and time-independent in the current implementation.
- The periodic-grid norm and the Dirichlet-grid norm $\int |\Psi(x)|^2\,dx$ are discretely approximated by calculating $\Delta x\sum_j |\Psi_j|^2$ over the represented points (interior points for Dirichlet boundaries).
- The finite-difference kinetic operator has a different dispersion relation from the Fourier spectral kinetic operator used by SSF. Differences between CN and SSF therefore reflect both their time-propagation methods and their spatial kinetic-energy discretizations.
- Error and runtime comparisons depend on the initial state, potential, grid, time step, total simulated time, and the reference solution used. The scheme alone does not establish that one solver is always more accurate or faster.

## Implementations

- CN matrix assembly and time stepping: [`Solvers/cranknicolson.py`](../../Solvers/cranknicolson.py)
- Periodic and Dirichlet grid construction: [`grid.py`](../../grid.py)
- Simulation boundary handling and infinite-well setup: [`DesktopUI/Simulation.py`](../../DesktopUI/Simulation.py)
- Split-step implementation for comparison: [`Solvers/SSFSolver.py`](../../Solvers/SSFSolver.py)

## References
<!-- TODO citing in lines-->
[Numerical Solution of Schrödinger Equation by Crank–Nicolson Method - Khan - 2022 - Mathematical Problems in Engineering - Wiley Online Library](https://onlinelibrary.wiley.com/doi/full/10.1155/2022/6991067)

[On the Analytical and Numerical Solutions of the One‐Dimensional Nonlinear Schrodinger Equation - Farag - 2021 - Mathematical Problems in Engineering - Wiley Online Library](https://onlinelibrary.wiley.com/doi/full/10.1155/2021/3094011)

[A comparison of numerical approaches to the solution of the time-dependent Schrödinger equation in one dimension - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7594019/)
