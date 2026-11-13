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
        "k0": "TODO: Explain the initial wave number and units.",
    },
    "Plane Wave": {
        "n": "TODO: Explain the plane-wave mode number and allowed values.",
    },
    "Harmonic Oscillator Eigenstate": {
        "n": "TODO: Explain the energy-state index and allowed values.",
        "omega": "TODO: Explain the wave state's angular frequency and units.",
    },
}


POTENTIAL_HELP = {
    "Free Particle": {},
    "Harmonic Oscillator": {
        "omega": "TODO: Explain the potential's angular frequency and units.",
    },
    "Barrier": {
        "height": "TODO: Explain barrier height and energy units.",
        "x_left": "TODO: Explain the barrier's left edge and units.",
        "x_right": "TODO: Explain the barrier's right edge and units.",
    },
    "Infinite Square Well": {
        "x_left": "TODO: Explain the well's left wall and units.",
        "x_right": "TODO: Explain the well's right wall and units.",
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