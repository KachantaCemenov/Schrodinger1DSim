# DesktopUI/WaveFunctionParser.py

import ast
import numpy as np

from wavefunction import WaveFunction


ALLOWED_FUNCTIONS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "sqrt": np.sqrt,
    "abs": np.abs
}

ALLOWED_CONSTANTS = {
    "pi": np.pi,
    "e": np.e,
    "i": 1j,
    "j": 1j
}


def ParseWaveFunction(expression: str, grid):

    #https://docs.python.org/3/library/ast.html
    tree = ast.parse(expression, mode="eval")

    psi = _EvaluateNode(tree.body, grid.x)

    psi = np.asarray(psi, dtype=complex)

    #Checking for some special cases
    #If psi ended up a scalar, convert that into array
    if psi.ndim == 0:
        psi = np.full(len(grid.x),psi,dtype=complex)

    if psi.shape != grid.x.shape:
        raise ValueError("Expression did not produce one value for every point on the grid")

    if not np.all(np.isfinite(psi)):
        raise ValueError("Wave function somehow contains infinite (?) values")

    wave = WaveFunction(grid, psi)

    if wave.Norm() == 0:
        raise ValueError("Wave function cannot have zero norm.")

    wave.Normalize()

    return wave




# LOOK UP: https://docs.python.org/3/library/ast.html
def _EvaluateNode(node, x):

    # Numbers: 2, 3.5, 1j etc
    if isinstance(node, ast.Constant):

        if isinstance(node.value, (int, float, complex)):
            return node.value

        raise ValueError("Only numeric (int/float/complex) constants are allowed")


    # Chara: x, pi, e, i, j
    if isinstance(node, ast.Name):

        if node.id == "x":
            return x

        if node.id in ALLOWED_CONSTANTS:
            return ALLOWED_CONSTANTS[node.id]

        raise ValueError(f"Unknown variable: {node.id}")


    # +, -, *, /, **
    if isinstance(node, ast.BinOp):

        left = _EvaluateNode(node.left, x)

        right = _EvaluateNode(node.right, x)

        if isinstance(node.op, ast.Add):
            return left + right

        if isinstance(node.op, ast.Sub):
            return left - right

        if isinstance(node.op, ast.Mult):
            return left * right

        if isinstance(node.op, ast.Div):
            return left / right

        if isinstance(node.op, ast.Pow):
            return left ** right

        raise ValueError("Operator not allowed")


    # Unary + and -
    if isinstance(node, ast.UnaryOp):

        value = _EvaluateNode(node.operand, x)

        if isinstance(node.op, ast.USub):
            return -value

        if isinstance(node.op, ast.UAdd):
            return value

        raise ValueError("Unary operator not allowed")


    # Functions: exp, sin etc
    if isinstance(node, ast.Call):

        if not isinstance(node.func, ast.Name):
            raise ValueError("Invalid function call")

        function_name = node.func.id

        if function_name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"Function '{function_name}' is not allowed")

        if node.keywords:raise ValueError("Keyword arguments are not allowed")

        arguments = [_EvaluateNode(arg, x) for arg in node.args]

        return ALLOWED_FUNCTIONS[function_name](*arguments)


    raise ValueError("Unrecognized syntax(es) in expression")



if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from grid import Grid1D

    grid = Grid1D(
        x_min=-10,
        x_max=10,
        num_points=1000
    )

    # Gaussian wave packet with momentum
    expression = "exp(-(x+2)**2/(4*1**2))" #"sin(x)"

    wave = ParseWaveFunction(expression, grid)

    print("Norm:", wave.Norm())
    print("Expected x:", wave.Expectation_x())
    print("Wave function shape:", wave.psi.shape)

    assert np.isclose(wave.Norm(), 1.0)
    assert wave.psi.shape == grid.x.shape

    plt.plot(grid.x, wave.ProbabilityDensity())
    plt.xlabel("x")
    plt.ylabel("|ψ(x)|²")
    plt.title("Parsed Wave Function")
    plt.grid()
    plt.show()

    # Test invalid iunput
    invalid_expressions = [
        "unknown_variable",
        "eval('2+2')",
        "0*x"
    ]

    for expr in invalid_expressions:
        try:
            ParseWaveFunction(expr, grid)
            print("PASS:", expr)
        except (ValueError, SyntaxError) as error:
            print("FAIL:", expr, "-", error)
