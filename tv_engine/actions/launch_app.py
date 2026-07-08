import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_launch_app(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    package = step.get("package", "")
    if not package:
        raise ValueError("launch_app requires 'package'")
    activity = step.get("wait_activity", "")
    device.start_app(package, activity)
    wait_ms = step.get("timeout", timeout)
    if activity:
        if not device.wait_for_activity(activity, wait_ms):
            raise TimeoutError(f"Activity '{activity}' not reached within {wait_ms}ms")
    device.wait_stable(wait_ms)
