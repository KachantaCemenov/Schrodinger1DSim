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
    "preset_mode": "TODO: Explain choosing a predefined wave function.",
    "expression_mode": "TODO: Explain entering a custom wave function.",
    "expression": (
        "TODO: Explain the expression syntax.\n\n"
        "TODO: List supported variables, functions, and an example."
    ),
    "wave_type": "TODO: Explain the available initial wave types.",
    "potential_type": "TODO: Explain the available potential types.",
    "solver": "TODO: Explain solver selection and compatibility restrictions.",
    "configuration_name": "TODO: Explain naming and saving a configuration.",
    "saved_configuration": (
        "TODO: Explain selecting a saved configuration and opening its folder."
    ),
}


BENCHMARK_HELP = {
    "N_values": "TODO: Explain the comma-separated list of spatial grid sizes.",
    "dt_values": "TODO: Explain the comma-separated list of time steps.",
    "wave_type": "TODO: Explain choosing the current benchmark problem's wave.",
    "potential_type": "TODO: Explain choosing the current problem's potential.",
    "problem_name": "TODO: Explain naming a problem and updating an existing one.",
    "problem_list": "TODO: Explain selecting, loading, and removing run problems.",
    "configuration_name": "TODO: Explain naming a configuration for an entire run.",
    "saved_configuration": (
        "TODO: Explain loading a saved run configuration and opening its folder."
    ),
}