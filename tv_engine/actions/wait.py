from typing import Any
import time as _time
from tv_engine.core.locator import Locator


def handle_wait_for(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    wait_ms = step.get("timeout", timeout)
    if not device.wait_stable(wait_ms):
        raise TimeoutError(f"wait_for timed out after {wait_ms}ms")
    condition = step.get("condition", {})
    cond_type = condition.get("type", "")
    if cond_type == "element_exists":
        cond_target = condition.get("target", {})
        if cond_target:
            locator = Locator(device)
            tree = device.get_ui_tree()
            result = locator.locate(cond_target, ui_tree=tree)
            if not result or not result.found:
                raise AssertionError(f"Condition element not found: {cond_target}")
    elif cond_type == "activity_is":
        expected = condition.get("activity", "")
        current = device.get_current_activity()
        if expected not in current:
            raise AssertionError(f"Expected activity '{expected}', got '{current}'")
    elif cond_type == "no_loading":
        deadline = _time.time() + (wait_ms / 1000.0)
        while _time.time() < deadline:
            tree = device.get_ui_tree()
            loading_keywords = ("loading", "progress", "spinner", "缓冲", "加载")
            elements = tree.get("elements", [])
            has_loading = False
            for el in elements:
                text = str(el.get("text", "")).lower()
                desc = str(el.get("content_desc", "")).lower()
                if any(kw in text or kw in desc for kw in loading_keywords):
                    has_loading = True
                    break
            if not has_loading:
                return
            _time.sleep(0.3)
        raise TimeoutError(f"Loading did not complete within {wait_ms}ms")


def handle_wait_stable(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    wait_ms = step.get("timeout", timeout)
    if not device.wait_stable(wait_ms):
        raise TimeoutError(f"wait_stable timed out after {wait_ms}ms")


def handle_wait_then_assert(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    import time
    wait_seconds = step.get("wait_seconds", 0)
    time.sleep(wait_seconds)
    device.wait_stable(1000)
    assert_data = step.get("assert", {})
    assert_type = assert_data.get("type", "element_exists")
    assert_target = assert_data.get("target", {})
    if assert_type == "element_exists":
        locator = Locator(device)
        tree = device.get_ui_tree()
        result = locator.locate(assert_target, ui_tree=tree)
        if not result or not result.found:
            raise AssertionError(f"After wait {wait_seconds}s, element not found: {assert_target}")
    elif assert_type == "activity_is":
        expected = assert_data.get("activity", "")
        current = device.get_current_activity()
        if expected not in current:
            raise AssertionError(f"After wait {wait_seconds}s, expected activity '{expected}', got '{current}'")
