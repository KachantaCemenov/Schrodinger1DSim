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
}