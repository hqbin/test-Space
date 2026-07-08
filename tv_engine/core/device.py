import io
import logging
import subprocess
import time
import xml.etree.ElementTree as ET
from typing import Any, Optional

from PIL import Image

try:
    import uiautomator2 as u2

    _HAS_U2 = True
except ImportError:
    _HAS_U2 = False

logger = logging.getLogger(__name__)

KEYCODE_MAP: dict[str, int] = {
    "DPAD_UP": 19,
    "DPAD_DOWN": 20,
    "DPAD_LEFT": 21,
    "DPAD_RIGHT": 22,
    "DPAD_CENTER": 23,
    "DPAD_OK": 23,
    "BACK": 4,
    "HOME": 3,
    "MENU": 82,
    "VOLUME_UP": 24,
    "VOLUME_DOWN": 25,
    "POWER": 26,
    "ENTER": 66,
    "DEL": 67,
    "SETTINGS": 176,
    "MEDIA_PLAY_PAUSE": 85,
    "MEDIA_STOP": 86,
    "MEDIA_NEXT": 87,
    "MEDIA_PREVIOUS": 88,
    "MEDIA_REWIND": 89,
    "MEDIA_FAST_FORWARD": 90,
    "DPAD_UP_LEFT": 93,
    "DPAD_DOWN_LEFT": 94,
    "DPAD_UP_RIGHT": 95,
    "DPAD_DOWN_RIGHT": 96,
    "MOVE_HOME": 122,
    "MOVE_END": 123,
    "NUMPAD_ENTER": 160,
    "APP_SWITCH": 187,
    "EXPLORER": 200,
    "INFO": 201,
    "SEARCH": 84,
    "GUIDE": 288,
    "DVR": 289,
    "LIVE": 290,
    "PROGRAM_BROWSER": 291,
    "CAPTIONS": 292,
    "SUBTITLE": 293,
    "STB_INPUT": 294,
    "TV_INPUT": 295,
    "INPUT": 296,
    "MEDIA_AUDIO_TRACK": 297,
    "MEDIA_SKIP_FORWARD": 298,
    "MEDIA_SKIP_BACKWARD": 299,
    "MEDIA_STEP_FORWARD": 300,
    "MEDIA_STEP_BACKWARD": 301,
    "MEDIA_TOP_MENU": 302,
    "MEDIA_CONTEXT_MENU": 303,
    "PAGE_UP": 92,
    "PAGE_DOWN": 93,
    "CHANNEL_UP": 166,
    "CHANNEL_DOWN": 167,
    "ZOOM_IN": 168,
    "ZOOM_OUT": 169,
    "SLEEP": 223,
    "WAKEUP": 224,
    "PAIRING": 225,
    "MEDIA_RECORD": 130,
    "MEDIA_PLAY": 126,
    "MEDIA_PAUSE": 127,
    "CAPS_LOCK": 115,
    "SPACE": 62,
    "TAB": 61,
}


def _parse_bounds(bounds_str: str) -> tuple[int, int, int, int]:
    parsed = bounds_str.replace("[", "").replace("]", ",").split(",")
    if len(parsed) >= 4:
        return (int(parsed[0]), int(parsed[1]), int(parsed[2]), int(parsed[3]))
    return (0, 0, 0, 0)


def _element_to_dict(node: ET.Element) -> dict[str, Any]:
    attrib = node.attrib
    bounds = _parse_bounds(attrib.get("bounds", ""))
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


def _traverse(node: ET.Element) -> dict[str, Any]:
    elem = _element_to_dict(node)
    for child in node:
        elem["children"].append(_traverse(child))
    return elem


def _find_focused(node: ET.Element) -> Optional[dict[str, Any]]:
    if node.attrib.get("focused", "false") == "true":
        return _element_to_dict(node)
    for child in node:
        result = _find_focused(child)
        if result is not None:
            return result
    return None


def _find_all_focusable(node: ET.Element) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if node.attrib.get("focusable", "false") == "true":
        results.append(_element_to_dict(node))
    for child in node:
        results.extend(_find_all_focusable(child))
    return results


class DeviceController:
    def __init__(self, serial: str = "") -> None:
        self._device: Optional[u2.Device] = None
        self._serial: Optional[str] = serial or None
        self._u2_available: bool = _HAS_U2

    def connect(self, serial: str) -> bool:
        if not self._u2_available:
            logger.error("uiautomator2 is not installed; cannot connect via u2")
            return False
        try:
            self._device = u2.connect(serial)
            _ = self._device.info
            self._serial = serial
            logger.info("Connected to device %s", serial)
            return True
        except Exception as exc:
            logger.error("Failed to connect to %s: %s", serial, exc)
            self._device = None
            self._serial = None
            return False

    def disconnect(self) -> None:
        if self._device is not None:
            try:
                self._device.disconnect()
            except Exception as exc:
                logger.warning("Error during disconnect: %s", exc)
        self._device = None
        self._serial = None
        logger.info("Disconnected from device")

    def get_ui_tree(self) -> ET.Element:
        raw_xml = self._dump_hierarchy()
        root = ET.fromstring(raw_xml.encode("utf-8"))
        return root

    def _dump_hierarchy(self) -> str:
        if self._device is not None:
            try:
                return self._device.dump_hierarchy()
            except Exception as exc:
                logger.warning("u2 dump_hierarchy failed: %s. Falling back to adb.", exc)
        return self._shell_xml_dump()

    def _shell_xml_dump(self) -> str:
        try:
            raw = self.shell("uiautomator dump /dev/tty 2>/dev/null || uiautomator dump /sdcard/ui.xml && cat /sdcard/ui.xml && rm /sdcard/ui.xml")
            start = raw.find("<")
            if start >= 0:
                raw = raw[start:]
            return raw
        except Exception as exc:
            logger.error("ADB shell xml dump failed: %s", exc)
            return "<hierarchy/>"

    def get_focused_element(self) -> dict[str, Any]:
        try:
            tree = self.get_ui_tree()
            result = _find_focused(tree)
            if result is not None:
                return result
        except Exception as exc:
            logger.warning("get_focused_element error: %s", exc)
        return {
            "resource_id": "",
            "content_desc": "",
            "text": "",
            "class_name": "",
            "package": "",
            "focused": False,
            "focusable": False,
            "selected": False,
            "checkable": False,
            "checked": False,
            "clickable": False,
            "enabled": True,
            "long_clickable": False,
            "scrollable": False,
            "index": 0,
            "bounds_left": 0,
            "bounds_top": 0,
            "bounds_right": 0,
            "bounds_bottom": 0,
            "bounds_width": 0,
            "bounds_height": 0,
            "children": [],
        }

    def get_focusable_elements(self) -> list[dict[str, Any]]:
        try:
            tree = self.get_ui_tree()
            return _find_all_focusable(tree)
        except Exception as exc:
            logger.warning("get_focusable_elements error: %s", exc)
            return []

    def press_key(self, keycode: str) -> None:
        keycode_upper = keycode.upper()
        code = KEYCODE_MAP.get(keycode_upper)
        if code is None:
            logger.warning("Unknown keycode: %s", keycode)
            return
        try:
            if self._device is not None:
                try:
                    self._device.press(code)
                    return
                except Exception as exc:
                    logger.warning("u2 press failed: %s. Falling back to adb.", exc)
            self.shell(f"input keyevent {code}")
        except Exception as exc:
            logger.error("press_key %s failed: %s", keycode, exc)

    def screenshot(self) -> Image.Image:
        if self._device is not None:
            try:
                raw = self._device.screenshot(format="raw")
                buf = io.BytesIO(raw)
                return Image.open(buf).convert("RGB")
            except Exception as exc:
                logger.warning("u2 screenshot failed: %s. Falling back to adb.", exc)
        return self._adb_screenshot()

    def _adb_screenshot(self) -> Image.Image:
        try:
            raw = self.shell("screencap -p 2>/dev/null")
            if not raw:
                raise RuntimeError("Empty screenshot output")
            buf = io.BytesIO(raw.encode("latin-1") if isinstance(raw, str) else raw)
            return Image.open(buf).convert("RGB")
        except Exception as exc:
            logger.error("ADB screenshot failed: %s", exc)
            return Image.new("RGB", (1920, 1080), (0, 0, 0))

    def get_current_activity(self) -> str:
        try:
            if self._device is not None:
                try:
                    info = self._device.app_current()
                    activity = info.get("activity", "")
                    if activity:
                        if activity.startswith("."):
                            pkg = info.get("package", "")
                            activity = pkg + activity
                        return activity
                except Exception as exc:
                    logger.warning("u2 app_current failed: %s", exc)
            output = self.shell("dumpsys window windows 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | head -1")
            if "/" in output:
                parts = output.split("/")
                if len(parts) >= 2:
                    act_part = parts[1].split("}")[0].strip()
                    return act_part
            return ""
        except Exception as exc:
            logger.error("get_current_activity failed: %s", exc)
            return ""

    def wait_stable(self, timeout_ms: int = 3000) -> bool:
        deadline = time.time() + (timeout_ms / 1000.0)
        last_tree: Optional[str] = None
        while time.time() < deadline:
            try:
                current = self._dump_hierarchy()
                if last_tree is not None and current == last_tree:
                    return True
                last_tree = current
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def get_display_size(self) -> tuple[int, int]:
        try:
            if self._device is not None:
                try:
                    info = self._device.info
                    width = info.get("displayWidth", 0)
                    height = info.get("displayHeight", 0)
                    if width and height:
                        return (width, height)
                except Exception:
                    pass
            output = self.shell("wm size 2>/dev/null")
            if "Physical size:" in output:
                dims = output.split("Physical size:")[1].strip().split("x")
                return (int(dims[0]), int(dims[1]))
            return (1920, 1080)
        except Exception:
            return (1920, 1080)

    def shell(self, cmd: str) -> str:
        if self._device is not None:
            try:
                return self._device.shell(cmd).output
            except Exception as exc:
                logger.warning("u2 shell failed: %s. Trying adb directly.", exc)
        try:
            serial_arg = []
            if self._serial:
                serial_arg = ["-s", self._serial]
            result = subprocess.run(
                ["adb"] + serial_arg + ["shell", cmd],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout
        except Exception as exc:
            logger.error("ADB shell command failed: %s", exc)
            return ""

    def start_app(self, package: str, activity: str = "") -> None:
        try:
            if self._device is not None:
                try:
                    self._device.app_start(package, activity=activity if activity else None)
                    return
                except Exception as exc:
                    logger.warning("u2 app_start failed: %s. Falling back to adb.", exc)
            if activity:
                self.shell(f"am start -n {package}/{activity}")
            else:
                self.shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")
        except Exception as exc:
            logger.error("start_app failed: %s", exc)

    def stop_app(self, package: str) -> None:
        try:
            if self._device is not None:
                try:
                    self._device.app_stop(package)
                    return
                except Exception as exc:
                    logger.warning("u2 app_stop failed: %s. Falling back to adb.", exc)
            self.shell(f"am force-stop {package}")
        except Exception as exc:
            logger.error("stop_app failed: %s", exc)

    def is_app_foreground(self, package: str) -> bool:
        try:
            current = self.get_current_activity()
            return current.startswith(package)
        except Exception:
            return False

    def wait_for_activity(self, activity: str, timeout_ms: int = 8000) -> bool:
        deadline = time.time() + (timeout_ms / 1000.0)
        while time.time() < deadline:
            try:
                current = self.get_current_activity()
                if current and (current == activity or current.endswith(activity)):
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def close_popups(self) -> bool:
        try:
            tree = self.get_ui_tree()
            dismissed = False

            dismiss_ids = [
                "android:id/button1",
                "android:id/button2",
                "android:id/button3",
                "com.android.systemui:id/back",
                "android:id/parentPanel",
            ]
            dismiss_texts = [
                "allow",
                "deny",
                "ok",
                "cancel",
                "dismiss",
                "close",
                "yes",
                "no",
                "agree",
                "disagree",
                "confirm",
            ]

            def _walk_and_dismiss(node: ET.Element) -> bool:
                rid = node.attrib.get("resource-id", "")
                txt = node.attrib.get("text", "").lower()
                desc = node.attrib.get("content-desc", "").lower()
                clazz = node.attrib.get("class", "")

                if rid in dismiss_ids:
                    try:
                        self.press_key("DPAD_CENTER")
                        return True
                    except Exception:
                        pass
                if txt in dismiss_texts or desc in dismiss_texts:
                    try:
                        self.press_key("DPAD_CENTER")
                        return True
                    except Exception:
                        pass
                if clazz.endswith("AlertDialog"):
                    try:
                        self.press_key("BACK")
                        return True
                    except Exception:
                        pass
                for child in node:
                    if _walk_and_dismiss(child):
                        return True
                return False

            dismissed = _walk_and_dismiss(tree)
            if dismissed:
                time.sleep(0.5)
            return dismissed
        except Exception as exc:
            logger.warning("close_popups failed: %s", exc)
            return False
