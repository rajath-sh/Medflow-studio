def apply_transformations(data: dict, operations: list) -> dict:
    """
    Apply a list of transformations to the input data.
    """

    result = data.copy()

    for op in operations:
        op_type = op["type"]

        if op_type == "filter":
            field = op["field"]
            operator = op["operator"]
            value = op["value"]

            if field not in result:
                return {}

            if not _apply_filter(result[field], operator, value):
                return {}

        elif op_type == "rename":
            old = op["from"]
            new = op["to"]

            if old in result:
                result[new] = result.pop(old)

        elif op_type == "map":
            field = op["field"]
            expression = op["expression"]

            try:
                result[field] = eval(expression, {}, result)
            except Exception:
                result[field] = None

    return result


def _apply_filter(value, operator, target):
    if operator == ">":
        return value > target
    if operator == "<":
        return value < target
    if operator == "==":
        return value == target
    if operator == "!=":
        return value != target
    if operator == ">=":
        return value >= target
    if operator == "<=":
        return value <= target
    return False
