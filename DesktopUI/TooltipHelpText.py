NUMERICAL_HELP = {
    "mass": "TODO: Explain particle mass, units, and allowed values.",
    "hbar": "TODO: Explain reduced Planck constant and units.",
    "x_min": "TODO: Explain the left spatial boundary and units.",
    "x_max": "TODO: Explain the right spatial boundary and units.",
    "N": "TODO: Explain spatial grid size and its effect.",
    "dt": "TODO: Explain time-step size, units, and its effect.",
    "T_final": "TODO: Explain total simulation time and units.",
}


WAVE_HELP = {
    "Gaussian Packet": {
        "x0": "TODO: Explain the initial packet center and units.",
        "sigma": "TODO: Explain the packet width convention and units.",
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