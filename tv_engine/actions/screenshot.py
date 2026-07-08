import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def handle_screenshot(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    step_id = step.get("id", "screenshot")
    run_id = context.get("run_id", "unknown")
    report_dir = context.get("report_dir", "reports")
    screenshot_dir = Path(report_dir) / run_id / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    img = device.screenshot()
    path = str(screenshot_dir / f"{step_id}.png")
    img.save(path)
    context[f"_screenshot_{step_id}"] = path
