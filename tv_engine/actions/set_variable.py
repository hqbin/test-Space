from typing import Any


def handle_set_variable(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    var_name = step.get("name", "")
    var_value = step.get("value", "")
    if not var_name:
        raise ValueError("set_variable requires 'name'")
    context[var_name] = var_value
