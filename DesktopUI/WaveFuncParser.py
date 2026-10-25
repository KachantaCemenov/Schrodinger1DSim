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
    #Convert to array if psi is a scalar
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

        raise ValueError("Only numeric constants are allowed")


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


    # Functions: exp(...), sin(...), etc
    if isinstance(node, ast.Call):

        if not isinstance(node.func, ast.Name):
            raise ValueError("Invalid function call")

        function_name = node.func.id

        if function_name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"Function '{function_name}' is not allowed")

        if node.keywords:raise ValueError("Keyword arguments are not allowed")

        arguments = [_EvaluateNode(arg, x) for arg in node.args]

        return ALLOWED_FUNCTIONS[function_name](*arguments)


    raise ValueError("Expression contains unrecognized syntax")