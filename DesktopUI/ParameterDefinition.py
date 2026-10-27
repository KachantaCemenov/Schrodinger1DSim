WAVE_PARAMETERS = {
    "Gaussian Packet": {
        "x0": float,
        "sigma": float,
        "k0": float
    },

    "Plane Wave": {
        "n": int
    },

    "Harmonic Oscillator Eigenstate": {
        "n": int,
        "mass": float,
        "omega": float,
        "hbar": float
    }
}


POTENTIAL_PARAMETERS = {
    "Free Particle": {},

    "Harmonic Oscillator": {
        "mass": float,
        "omega": float
    },

    "Barrier": {
        "height": float,
        "x_left": float,
        "x_right": float
    }
}