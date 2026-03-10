"""
HealthOps Studio -- Data Transformer (SAFE)

Applies user-defined transformations to data records.
Used by the ETL pipeline when processing workflow nodes.

SECURITY FIX: The original used eval() which allows arbitrary code execution.
Now uses ast.literal_eval for safe expression evaluation, supporting only:
- Arithmetic: +, -, *, /
- Field references from the data record
- String concatenation
- Literals (numbers, strings)
"""

import ast
import operator

# Allowed operations for safe expression evaluation
SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
}


def _safe_eval(expression: str, variables: dict):
    """
    Safely evaluate a simple math/string expression.

    Supports:
        age + 1
        height_cm * 2.54
        name + ' (verified)'
        age * 2 + 10

    Does NOT support:
        __import__('os').system('rm -rf /')  (blocked!)
        open('/etc/passwd').read()           (blocked!)
    """
    try:
        tree = ast.parse(expression, mode='eval')
        return _eval_node(tree.body, variables)
    except Exception:
        return None


def _eval_node(node, variables: dict):
    """Recursively evaluate AST nodes safely."""
    if isinstance(node, ast.Constant):
        # Literal values: 42, "hello", 3.14
        return node.value

    elif isinstance(node, ast.Name):
        # Variable references: age, name, height_cm
        if node.id in variables:
            return variables[node.id]
        raise ValueError(f"Unknown variable: {node.id}")

    elif isinstance(node, ast.BinOp):
        # Binary operations: a + b, x * y
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        op_func = SAFE_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
        return op_func(left, right)

    elif isinstance(node, ast.UnaryOp):
        # Unary operations: -x
        operand = _eval_node(node.operand, variables)
        op_func = SAFE_OPS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
        return op_func(operand)

    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def apply_transformations(data: dict, operations: list) -> dict:
    """Apply a list of transformation operations to a data record."""
    result = data.copy()

    for op in operations:
        op_type = op["type"]

        if op_type == "filter":
            field = op["field"]
            op_operator = op["operator"]
            value = op["value"]

            if field not in result:
                return {}

            if not _apply_filter(result[field], op_operator, value):
                return {}

        elif op_type == "rename":
            old = op["from"]
            new = op["to"]
            if old in result:
                result[new] = result.pop(old)

        elif op_type == "map":
            field = op["field"]
            expression = op["expression"]
            # SAFE: uses AST-based evaluation instead of eval()
            result[field] = _safe_eval(expression, result)

    return result


def _apply_filter(value, op_operator, target):
    if op_operator == ">":
        return value > target
    if op_operator == "<":
        return value < target
    if op_operator == "==":
        return value == target
    if op_operator == "!=":
        return value != target
    if op_operator == ">=":
        return value >= target
    if op_operator == "<=":
        return value <= target
    return False
