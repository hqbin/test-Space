import difflib
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Optional

from PIL import Image

from tv_engine.core.device import DeviceController

logger = logging.getLogger(__name__)


@dataclass
class LocatorResult:
    found: bool
    element: Optional[dict[str, Any]] = None
    fallback_used: Optional[str] = None
    strategy: Optional[str] = None


_FALLBACK_ORDER = ["primary", "fallback1", "fallback2", "fallback3"]


class Locator:
    def __init__(self, device: DeviceController) -> None:
        self._device = device

    def locate(self, target: dict[str, Any], ui_tree: Optional[ET.Element] = None) -> LocatorResult:
        if ui_tree is None:
            try:
                ui_tree = self._device.get_ui_tree()
            except Exception as exc:
                logger.error("Failed to get UI tree: %s", exc)
                return LocatorResult(found=False)

        for fb_name in _FALLBACK_ORDER:
            strategy_def = target.get(fb_name)
            if strategy_def is None:
                continue
            by = strategy_def.get("by", "")
            value = strategy_def.get("value", "")
            if not by or not value:
                continue
            try:
                result = self.locate_by(ui_tree, by, value)
                if result is not None:
                    return LocatorResult(
                        found=True,
                        element=result,
                        fallback_used=fb_name,
                        strategy=by,
                    )
            except Exception as exc:
                logger.warning("Locator strategy '%s' (by=%s) failed: %s", fb_name, by, exc)

        return LocatorResult(found=False)

    def locate_by(self, ui_tree: ET.Element, by: str, value: str) -> Optional[dict[str, Any]]:
        strategy_map = {
            "resource_id": self.locate_resource_id,
            "content_desc": self.locate_content_desc,
            "text": self.locate_text,
            "text_contains": self.locate_text_contains,
            "class_name": self.locate_class_name,
            "index": self.locate_by_index,
            "class_and_index": self.locate_by_class_and_index,
            "visual_match": self.locate_visual_match,
        }
        locator_fn = strategy_map.get(by)
        if locator_fn is None:
            logger.warning("Unknown locator strategy: %s", by)
            return None
        return locator_fn(ui_tree, value)

    def locate_resource_id(self, tree: ET.Element, rid: str) -> Optional[dict[str, Any]]:
        def _walk(node: ET.Element) -> Optional[dict[str, Any]]:
            if node.attrib.get("resource-id", "") == rid:
                return self._element_to_dict(node)
            for child in node:
                result = _walk(child)
                if result is not None:
                    return result
            return None

        return _walk(tree)

    def locate_content_desc(self, tree: ET.Element, desc: str) -> Optional[dict[str, Any]]:
        def _walk(node: ET.Element) -> Optional[dict[str, Any]]:
            if node.attrib.get("content-desc", "") == desc:
                return self._element_to_dict(node)
            for child in node:
                result = _walk(child)
                if result is not None:
                    return result
            return None

        return _walk(tree)

    def locate_text(self, tree: ET.Element, text: str) -> Optional[dict[str, Any]]:
        def _walk(node: ET.Element) -> Optional[dict[str, Any]]:
            if node.attrib.get("text", "") == text:
                return self._element_to_dict(node)
            for child in node:
                result = _walk(child)
                if result is not None:
                    return result
            return None

        return _walk(tree)

    def locate_text_contains(self, tree: ET.Element, text: str) -> Optional[dict[str, Any]]:
        text_lower = text.lower()

        def _walk(node: ET.Element) -> Optional[dict[str, Any]]:
            node_text = node.attrib.get("text", "").lower()
            node_desc = node.attrib.get("content-desc", "").lower()
            if text_lower in node_text or text_lower in node_desc:
                return self._element_to_dict(node)
            for child in node:
                result = _walk(child)
                if result is not None:
                    return result
            return None

        return _walk(tree)

    def locate_class_name(self, tree: ET.Element, class_name: str) -> Optional[dict[str, Any]]:
        def _walk(node: ET.Element) -> Optional[dict[str, Any]]:
            if node.attrib.get("class", "") == class_name:
                return self._element_to_dict(node)
            for child in node:
                result = _walk(child)
                if result is not None:
                    return result
            return None

        return _walk(tree)

    def locate_visual_match(self, tree: ET.Element, template_path: str) -> Optional[dict[str, Any]]:
        _ = tree
        threshold: float = 0.9
        parts = template_path.rsplit(":", 1)
        if len(parts) == 2:
            try:
                threshold = float(parts[1])
            except ValueError:
                pass
            template_path = parts[0]
        try:
            template = Image.open(template_path).convert("RGB")
        except Exception as exc:
            logger.error("Cannot open template image %s: %s", template_path, exc)
            return None
        try:
            screenshot = self._device.screenshot()
        except Exception as exc:
            logger.error("Failed to take screenshot for visual match: %s", exc)
            return None
        if screenshot.width < template.width or screenshot.height < template.height:
            logger.warning("Template %dx%d larger than screenshot %dx%d", template.width, template.height, screenshot.width, screenshot.height)
            return None
        try:
            import numpy as np
            from numpy.lib.stride_tricks import sliding_window_view

            screen_arr = np.array(screenshot)
            template_arr = np.array(template)
            if screen_arr.ndim == 3:
                s_gray = np.mean(screen_arr, axis=2).astype(np.uint8)
                t_gray = np.mean(template_arr, axis=2).astype(np.uint8)
            else:
                s_gray = screen_arr
                t_gray = template_arr
            th, tw = t_gray.shape
            windows = sliding_window_view(s_gray, (th, tw))
            corr = np.sum(windows * t_gray, axis=(-2, -1)) / (
                np.sqrt(np.sum(windows**2, axis=(-2, -1))) * np.sqrt(np.sum(t_gray**2)) + 1e-8
            )
            max_corr = float(np.max(corr))
            if max_corr >= threshold:
                match_pos = np.unravel_index(np.argmax(corr), corr.shape)
                return {
                    "match_x": int(match_pos[1]),
                    "match_y": int(match_pos[0]),
                    "match_width": tw,
                    "match_height": th,
                    "match_confidence": max_corr,
                    "resource_id": "",
                    "content_desc": "",
                    "text": "",
                    "class_name": "",
                    "focused": False,
                    "focusable": False,
                    "bounds_left": int(match_pos[1]),
                    "bounds_top": int(match_pos[0]),
                    "bounds_right": int(match_pos[1]) + tw,
                    "bounds_bottom": int(match_pos[0]) + th,
                    "bounds_width": tw,
                    "bounds_height": th,
                    "children": [],
                }
        except ImportError:
            logger.warning("numpy not available; visual matching requires numpy")
        except Exception as exc:
            logger.warning("Visual matching failed: %s", exc)
        return None

    def locate_by_index(self, tree: ET.Element, value: str) -> Optional[dict[str, Any]]:
        parts = value.rsplit(":", 1)
        index_str = parts[0]
        parent_id = parts[1] if len(parts) > 1 else ""

        try:
            idx = int(index_str)
        except (ValueError, TypeError):
            logger.warning("Invalid index value: %s", index_str)
            return None

        def _collect_focusable(node: ET.Element, parent_rid: str = "") -> list[dict[str, Any]]:
            results: list[dict[str, Any]] = []
            current_rid = node.attrib.get("resource-id", "") or parent_rid
            if not parent_id or current_rid == parent_id:
                if node.attrib.get("focusable", "false") == "true" or node.attrib.get("clickable", "false") == "true":
                    results.append(self._element_to_dict(node))
            for child in node:
                results.extend(_collect_focusable(child, current_rid))
            return results

        elements = _collect_focusable(tree)
        if 0 <= idx < len(elements):
            return elements[idx]
        return None

    def locate_by_class_and_index(self, tree: ET.Element, value: str) -> Optional[dict[str, Any]]:
        parts = value.rsplit(":", 1)
        if len(parts) != 2:
            logger.warning("class_and_index value must be 'class_name:index', got: %s", value)
            return None
        class_name, index_str = parts
        try:
            idx = int(index_str)
        except (ValueError, TypeError):
            logger.warning("Invalid index in class_and_index: %s", index_str)
            return None

        def _count_by_class(node: ET.Element, target_class: str) -> list[dict[str, Any]]:
            results: list[dict[str, Any]] = []
            if node.attrib.get("class", "") == target_class:
                results.append(self._element_to_dict(node))
            for child in node:
                results.extend(_count_by_class(child, target_class))
            return results

        matches = _count_by_class(tree, class_name)
        if 0 <= idx < len(matches):
            return matches[idx]
        return None

    def semantic_match(self, elements: list[dict[str, Any]], target: dict[str, Any]) -> Optional[dict[str, Any]]:
        target_id = target.get("resource_id", "").lower()
        target_desc = target.get("content_desc", "").lower()
        target_text = target.get("text", "").lower()

        best_score: float = 0.0
        best_element: Optional[dict[str, Any]] = None

        for elem in elements:
            score = 0.0
            rid = elem.get("resource_id", "").lower()
            desc = elem.get("content_desc", "").lower()
            text = elem.get("text", "").lower()

            if target_id and rid:
                if target_id == rid:
                    score += 3.0
                elif target_id in rid or rid in target_id:
                    score += 1.5
                else:
                    ratio = difflib.SequenceMatcher(None, target_id, rid).ratio()
                    score += ratio * 2.0

            if target_desc and desc:
                if target_desc == desc:
                    score += 2.0
                elif target_desc in desc or desc in target_desc:
                    score += 1.0
                else:
                    ratio = difflib.SequenceMatcher(None, target_desc, desc).ratio()
                    score += ratio * 1.5

            if target_text and text:
                if target_text == text:
                    score += 2.0
                elif target_text in text or text in target_text:
                    score += 1.0
                else:
                    ratio = difflib.SequenceMatcher(None, target_text, text).ratio()
                    score += ratio * 1.5

            if score > best_score:
                best_score = score
                best_element = elem

        if best_element and best_score > 0.5:
            return best_element
        return None

    @staticmethod
    def _element_to_dict(node: ET.Element) -> dict[str, Any]:
        attrib = node.attrib
        bounds_str = attrib.get("bounds", "")
        bounds = (0, 0, 0, 0)
        if bounds_str:
            try:
                parts = bounds_str.replace("[", "").replace("]", ",").split(",")
                if len(parts) >= 4:
                    bounds = (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
            except (ValueError, IndexError):
                pass
        return {
            "resource_id": attrib.get("resource-id", ""),
            "content_desc": attrib.get("content-desc", ""),
            "text": attrib.get("text", ""),
            "class_name": attrib.get("class", ""),
            "package": attrib.get("package", ""),
            "focused": attrib.get("focused", "false") == "true",
            "focusable": attrib.get("focusable", "false") == "true",
            "selected": attrib.get("selected", "false") == "true",
            "checkable": attrib.get("checkable", "false") == "true",
            "checked": attrib.get("checked", "false") == "true",
            "clickable": attrib.get("clickable", "false") == "true",
            "enabled": attrib.get("enabled", "true") == "true",
            "long_clickable": attrib.get("long-clickable", "false") == "true",
            "scrollable": attrib.get("scrollable", "false") == "true",
            "index": int(attrib.get("index", "0")),
            "bounds_left": bounds[0],
            "bounds_top": bounds[1],
            "bounds_right": bounds[2],
            "bounds_bottom": bounds[3],
            "bounds_width": bounds[2] - bounds[0],
            "bounds_height": bounds[3] - bounds[1],
            "children": [],
        }
