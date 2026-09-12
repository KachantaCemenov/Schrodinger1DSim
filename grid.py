import numpy as np

class Grid1D:
    def __init__(self, x_min, x_max, num_points):
        self.x_min = x_min
        self.x_max = x_max
        self.N = num_points

        # 1D grid of N points between x_min and x_max 
        self.x = np.linspace(
            x_min,
            x_max,
            num_points
        )

        self.dx = self.x[1] - self.x[0]