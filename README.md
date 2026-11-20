# Schrodinger1DSim (README.md unfinished)

<!-- CTRL + E then CTRL + W to wrap words -->

This application propagate your one dimension wave function to the next time step by solving the time-dependent Schrodinger equation. 
Shape of the results of the wave function at subsequent time step is joined into an animation after the calcualtion to demonstrate how this result change.
Result of a wave function (more on this below) in the current iteration of this program is a 1D matrix. A Fourier transform of the spatial domain produced the second animation of the momentum space.

## Discretization

This program works on the basis of discretizing the spatial domain. The $\Psi(x, t)$ in your Schrodinger equation

$$
i\hbar \frac{\partial \Psi(x, t)}{\partial t} = -\frac{\hbar^2}{2m}\frac{\partial^2 \Psi(x, t)}{\partial x^2} + V(x)\Psi(x, t)
$$

is theoretically supposedly a continuous function across your spatial (x-axis) domain. To compute it numerically on a computer, however, that $\Psi(x, t)$ needs to become a matrix containing its value at each $x$ in the domain. Now, the number of possible $x$ in your domain depends on how many time you slice your spatial domain. In this program, the number of time you slice your domain is $N$ and the distance between each of your slice is thus $dx$. The number of rows of $\Psi(x)$ equals N. The number of column is, at the time of writing this, is strictly one as far as this program is concerned. Only one-dimension problems are supported at the moment.

Potential operator $V$ is currently implemented as unchanging with time at this time. 

With total time being $T$, you can declare a $dt$ to slice the temporal domain and evaluate $\Psi(x, t)$ at each $dt$.


## The solvers

Capitalizing on the fact that $\Psi(x, t = 0)$ is now uncontinuous with a discrete value after each $dx$, one can use finite difference method (derived from Taylor series) for the first derivative with time and second derivative with space to solve for $\Psi(x, t = 0 + dt)$. 

Or one can argue that if one slice $dx$ and $dt$ so thin over spatial and temporal domains, the non-commuting kinetic and potential operator in the Hamiltonian in the wave propagator $e^{\frac{-iHdt}{\hbar}}$ can be splitted and then applied one after another. Fast Discrete Fourier Transform and its inverse counterpart are used to transform $\Psi(x, t)$ from spatial to momentum space and back, so that the potential operator is applied to $\Psi(x, t)$ in the spatial, and kinetic operator applied in momentum space. 

The former is the Crank-Nicolson (CN) method, and the latter is Split-Step Fourier (SSF) method. Each of these methods are interesting in its own rights, and wanting to compare them was the motivation behind which I built this program. 

So far, I have observed that in general, SSF is faster and more accurate in many configuration, with CN being more accurate especially in some problems with very large $\frac{N}{dx}$ and $\frac{T}{dt}$. Details on these solvers and my observations will be added the "docs" folder.
<!-- TODO THAT DOCS FOLDER -->

Due to Fast Discrete Fourier Transform requires a periodic boundary condition, the current implementation of SSF does not support certain potential configurations such as the infinite square well. Periodic boundary condition means that the value of $\Psi(x, t)$ at the end of spatial domain is warped around to the start of the domain: $\Psi(x = x_{max}, t) = \Psi(x = x_{min}, t)$.

The other boundary condition implemented in this application is the zero-value boundaries (Dirichlet): $\Psi(x = x_{max}, t) = \Psi(x = x_{min}, t) = 0$. Current only CN is able to work with this condition. This condition forces the wave function to behave inside the domain as if it is in an infinite square well.

## Features

This program has four tabs: Simulation, Benchmark, ReadBenchmark, and Recommendation.

### Simulation tab

This tab contains the functions to propagate one wave function in a potential configuration over $\frac{N}{dx}$ grid points and $\frac{T}{dt}$ time steps. At each $dt$, these values of the wave function are recorded:
- Norm
- Expected position, $\langle x \rangle$
- Expected momentum, $\langle p \rangle$
- Expected energy, $\langle E \rangle$

Currently the supported wave types are Gaussian wave packet, Harmonic oscillator, and Plane wave. Currently supported potential types are Free (no potential), Infinite Square Well, Barrier, Harmonic. 

Current supported boundary conditions are:
- Periodic: N grid points with $dx = \frac{x_{max} - x_{min}}{N}$. Value of the $\Psi$ at the end boundary warps to the start: $\Psi(x = x_{max}, t) = \Psi(x = x_{min}, t)$
- Zero-value boundaries (Dirichlet) / Non-periodic boundaries: N grid points with $dx = \frac{x_{max} - x_{min}}{N - 1}$. Value of the $\Psi$ at the both boundaries are forced to be zero and bounced back toward center.

Due to current implementation of FFS requires periodic boundary condition, SSF cannot run Infinite Square Well. CN can run all of potential configurations in either boundary conditions.

The $\Psi(x)$ array is save every 400 time steps into a list of frames which is showed as an animation after the calculation. A FFT is applied to the spatial domain to produce the momentum distribution graph.

### Benchmark and Read Benchmark

In Benchmark tab you can specify one or many problems to be run over a number of different $N$ and $dt$ values with both SSF and CN. In this program one set of such problems is called a "run".   

The purpose is to compare the performance of SSF and CN acrross a set of problem as well as to observe their error convergence (how much of $L^2$ error are we expecting to change in CN and SSF from reducing $dx$ by half?)

In Read Benchmark tab, you can observe graphs based on results from one of your Benchmark runs. You can inspect an error value in each problem at different configuration specified in the run, as well as observe the convergence of the errors. The convergence plots are produced for each problem by holding $N$ (or $dt$) still and observe how an error value change with $dt$ (or $N$)

### Recommendation

The Recommendation tab is for finding the faster solver for a certain requiments. The data needs to be loaded from one of your Benchmark runs. 

In this tab you specify your problem in the Benchmark run and select a certain $N$ and $dt$ in that run or let it look through all $N$ and $dt$. After that, enter a restraint on any of the conservation error:
- Maximum $L^2$ error among all time steps.
- Maximum norm drift (derivation from 1) among all time steps
- Maximum energy drift (derivation from energy at $t = 0$) among all time steps\
And the program will find the fastest solver satisfying your restraint and specified configuration.

The table has a selection for showing qualified or disqualified candidates. The results are printed in words.
