import numpy as np

class Grid1D:
    def __init__(self, x_min, x_max, num_points, periodic = True):
        self.x_min = x_min
        self.x_max = x_max
        self.N = num_points
        self.periodic = periodic

        # 1D grid of N points between x_min and x_max 
        self.x = np.linspace(
            x_min,
            x_max,
            num_points,
            endpoint = not periodic
        )

        self.dx = self.x[1] - self.x[0] # linspace makes uniform spacing, so dx is constant