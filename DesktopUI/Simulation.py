from dataclasses import dataclass
from grid import Grid1D

@dataclass
class SimulationConfig:

    mass: float
    hbar: float

    x_min: float
    x_max: float

    N: int

    dt: float
    T_final: float

    solver: str

    wave_mode: str
    wave_type: str
    wave_parameters: dict

    potential_type: str
    potential_parameters: dict

    wave_expression: str | None = None


def BuildGrid(config):
    return Grid1D(
    x_min = config.x_min,
    x_max = config.x_max,
    num_points = config.N
    )


def BuildWaveFunction(config, grid):
    return None


def BuildPotential(config, grid):
    return None