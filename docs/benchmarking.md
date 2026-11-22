# Benchmarking

This document explains how the Benchmark and Read Benchmark tabs compare Crank–Nicolson (CN) and Split-Step Fourier (SSF). It describes which problems can be benchmarked, how the program calculates the errors and record the runtimes

## 1. What one benchmark run contains

A benchmark run is made from one or more named problems, a list of grid sizes $N$, and a list of time steps $\Delta t$. For each problem, the program runs every combination of $N$ and $\Delta t$ with both CN and SSF.

The two solvers use copies of the same initial wavefunction and the same potential, grid, mass, $\hbar$, $N$, $\Delta t$, and final time. The program records values at $t=0$ and after every time step through $T_{\text{final}}$. Therefore, each completed comparison contains $T_{\text{final}}/\Delta t+1$ rows.

The final time must be an integer multiple of the time step so that $T_{\text{final}}/\Delta t$ is also an integer. Since the current implementation of SSF requires the periodic boundary condition, the benchmark problems also have to periodic so that a comparison between SSF and CN can be made. The Infinite Square Well is therefore not available in the Benchmark tab because it requires Dirichlet boundaries - it is available in Simulation tab with CN.

## 2. Errors recorded by the benchmark

### $L^2$ error

When an analytical reference solution is available, the program compares each numerical wavefunction with that reference at a same $t$. It calculates

$$
\left\|\Psi_{\mathrm{num}}-\Psi_{\mathrm{ref}}\right\| =
\sqrt{\Delta x\sum_j
\left|\Psi_{\mathrm{num},j}-\Psi_{\mathrm{ref},j}\right|^2}.
$$

The benchmark records the error at $t=0$ and after each step. The Read Benchmark and Recommendation tabs use the maximum recorded $L^2$ error across all time steps of each problem-solver pair as one of the main criteria to compare the solvers' performance.

The analytical reference is evaluated on the same grid points and normalized at $t=0$. The current references are available for these periodic preset problems:

- A Gaussian packet in a free-particle potential.
- A plane wave in a free-particle potential.
- A harmonic-oscillator eigenstate whose wave and potential frequencies match.
- A Gaussian packet in a harmonic-oscillator potential when its width is $\sigma=\sqrt{\hbar/(2m\omega)}$, giving a coherent state.

For other wave and potential combinations, custom initial wavefunctions, or Dirichlet boundaries, the current benchmark does not have an analytical reference and records the $L^2$ error as unavailable ("N/A"). These combinations can still be compared using the other recorded quantities.

### Norm drift

The program calculates the discrete norm as

$$
\|\Psi(t)\| = \sqrt{\Delta x\sum_j |\Psi_j(t)|^2}.
$$

The norm drift is the absolute change from the initial value:

$$
\Delta_{norm}(t) = \left|\|\Psi(t)\|-\|\Psi(0)\|\right|.
$$

The maximum norm drift is the largest $\Delta_{norm}$ over all $t$. The initial wavefunction is normalized by this setup, so its initial norm is usually 1 or close to 1. The calculation for maximum norm drift uses the recorded initial norm instead of the number 1.

### Energy drift

For each periodic benchmark state, SSF reports energy using the Fourier-space kinetic-energy diagnostic:

$$
\langle E\rangle =
\frac{\displaystyle\sum_q \frac{\hbar^2 k_q^2}{2m}|\widetilde{\Psi}_q|^2}
     {\displaystyle\sum_q |\widetilde{\Psi}_q|^2} +
\frac{\displaystyle\sum_j V_j|\Psi_j|^2}
     {\displaystyle\sum_j |\Psi_j|^2}.
$$

While CN reports energy using its own Hamiltonian matrix:

$$
\langle E\rangle = \frac{\Psi^\dagger H_{CN} \Psi}{(\Psi^\dagger \Psi)}.
$$

The energy drift is the absolute change from the initial reported energy,

$$
\Delta_E(t) = |\langle E(t)\rangle-\langle E(0)\rangle|,
$$

and the maximum energy drift is the largest value over all $t$.

In an ealier version of this program (v0.1.0-beta) there was a CN energy diagnostic bug which has now been fixed. The program does not support marking or recalculating the CN energy values in the earlier bugged version.

### Global phase difference and phase-aligned $L^2$ error

The benchmark also records the global phase difference between the numerical wavefunction and the analytical reference. It first normalizes both wavefunctions and calculates their overlap:

$$
C =
\left\langle
\frac{\Psi_{\mathrm{ref}}}{\|\Psi_{\mathrm{ref}}\|}
\middle|
\frac{\Psi_{\mathrm{num}}}{\|\Psi_{\mathrm{num}}\|}
\right\rangle.
$$

The global phase difference is the angle of this overlap:

$$
\Delta\phi = \arg(C).
$$

This value is reported in radians and wrapped to the range $[-\pi,\pi]$. It describes a single overall phase offset between the two wavefunctions.

The ordinary $L^2$ error compares the wavefunctions directly, including this global phase offset. Phase-aligned $L^2$ error is $L^2$ error calculated after removing the phase offset by:

$$
\Psi_{\mathrm{num,aligned}} = e^{-i\Delta\phi}\Psi_{\mathrm{num}}.
$$

It then calculates

$$
\left\|\Psi_{\mathrm{num,aligned}}-\Psi_{\mathrm{ref}}\right\| =
\sqrt{\Delta x\sum_j
\left|\Psi_{\mathrm{num,aligned},j}-\Psi_{\mathrm{ref},j}\right|^2}.
$$

The phase-aligned error reflects the difference in the waves' amplitudes while ignoring the phase offset. Comparing it with the ordinary $L^2$ error illustrate how much deviation was due to a global phase offset.

These two diagnostics require an analytical reference. They are reported as unavailable if there is no reference or if the normalized overlap is too small for reliable phase alignment. They are available in the Read Benchmark time-series graph and table; they are not currently used by the convergence plots or Recommendation constraints.


## 3. How to read convergence results

The Read Benchmark tab can show a quantity while varying $\Delta t$ at fixed $N$ or vice versa. The available quantities are maximum $L^2$ error, maximum norm drift, or maximum energy drift for each completed combination.

- **Vary $\Delta t$ at fixed $N$** to examine temporal convergence. The spatial grid error remains present and can eventually limit the improvement as $\Delta t$ gets smaller.
- **Vary $N$ at fixed $\Delta t$** to examine spatial convergence. The time-stepping error remains present and can eventually limit the improvement as $N$ gets larger.

To estimate an observed order, compare errors in a range where the quantity is decreasing consistently and the other source of error is small. If halving a parameter reduces the error by about a factor of four, that is consistent with second-order convergence in that parameter. A plateau, irregular trend, or increase can mean that another error source, boundary effects, or floating-point effects are controlling the result.

These plots show the maximum error over the entire run, not only the error at the final time. The graph uses a logarithmic horizontal axis. Its vertical axis is logarithmic when all plotted values are positive; if any values are zero, it uses a linear vertical axis so those values remain visible. A plot needs at least two completed parameter values to show a trend.

## 4. Runtime measurements

For each configuration, the benchmark records a CN runtime and an SSF runtime. These measurements time the repeated `Step` calls over the full number of time steps. They do not include the initialization of the solvers and the process of writing data to disk.

The current code records one timing per solver for a configuration, and not an averaged repeated timing trials. The measurements therefore can vary with hardware, software environment, background load, and run order. The elapsed time for the entire benchmark run is a separate measurement and includes work beyond the timed solver steps.

## 5. Reading benchmark files

A completed run folder contains a `run.json` manifest with the run configuration and completed problem/grid/time-step combinations. Each combination has its own folder containing:

- `comparison_data.csv`, with a row for the initial state and each later time step. It stores time, norm, expected position, momentum and energy for CN and SSF, and the $L^2$ errors when analytical solution is available.
- `runtime_data.txt`, with the measured step-loop runtime for CN and SSF and the associated $N$, $\Delta t$, final time, and step count.

The Read Benchmark tab loads these files to display time-series plots, tables, and convergence plots. The Recommendation tab uses the same benchmark data to identify the fastest tested solver that meets the selected error tolerances. Its error values are measured over the recorded time points for the selected problem, $N$, and $\Delta t$.

## Implementation

- Benchmark problem setup and supported analytical references: [`DesktopUI/Benchmark.py`](../DesktopUI/Benchmark.py)
- Per-step data and runtime recording, and the $L^2$ error calculation: [`ComparingMethods/CompareMethods.py`](../ComparingMethods/CompareMethods.py)
- Convergence selections and quantities: [`DesktopUI/BenchmarkConvergence.py`](../DesktopUI/BenchmarkConvergence.py)
- Reading result files and plotting: [`DesktopUI/BenchmarkResults.py`](../DesktopUI/BenchmarkResults.py)
- Recommendation metrics and tolerance checks: [`DesktopUI/Recommendation.py`](../DesktopUI/Recommendation.py)
- Solver equations and implementation details: [`Crank–Nicolson method`](solvers/Crank-Nicolson.md) and [`Split-Step Fourier method`](solvers/Split-Step-Fourier.md)
