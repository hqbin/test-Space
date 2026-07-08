import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_swipe(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    direction = step.get("direction", "RIGHT")
    steps = step.get("steps", 10)
    x1 = step.get("x1", 0)
    y1 = step.get("y1", 0)
    x2 = step.get("x2", 0)
    y2 = step.get("y2", 0)
    if x1 or y1 or x2 or y2:
        device.shell(f"input swipe {x1} {y1} {x2} {y2} {steps}")
    else:
        w, h = device.get_display_size()
        dirs = {
            "UP": (w // 2, h * 3 // 4, w // 2, h // 4),
            "DOWN": (w // 2, h // 4, w // 2, h * 3 // 4),
            "LEFT": (w * 3 // 4, h // 2, w // 4, h // 2),
            "RIGHT": (w // 4, h // 2, w * 3 // 4, h // 2),
        }
        sx, sy, ex, ey = dirs.get(direction.upper(), (0, 0, 0, 0))
        device.shell(f"input swipe {sx} {sy} {ex} {ey} {steps}")
