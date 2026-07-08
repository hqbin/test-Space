import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_press_key(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    key = step.get("key", "DPAD_CENTER")
    wait_after = step.get("wait_after", 0)
    device.press_key(key)
    if wait_after:
        device.wait_stable(wait_after)


def handle_press_key_sequence(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    keys = step.get("keys", [])
    wait_after = step.get("wait_after", 0)
    for k in keys:
        device.press_key(k)
    if wait_after:
        device.wait_stable(wait_after)
