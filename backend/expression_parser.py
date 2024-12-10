from typing import Dict, Any


def get_value(expression: str, context: Dict[str, Any]) -> Any:
    if expression.startswith("attr:"):
        key = expression.split(":", 1)[1].strip()
        return context.get(key, None)
    return expression


def evaluate_expression(expression: Dict[str, Any], context: Dict[str, Any]) -> bool:
    if "eq" in expression:
        return get_value(expression["eq"][0], context) == get_value(expression["eq"][1], context)
    elif "ne" in expression:
        return get_value(expression["ne"][0], context) != get_value(expression["ne"][1], context)
    elif "le" in expression:
        return get_value(expression["le"][0], context) <= get_value(expression["le"][1], context)
    elif "lt" in expression:
        return get_value(expression["lt"][0], context) < get_value(expression["lt"][1], context)
    elif "ge" in expression:
        return get_value(expression["ge"][0], context) >= get_value(expression["ge"][1], context)
    elif "gt" in expression:
        return get_value(expression["gt"][0], context) > get_value(expression["gt"][1], context)
    elif "in" in expression:
        return get_value(expression["in"][1], context) in get_value(expression["in"][0], context)
    elif "and" in expression:
        return all(evaluate_expression(sub_exp, context) for sub_exp in expression["and"])
    elif "or" in expression:
        return any(evaluate_expression(sub_exp, context) for sub_exp in expression["or"])
    elif "not" in expression:
        return not evaluate_expression(expression["not"], context)
    else:
        raise ValueError(f"Unsupported expression: {expression}")
