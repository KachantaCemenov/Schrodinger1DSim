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
        "omega": float
    }
}


POTENTIAL_PARAMETERS = {
    "Free Particle": {},

    "Harmonic Oscillator": {
        "omega": float
    },

    "Barrier": {
        "height": float,
        "x_left": float,
        "x_right": float
    }
}