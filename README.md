# Schrodinger1DSim (README.md unfinished)

<!-- CTRL + E then CTRL + W to wrap words -->

This application propagates your one dimension wave function to the next time step by solving the time-dependent Schrodinger equation. 
Shape of the results of the wave function at subsequent time step is joined into an animation after the calculation to demonstrate how this result change.
Result of a wave function (more on this below) in the current iteration of this program is a 1D matrix. A Fourier transform of the spatial domain produced the second animation of the momentum space.

## Discretization

This program works on the basis of discretizing the spatial domain. The $\Psi(x, t)$ in your Schrodinger equation

$$
i\hbar \frac{\partial \Psi(x, t)}{\partial t} = -\frac{\hbar^2}{2m}\frac{\partial^2 \Psi(x, t)}{\partial x^2} + V(x)\Psi(x, t)
$$

is theoretically supposedly a continuous function across your spatial (x-axis) domain. To compute it numerically on a computer, however, that $\Psi(x, t)$ at a certain $t$ needs to become a array containing its value at each $x$ in the domain. Now, the number of possible $x$ in your domain depends on how you slice your spatial domain. In this program, you specify an integer $N$ as the number of grid points after discretizing the spatial domain, and the spacing between them is $dx$. Then the number of rows of $\Psi(x)$ equals N. The number of column is, at the time of writing this, is strictly one as far as this program is concerned. Only one-dimension problems are supported at the moment. $\Psi(x)$ is currently stored as a one-dimension NumPy array.

Then, with total time being $T$, you can declare a $dt$ to slice the temporal domain into $\frac{T}{dt}$ pieces and evaluate $\Psi(x, t)$ after each $dt$.

Potential operator $V$ is currently implemented as unchanging with time. 




## The solvers

Capitalizing on the fact that $\Psi(x, t = 0)$ now has discrete values after each $dx$, one can use finite difference method (derived from Taylor series) to approximate the first derivative with time and second derivative with space to solve for $\Psi(x, t = 0 + dt)$. 

Or one can argue that if one slice $dx$ and $dt$ so thin over spatial and temporal domains, the non-commuting kinetic and potential operator in the Hamiltonian in the wave propagator $e^{\frac{-iHdt}{\hbar}}$ can be approximately splitted and then applied seperately using Strang splitting. Fast Discrete Fourier Transform (FFT) and its inverse counterpart are used to transform $\Psi(x, t)$ from spatial to momentum space and back, so that the potential operator is applied to $\Psi(x, t)$ in the spatial, and kinetic operator applied in momentum space. 

The former is the Crank-Nicolson (CN) method, and the latter is Split-Step Fourier (SSF) method. Each of these methods are interesting in its own rights, and wanting to compare them was the motivation behind which I built this program. 

So far, I have observed that their performance depends a lot on details of the problem and configurations. Although SSF was seen to be faster and more accurate in many configurations, CN was more accurate especially in some problems with very large $N$ and $\frac{T}{dt}$. Details on these solvers and my observations will be added the "docs" folder.
<!-- TODO THAT DOCS FOLDER -->

Because Fast Discrete Fourier Transform requires a periodic boundary condition, the current implementation of SSF does not support certain potential configurations such as the infinite square well. Periodic boundary condition means that the value of $\Psi(x, t)$ at the end of spatial domain is warped around to the start of the domain: $\Psi(x = x_{max}, t) = \Psi(x = x_{min}, t)$. In the code, the two endpoints are treated as one, the grid stores $N$ points from $x_{min}$ to $x_{max} - dx$.

The other boundary condition implemented in this application is the zero-value boundaries (Dirichlet): $\Psi(x = x_{max}, t) = \Psi(x = x_{min}, t) = 0$. Current only CN is able to work with this condition. This condition forces the wave function to behave inside the domain as if it is in an infinite square well.

## Features

This program has four tabs: Simulation, Benchmark, Read Benchmark, and Recommendation.

### Simulation tab

This tab contains the functions to propagate one wave function in a potential configuration over $N$ grid points and $\frac{T}{dt}$ time steps. At each $dt$, these values of the wave function are recorded:
- Norm
- Expected position, $\langle x \rangle$
- Expected momentum, $\langle p \rangle$
- Expected energy, $\langle E \rangle$

Currently the supported wave types are Gaussian wave packet, Harmonic oscillator, and Plane wave. Currently supported potential types are Free (no potential), Infinite Square Well, Barrier, Harmonic. 
The program also supports typing in your own wave function. The rules for typing in your own mathematical expression is in "docs" folder and in "Help" inside the program. 

Current supported boundary conditions are:
- Periodic: N grid points with $dx = \frac{x_{max} - x_{min}}{N}$. Value of the $\Psi$ at the end boundary warps to the start: $\Psi(x = x_{max}, t) = \Psi(x = x_{min}, t)$
- Zero-value boundaries (Dirichlet) / Non-periodic boundaries: N grid points with $dx = \frac{x_{max} - x_{min}}{N - 1}$. Value of the $\Psi$ at the both boundaries are forced to be zero.

Because the current implementation of FFT requires periodic boundary condition, SSF cannot run Infinite Square Well. CN can run all of potential configurations in either boundary conditions except infinite square well - that requires Dirichlet.

The $\Psi(x)$ array is saved at most 400 times (due to technical limits) accross all time steps into a list of frames which is showed as an animation after the calculation. A FFT is applied to the spatial domain to produce the momentum distribution graph. 

### Benchmark and Read Benchmark

In Benchmark tab you can specify one or many problems to be run over a number of different $N$ and $dt$ values with both SSF and CN. In this program one set of such problems is called a "run".   

The purpose is to compare the performance of SSF and CN across a set of problem as well as to observe their error convergence (how much of $L^2$ error are we expecting to change in CN and SSF from reducing $dx$ by half?).
Since the point is comparison, currently some configurations are unallowed for Benchmark because of limitation in my current implementation of SSF. The current setup requires periodic boundary and does not accept the infinite square well. 

In Read Benchmark tab, you can observe graphs based on results from one of your Benchmark runs. You can inspect an error value in each problem at different configuration specified in the run, as well as observe the convergence of the errors. The convergence plots are produced for each problem by holding $N$ (or $dt$) fixed and observe how an error value change with $dt$ (or $N$).

In problems without an implemented analytical solutions, functions involve $L^2$ error are unavailable.

### Recommendation

The Recommendation tab is for finding the faster solver for a certain requirements. The data needs to be loaded from one of your Benchmark runs. 

In this tab you specify your problem in the Benchmark run and select a certain $N$ and $dt$ in that run or let it look through all $N$ and $dt$. After that, enter a restraint on any of the conservation error:
- Maximum $L^2$ error among all time steps.
- Maximum norm drift (deviation from norm at $t = 0$, or 1) among all time steps
- Maximum energy drift (deviation from energy at $t = 0$) among all time steps\
And the program will find the fastest solver satisfying your restraint and specified configuration.

The table has a selection for showing qualified or disqualified candidates. The results are printed in words.
