# Split-Step Fourier method

This document derives the Split-Step Fourier (SSF) update used by this program and describes how the update is implemented in [`SSFSolver.py`](../../Solvers/SSFSolver.py). The method evolves a one-dimensional wavefunction under a time-independent potential on a uniform periodic spatial grid.

## 1. Starting equation

The time-dependent Schrödinger equation is

$$
i\hbar \frac{\partial \Psi(x,t)}{\partial t} = -\frac{\hbar^2}{2m}\frac{\partial^2 \Psi(x,t)}{\partial x^2} + V(x)\Psi(x,t).
$$

The Hamiltonian contains a kinetic energy operator and a potential energy operator:

$$
H = T + V,
\qquad
T = -\frac{\hbar^2}{2m}\frac{\partial^2}{\partial x^2}.
$$

Here $m$ is the particle mass, $\hbar$ is the reduced Planck constant, and $V(x)$ is the potential energy. In the current implementation, the potential does not vary with time. The code represents the wavefunction at grid points as a one-dimensional complex NumPy array.

For a time-independent Hamiltonian, the exact solution over a time step $\Delta t$ is

$$
\Psi(t+\Delta t) = e^{-iH\Delta t/\hbar}\Psi(t)
= e^{-i(T+V)\Delta t/\hbar}\Psi(t).
$$

One important note is that $T$ and $V$ generally do not commute. The kinetic operator uses spatial derivatives, while the potential operator multiplies the wavefunction by $V(x)$. Therefore, in general,

$$
TV\Psi \ne VT\Psi.
$$

This means that the full exponential cannot generally be replaced by the product of the kinetic and potential exponentials without making it an approximation.

## 2. Splitting the kinetic and potential evolution

If the two operators did commute, then the propagator could be factored exactly:

$$
e^{-i(T+V)\Delta t/\hbar}
= e^{-iV\Delta t/\hbar}e^{-iT\Delta t/\hbar}.
$$

Since they do not generally commute, this simple product is only a first-order splitting. The current implementation uses a symmetric splitting, also called Strang splitting:

$$
e^{-i(T+V)\Delta t/\hbar}
\approx
 e^{-iV\Delta t/(2\hbar)}
 e^{-iT\Delta t/\hbar}
 e^{-iV\Delta t/(2\hbar)}.
$$

The sequence of action is from right to left since we are dealing with operators. Each time step applies half of the potential evolution, then the full kinetic evolution, then the other half of the potential evolution.

The symmetry of this product cancels the leading splitting error that would appear in a one-sided product. For a sufficiently smooth solution and time-independent operators, the local splitting error is $O((\Delta t)^3)$ per step. Over a fixed total time, the accumulated temporal error is second order, $O((\Delta t)^2)$.

## 3. Applying the potential operator in position space

The potential operator acts by multiplication:

$$
(V\Psi)(x)=V(x)\Psi(x).
$$

Therefore, its time-evolution operator is also a pointwise multiplication:

$$
e^{-iV\Delta t/(2\hbar)}\Psi(x)
= e^{-iV(x)\Delta t/(2\hbar)}\Psi(x).
$$

At grid point $x_j$, the half-step is

$$
\Psi_j \leftarrow e^{-iV_j\Delta t/(2\hbar)}\Psi_j.
$$

The code calculates this multiplier once in `_build_operators` and stores it as `self.V_half`. Since the potential and time step stay fixed during a run, the same array is used at every step.

## 4. Applying the kinetic operator in Fourier space

The kinetic operator contains a second spatial derivative. 

$$
\Psi(x)=e^{ikx}
\quad\Longrightarrow\quad
\frac{\partial^2\Psi}{\partial x^2}=-k^2\Psi(x).
$$

Consequently, the kinetic operator acts on a Fourier mode as multiplication by its kinetic energy:

$$
T e^{ikx}=\frac{\hbar^2k^2}{2m}e^{ikx}.
$$

In Fourier space, the kinetic evolution over one time step is therefore

$$
\widetilde{\Psi}(k,t+\Delta t)
= e^{-i\hbar k^2\Delta t/(2m)}\widetilde{\Psi}(k,t),
$$

where $\widetilde{\Psi}(k,t)$ is the Fourier transform of the wavefunction. This multiplication by a phase is the reason the kinetic part is efficient to apply in Fourier space.

On a grid with $N$ points and spacing $\Delta x$, the code obtains the discrete Fourier wave numbers from

$$
k_q = 2\pi\,\text{fftfreq}(N,\Delta x).
$$

with numpy.fft.fftfreq getting the frequencies associated with the bins of Fast Fourier Transform (FFT) using the grid spacing. The factor $2\pi$ converts the frenquencies to angular wave numbers.

For each wave number $k_q$, it calculates the kinetic phase

$$
\exp\left(-i\frac{\hbar k_q^2\Delta t}{2m}\right).
$$

In the implementation this array is stored as `self.T_full`. NumPy's FFT converts the wavefunction to Fourier space, and its inverse FFT returns it to position space.

## 5. One complete time step

Combining the potential and kinetic steps gives

$$
\begin{aligned}
\Psi^{(1)} &= e^{-iV\Delta t/(2\hbar)}\Psi^n, \\
\widetilde{\Psi}^{(1)} &= \mathcal{F}\{\Psi^{(1)}\}, \\
\widetilde{\Psi}^{(2)} &= e^{-i\hbar k^2\Delta t/(2m)}\widetilde{\Psi}^{(1)}, \\
\Psi^{(2)} &= \mathcal{F}^{-1}\{\widetilde{\Psi}^{(2)}\}, \\
\Psi^{n+1} &= e^{-iV\Delta t/(2\hbar)}\Psi^{(2)}.
\end{aligned}
$$

With $\mathcal{F}$ and $\mathcal{F}^{-1}$ being the discrete Fourier transform and its inverse. In code, the steps in `Step` are:

1. Multiply `wave.psi` by `self.V_half`.
2. Apply `np.fft.fft` to transform the wavefunction to Fourier space.
3. Multiply by `self.T_full` to apply the kinetic evolution.
4. Apply `np.fft.ifft` to return to position space.
5. Multiply by `self.V_half` again.

The resulting array replaces `wave.psi`.

## 6. Periodic boundary condition

The discrete Fourier transform represents a periodic extension of the grid data. The value at one end of the domain connects to the value at the other end. The grid therefore stores $N$ points from $x_{\min}$ to $x_{\max}-\Delta x$, without storing a duplicate point at $x_{\max}$:

$$
\Delta x=\frac{x_{\max}-x_{\min}}{N}.
$$

The current solver checks that `grid.periodic` is true. If the grid is not periodic, it raises an error because this FFT implementation is not designed for Dirichlet boundaries. A wavefunction that reaches one edge of the domain can wrap around to the opposite edge, so the domain should be large enough that this does not affect the part of the wavefunction being studied.

## 7. Accuracy and conservation

For a real potential, each potential multiplier has magnitude one:

$$
\left|e^{-iV_j\Delta t/(2\hbar)}\right|=1.
$$

Likewise, each kinetic multiplier has magnitude one for real $k_q$:

$$
\left|e^{-i\hbar k_q^2\Delta t/(2m)}\right|=1.
$$

The Fourier transform and inverse transform also preserve the discrete norm when used as a pair. Thus the SSF update is expected to preserve the discrete norm, with perhaps small deviations caused by floating-points round up.

Since the potential and kinetic operators do not commute in general, so the split update does not exactly equal the exponential of the full Hamiltonian. The method has second-order temporal accuracy from the symmetric splitting, but a large $\Delta t$ can still produce phase and splitting errors.

The kinetic operator here is Fourier spectral: it uses the Fourier wave numbers and the energy $\frac{\hbar^2 k^2}{(2m)}$. This differs from the finite-difference kinetic operator used by CN. As a result, a direct CN-versus-SSF comparison can reflect both time-propagation error and spatial kinetic-energy discretization differences.

## 8. Scope and limitations

- SSF supports periodic boundaries in the current implementation. Dirichlet boundaries and the infinite square well are not supported by this solver.
- The potential is real and time-independent in the current implementation.
- The kinetic evolution is applied in Fourier space, while the potential evolution is applied in position space.
- The symmetric splitting has second-order temporal accuracy for sufficiently smooth solutions and fixed total simulation time.
- The Fourier representation is especially accurate for smooth periodic functions. Discontinuities or a wavefunction that does not match smoothly across the periodic boundary can reduce the observed spatial convergence.
- Error and runtime comparisons depend on the initial state, potential, grid, time step, total simulated time, and reference solution. The scheme alone does not establish that SSF is always more accurate or faster than CN.

## Implementation

- SSF operator construction and time stepping: [`Solvers/SSFSolver.py`](../../Solvers/SSFSolver.py)
- Periodic and Dirichlet grid construction: [`grid.py`](../../grid.py)
- Simulation boundary handling and observables: [`DesktopUI/Simulation.py`](../../DesktopUI/Simulation.py)

## References

[11.3: The Split-Step Fourier Method - Physics LibreTexts](https://phys.libretexts.org/Bookshelves/Mathematical_Physics_and_Pedagogy/Computational_Physics_(Chong)/11%3A_Discrete_Fourier_Transforms/11.03%3A_The_Split-Step_Fourier_Method)

[On the Analytical and Numerical Solutions of the One‐Dimensional Nonlinear Schrodinger Equation - Farag - 2021 - Mathematical Problems in Engineering - Wiley Online Library](https://onlinelibrary.wiley.com/doi/full/10.1155/2021/3094011)

[An introduction to the Split Step Fourier Method using MATLAB](https://www.researchgate.net/publication/281441538_An_introduction_to_the_Split_Step_Fourier_Method_using_MATLAB)