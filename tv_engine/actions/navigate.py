import logging
from typing import Any

from tv_engine.core.navigator import Navigator

logger = logging.getLogger(__name__)


def handle_navigate_to(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    target = step.get("target", {})
    max_steps = step.get("max_steps", 25)
    navigator = Navigator(device)
    nav_result = navigator.navigate_to(target, max_steps=max_steps, timeout_ms=timeout)
    if not nav_result.success:
        raise RuntimeError(
            f"Navigation to target failed after {nav_result.steps_taken} steps: "
            f"{nav_result.error}"
        )
    context.setdefault("_navigator", navigator)
    context["_locator_used"] = getattr(nav_result, "path_used", [])
