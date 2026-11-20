NUMERICAL_HELP = {
    "mass": ("Particle mass. Must be positive.\n\n"
             "SI unit: kilogram (kg).\n"
             "1 pound = 0.45359237 kg.\n"
             "Electron mass is approximately 9.10938e-31 kg."), 
    "hbar": ("Reduced Planck constant: hbar = h / (2*pi).\n"
            "Must be positive.\n\n"
            "SI unit: joule-second (J*s), equivalent to kg*m^2/s.\n"
            "For SI calculations, use approximately 1.054571817e-34."),
    "x_min": ("Left boundary of the spatial domain.\n\n"
              "SI unit: metre (m). Must be less than x_max."),
    "x_max": ("Right boundary of the spatial domain.\n\n"
              "SI unit: metre (m). Must be greater than x_min."),
    "N": ("Number of spatial grid points. An integer with no physical unit.\n\n"
          "Increasing N while keeping the domain fixed decrease the grid spacing and decrease spatial error"
          "but increases computation and memory use.\n\n"
          "Periodic grid: dx = (x_max - x_min) / N.\n"
          "Nonperiodic grid: dx = (x_max - x_min) / (N - 1)."),
    "dt": ("Time step used to advance the wave function.\n"
            "Must be positive. SI unit: second (s).\n"
            "Smaller dt reduces time-discretization error but "
            "requires more steps. T_final / dt must be a whole number."),
    "T_final": ("Total evolution time, starting from t = 0.\n"
                "Must be positive.SI unit: second (s).\n"
                "Number of time steps = T_final / dt. "
                "This must be a positive whole number.\n"
                "For example, T_final = 1e-14 and dt = 1e-17 require 1000 steps."),
}

CONSTANT_HELP = {
    "mass": ("Fill the electron mass: approximately 9.10938e-31 kg.\n\n"
            "Uses scipy.constants.m_e.\n"
            "Uncheck to clear the field, or type a different mass.\n\n"
            "This value uses kilograms. Keep all other inputs in a consistent unit system."),
    "hbar": ("Fill the SI reduced Planck constant: "
            "approximately 1.054571817e-34 J*s.\n\n"
            "Uses scipy.constants.hbar.\n"
            "Uncheck to clear the field, or type a different value.\n\n"
            "For SI calculations, use kilograms, metres, seconds, and joules throughout."),
}


WAVE_HELP = {
    "Gaussian Packet": {
        "x0": ("Initial center of the Gaussian packet.\n\n"
               "SI unit: metre (m)"),
        "sigma": ("Initial standard deviation of the ideal Gaussian probability density. Must be positive.\n\n"
                "SI unit: metre (m).\n\n"
                "This code uses an amplitude envelope exp(-(x-x0)^2 / (4*sigma^2)). "
                "Its probability density therefore has standard deviation sigma before finite-domain and grid effects.\n\n"
                "Smaller sigma gives a narrower packet and a broader "
                "momentum distribution. Resolve the width with multiple grid points."),
        "k0": ("Initial central wave number of the Gaussian packet.\n\n"
                "SI unit: inverse metre (1/m).\nIts ideal central momentum is p0 = hbar*k0.\n\n"
                "Positive k0 gives positive central momentum; negative k0 gives negative central momentum.\n"
                "k0 = 0 gives zero central momentum."),
    },
    "Plane Wave": {
        "n": ("Integer mode number of the plane wave. Positive, negative, and zero values are allowed.\n\n"
                "For domain length L = x_max - x_min:\nk = 2*pi*n/L and p = hbar*k.\n\n"
                "The sign determines the momentum direction. n = 0 gives a spatially constant wave.\n"
                "Use abs(n) well below N/2 to avoid grid aliasing."),
    },
    "Harmonic Oscillator Eigenstate": {
        "n": ("Energy-state index. A unitless integer greater than or equal to zero.\n\n"
                "n = 0 is the ground state; n = 1 is the first excited state.\n"
                "For the matching harmonic potential, E_n = hbar*omega*(n + 1/2).\n\n"
                "Higher states extend farther in position and require a sufficiently large, well-resolved domain."),
        "omega": ("Angular frequency used to construct the initial harmonic-oscillator eigenstate. Must be positive.\n\n"
                "SI unit: radians per second (rad/s).\nomega = 2*pi*f, where f is frequency in hertz.\n\n"
                "Match this value to the potential's omega to prepare an eigenstate of that potential.\n" 
                "Different values generally produce a changing probability distribution."),
    },
}


POTENTIAL_HELP = {
    "Free Particle": {},
    "Harmonic Oscillator": {
        "omega": ("Angular frequency of the harmonic potential V(x) = mass*omega**2*x**2 / 2, centered at x = 0.\n\n"
                "Use a positive value. SI unit: radians per second (rad/s).\nomega = 2*pi*f, where f is frequency in hertz.\n\n"
                "A larger omega gives a more strongly confining potential.")
    },
    "Barrier": {
        "height": ("Potential energy within the wall region; the potential is zero outside it.\n\n"
                    "SI unit: joule (J).\n"
                    "Note: 1 electronvolt = 1.602176634e-19 J.\n\n"
                    "A positive height creates a barrier. A negative height creates a finite potential well."),
        "x_left": ("Left edge of the rectangular potential region.\n\n"
                    "SI unit: metre (m). Must be less than x_right.\n"
                    "Place the region inside the computational domain and use enough grid points to resolve its width."),
        "x_right": ("Right edge of the rectangular potential region.\n\n"
                    "SI unit: metre (m). Must be greater than x_left.\n"
                    "The region's width is x_right - x_left."),
    },
    "Infinite Square Well": {
        "x_left": ("Left wall of the infinite square well.\n\n"
            "SI unit: metre (m).\nRequired: x_min < x_left < x_right < x_max.\n"
            "Both walls must align with grid points.\n\n"
            "The wave is zero at the walls and outside the well.\n"
            "SSF and the two-solver benchmark do not currently support this potential."
        ),
        "x_right": ("Right wall of the infinite square well.\n\n"
                    "SI unit: metre (m).\nRequired: x_min < x_left < x_right < x_max.\n"
                    "Both walls must align with grid points.\n\n"
                    "The well width is x_right - x_left.\nSSF and the two-solver benchmark do not currently support this potential."),
    },
}


SIMULATION_HELP = {
    "preset_mode": ("Construct the initial wave function using a predefined wave type and its parameter fields."),
    "expression_mode": ("Enter a mathematical expression for the initial wave amplitude psi(x, 0), instead of choosing a preset."),
    "expression": ("Enter the initial wave amplitude, not its probability density.\n\n"
                    "Variable: x.\n"
                    "Constants: pi, e, i, j. Both i and j represent sqrt(-1).\n"
                    "Functions: sin, cos, tan, exp, sqrt, abs.\n"
                    "Operators: +, -, *, /, ** and parentheses.\n\n"
                    "Example:\n"
                    "exp(-(x+2)**2/4)*exp(2*i*x)\n\n"
                    "Use ** for powers and explicit * for multiplication. "
                    "Do not use np. prefixes or undefined parameter names.\n"
                    "Values must be finite and the wave must have nonzero norm. "
                    "The initial wave is normalized automatically."),
    "wave_type": ("Choose the initial wave: Gaussian Packet, Plane Wave, or Harmonic Oscillator Eigenstate.\n\n"
                    "The fields below change to match the selected type. "
                    "The initial wave and the evolution potential are selected separately.\n"
                    "This section will be updated in the future as other wave types are implemented."),
    "potential_type": ("Choose the potential energy governing wave evolution.\n\n"
                        "Available types: Free Particle, Harmonic Oscillator, Barrier, and Infinite Square Well.\n"
                        "Infinite Square Well currently requires Crank-Nicolson.\n"
                        "This section will be updated in the future as other potential types are implemented."),
    "solver": ("Choose the numerical time-evolution method:\n"
                "Crank-Nicolson (CN) or Split-Step Fourier (SSF).\n\n"
                "Accuracy and runtime depend on the problem, N, and dt.\n"
                "Infinite Square Well currently supports CN only; the current SSF implementation uses periodic boundaries."),
    "configuration_name": ("Name used when saving the current Simulation settings.\n\n"
                            "A configuration stores inputs so they can be loaded again. It does not save calculated results; use Save Results for the simulation table."),
    "saved_configuration": ("Select a saved Simulation configuration, then click Load to fill the fields correspondingly.\n\n"
                            "Choose the folder-opening option to view the configuration storage location."),

    "boundary_condition": ("Choose the boundary condition for wave evolution.\n\n"
                        "Periodic: opposite domain edges are connected. A wave leaving one edge will re-enter through the other.\n\n"
                        "Dirichlet: the wave is fixed to zero at both domain boundaries. These boundaries reflect the wave; they do not absorb it. Initial endpoint values are set to zero.\n\n"
                        "For Infinite Square Well, zero-value boundaries are enforced at x_left and x_right inside the display domain.\n\n"
                        "The current SSF solver requires Periodic boundaries."),
}


BENCHMARK_HELP = {
    "N_values": ("Comma-separated spatial grid sizes for the entire run.\n\n"
                "Example: 500, 1000, 2000.\n"
                "Enter distinct integers without a trailing comma.\n\n"
                "Every problem is calculated for every N and dt combination using both solvers."),
    "dt_values": ("Comma-separated time steps for the entire run.\n\n"
                "SI unit: second (s).\n"
                "Example: 1e-17, 5e-18, 1e-18.\n"
                "Values must be distinct, finite, and positive.\n\n"
                "Each problem's T_final / dt must be a positive whole number for every listed dt."),
    "wave_type": ("Choose the initial wave type for the problem being edited.\n\n"
                "Set its parameters, give the problem a name, then click Add / Update to include those settings in the run."),
    "potential_type": ("Choose the potential for the problem being edited.\n\n"
                    "If no analytical reference is implemented for this combination, the run can proceed after confirmation, but L2 reference errors will be N/A.\n\n"
                    "Infinite Square Well is currently unavailable in Benchmark because the run compares both CN and SSF."
                    "Set its parameters, give the problem a name, then click Add / Update to include those settings in the run."),
    "problem_name": ("Name identifying a problem within this run.\n\n"
                    "Click Add / Update to store the current problem settings. Using an existing name asks whether to replace that problem.\n"
                    "Editing the form alone does not update a stored problem."),
    "problem_list": ("Problems currently included in this run.\n\n"
                    "Select an item and click Load selected into form to edit it, then click Add / Update to store the changes.\n"
                    "Select remove will remove it from the current run.\n\n"
                    "All listed problems use the run's shared N and dt lists."),
    "configuration_name": ("Name used to save the entire benchmark setup: all included problems and the shared N and dt lists.\n\n"
                        "Saving a configuration saves inputs, not calculated results."),
    "saved_configuration": ("Select a saved benchmark configuration and click Load to restore its problems and sweep settings.\n\n"
                        "Choose the folder-opening option to view the configuration storage location.\n"
                        "To inspect calculated results, open a saved run in Read Benchmark."),

    "boundary_condition": ("Periodic connects the two ends of the spatial domain.\n"
                        "Dirichlet fixes the wave function to zero at both ends.\n\n"
                        "The current benchmark compares CN and FFT-based SSF using periodic boundaries. FFT requires periodic boundary conditions, thus Dirichlet configuration is currently not supported in Benchmark."),
      
}

READ_BENCHMARK_HELP = {
    "open_run": ("Load a saved benchmark run for inspection.\n"
        "Select the run folder containing run.json.\n\n"
        "Completed and stopped runs can be inspected. Only completed combinations have results."),
    "open_folder": ("Open the loaded run's results folder in File Explorer."),
    "recover": ("Find unfinished benchmark runs retained by the application.\n\n"
        "You can inspect completed combinations, resume missing combinations, or delete recovery data."),
    "resume": ("Continue the loaded partial run by calculating missing problem/N/dt combinations.\n\n"
        "Completed combinations are reused. An interrupted combination is restarted rather than continued from its last time step."),
    "Problem": ("Choose a problem with completed results in this run."),
    "Quantity": ("Choose the quantity displayed in both the graph and table.\n\n"
                "Norm is the wave-function norm, not norm error.\n"
                "Position, momentum, and energy are expectation values.\n"
                "L2 error compares the numerical wave with an analytical reference; it is unavailable when no reference was used.\n\n"
                "Units follow the unit system used for the benchmark."),
    "N": ("Choose a completed spatial-grid size for this problem.\n"
        "N is the number of spatial grid points and has no unit."),
    "dt": ("Choose a completed time-step size for the selected problem and N.\n\n"
        "The unit is seconds when the benchmark uses SI units."),
    "previous": ("Display the previous page of table rows.\n"
        "Paging does not change the graph or saved results."),
    "next": ("Display the next page of table rows.\n"
        "Paging does not change the graph or saved results."),
}


RECOMMENDATION_HELP = {
    "open_run": ("Load a saved benchmark run and summarize its completed results.\n\n"
        "Recommendations use recorded results; no new simulations are performed."),
    "use_loaded": ("Analyze the run currently loaded in Read Benchmark."),
    "open_folder": ("Open the analyzed run's results folder in File Explorer."),
    "Problem": ("Choose the benchmark problem to evaluate.\n\n"
        "Recommendations compare tested solver/N/dt candidates for this problem."),
    "N": ("Restrict candidates to a particular tested grid size, "
        "or select Any tested value to consider all available sizes."),
    "dt": ("Restrict candidates to a particular tested time step, or select Any tested value to consider all available steps."),
    "l2": ("Enable this constraint to limit the maximum recorded L2 error over the simulation.\n\n"
            "Enter a finite, nonnegative tolerance, such as 1e-3.\n"
            "This compares the numerical wave with its analytical reference.\n"
            "Unavailable when the selected candidates lack reference errors.\n\n"
            "Unchecked constraints are ignored."),
    "norm": ("Enable this constraint to limit the maximum absolute change in wave-function norm from its initial value.\n\n"
            "Enter a finite, nonnegative tolerance, such as 1e-10.\n"
            "This is an absolute, unitless drift, not a percentage.\n\n"
            "Small norm drift alone does not guarantee an accurate wave.\n"
            "Unchecked constraints are ignored."),
    "energy": ("Enable this constraint to limit the maximum absolute change in expected energy from its initial value.\n\n"
                "Enter a finite, nonnegative tolerance in the benchmark's "
                "energy units: joules for SI calculations.\n"
                "This is absolute drift, not a relative error or percentage.\n\n"
                "Small energy drift alone does not guarantee an accurate wave.\n"
                "Unchecked constraints are ignored."),
    "find": ("Find the fastest recorded candidate satisfying all enabled constraints and the selected filters.\n\n"
            "Also show the best qualifying candidate for each solver.\n"
            "Results apply to the tested configurations and recorded runtimes; they do not predict untested configurations."),
    "reset": ("Clear and disable tolerance constraints and restore N and dt to Any tested value.\n"
        "Keep the currently selected problem."),
    "candidate_filter": ("Show all evaluated candidates, only qualifying candidates, or only rejected candidates.\n\n"
        "This changes the displayed table, not the recommendation criteria."),
}