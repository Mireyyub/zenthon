"""Math helpers adapted from AgilBot math_engine (safe subset)."""
from __future__ import annotations

import ast
import operator
from typing import List, Union

Number = Union[int, float]


def safe_eval_math(expr: str) -> Number:
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op = ops.get(type(node.op))
            if not op:
                raise ValueError("unsupported operator")
            return op(_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_eval(node.operand)
        raise ValueError("unsupported expression")

    tree = ast.parse(expr.strip(), mode="eval")
    return _eval(tree.body)


def matrix_add(a: List[List[Number]], b: List[List[Number]]) -> List[List[Number]]:
    if not a or not b or len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError("matrix dimensions must match")
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]
