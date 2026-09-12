import numpy as np

"""
Make a potential class that contains a grid and a potential array.
The potential array is initialized by some functions based on specifics of the problem.
"""

class Potential:
    def __init__(self, grid, potential_array):
        self.grid = grid
        self.V = np.asarray(potential_array, float)
        
    


    @classmethod
    def free_particle(cls, grid):
        """
        V(x) = 0
        """
        values = np.zeros_like(grid.x)

        return cls(grid, values)

    @classmethod
    def harmonic_oscillator(cls, grid, mass=1.0, omega=1.0):
        """
        V(x) = 1/2 m omega^2 x^2
        """
        x = grid.x

        values = 0.5 * mass * omega**2 * x**2

        return cls(grid, values)

    @classmethod
    def barrier(cls, grid, height, x_left, x_right):
        """
        Rectangular potential barrier with customizable height
        """

        values = np.zeros_like(grid.x)

        wall = (
            (grid.x >= x_left)
            & (grid.x <= x_right)
        )

        values[wall] = height

        return cls(grid, values)