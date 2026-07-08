import logging
from typing import Any

logger = logging.getLogger(__name__)


def handle_assert_focused(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    expected = step.get("target", {})
    focused = device.get_focused_element()
    if not focused:
        raise AssertionError("No element is currently focused")
    _check_match(focused, expected)


def handle_assert_app_foreground(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    package = step.get("package", "")
    if not package:
        raise ValueError("assert_app_foreground requires 'package' in step")
    if not device.is_app_foreground(package):
        current = device.get_current_activity()
        raise AssertionError(f"Expected app '{package}' in foreground, got activity: {current}")


def handle_assert_element(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    expected = step.get("target", {})
    tree = device.get_ui_tree()
    from tv_engine.core.locator import Locator
    locator = Locator(device)
    result = locator.locate(expected, ui_tree=tree)
    if not result or not result.found:
        raise AssertionError(f"Element not found: {expected}")


def _compute_phash(image):
    try:
        from PIL import Image
        import imagehash
        if isinstance(image, Image.Image):
            return str(imagehash.phash(image))
        return ""
    except ImportError:
        return ""


def handle_assert_visual(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    expected = step.get("target", {})
    similarity = step.get("similarity", 0.9)
    ref_path = step.get("ref_screenshot", "")
    screenshot = device.screenshot()

    from PIL import Image

    if ref_path:
        try:
            ref_img = Image.open(ref_path).convert("RGB")
            cur_img = screenshot.convert("RGB")
            if ref_img.size != cur_img.size:
                cur_img = cur_img.resize(ref_img.size, Image.LANCZOS)
            import numpy as np
            arr_ref = np.array(ref_img, dtype=np.float32)
            arr_cur = np.array(cur_img, dtype=np.float32)
            mse = np.mean((arr_ref - arr_cur) ** 2)
            actual_similarity = max(0, min(1, 1.0 - (mse / (255.0**2))))
            if actual_similarity < similarity:
                raise AssertionError(
                    f"Visual similarity {actual_similarity:.3f} below threshold {similarity} "
                    f"(MSE={mse:.1f})"
                )
            return
        except ImportError:
            pass
        except Exception as exc:
            raise AssertionError(f"Visual comparison with ref failed: {exc}")

    from tv_engine.core.locator import Locator
    locator = Locator(device)
    result = locator.locate(expected)
    if not result or not result.found:
        region = step.get("region", "")
        value = step.get("value", "")
        if region and value:
            w, h = screenshot.size
            ratio_map = {"top_20_percent": (0, 0, w, int(h * 0.2))}
            box = ratio_map.get(region, (0, 0, w, h))
            cropped = screenshot.crop(box)
            import numpy as np
            arr = np.array(cropped.convert("L"))
            found_any = False
            for y in range(0, arr.shape[0], 10):
                for x in range(0, arr.shape[1], 10):
                    block = arr[y:y+10, x:x+10]
                    if block.mean() > 200:
                        found_any = True
                        break
                if found_any:
                    break
            if not found_any:
                raise AssertionError(f"Region '{region}' appears empty or does not contain expected content")
            return
        raise AssertionError(f"Visual element not found: {expected}")
    step_id = step.get("id", "")
    if step.get("screenshot", False):
        from pathlib import Path
        run_id = context.get("run_id", "unknown")
        report_dir = context.get("report_dir", "reports")
        shot_dir = Path(report_dir) / run_id / "screenshots"
        shot_dir.mkdir(parents=True, exist_ok=True)
        path = str(shot_dir / f"{step_id}.png")
        screenshot.save(path)
        context[f"_screenshot_{step_id}"] = path


def handle_assert_shell(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    command = step.get("command", "")
    if not command:
        raise ValueError("assert_shell requires 'command'")
    expected_contains = step.get("expected_output_contains", "")
    output = device.shell(command)
    if expected_contains and expected_contains not in output:
        raise AssertionError(f"Shell output does not contain '{expected_contains}'. Output: {output[:500]}")


def _check_match(actual: dict, expected: dict) -> None:
    for key in ("resource_id", "content_desc", "text", "class_name"):
        val = expected.get(key)
        if val is not None:
            actual_val = actual.get(key, "")
            if actual_val != val:
                raise AssertionError(
                    f"Expected {key}='{val}', got '{actual_val}'"
                )
