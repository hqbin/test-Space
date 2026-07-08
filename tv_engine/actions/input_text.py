import logging
from typing import Any

logger = logging.getLogger(__name__)

_TEXT_KEYCODE_MAP: dict[str, int] = {
    **{chr(i): key for key, i in {
        29: 'a', 30: 'b', 31: 'c', 32: 'd', 33: 'e', 34: 'f', 35: 'g',
        36: 'h', 37: 'i', 38: 'j', 39: 'k', 40: 'l', 41: 'm', 42: 'n',
        43: 'o', 44: 'p', 45: 'q', 46: 'r', 47: 's', 48: 't', 49: 'u',
        50: 'v', 51: 'w', 52: 'x', 53: 'y', 54: 'z',
    }.items()},
    56: '0', 57: '1', 58: '2', 59: '3', 60: '4', 61: '5', 62: '6', 63: '7', 64: '8', 65: '9',
    66: 'enter', 67: 'del', 62: ' ', 61: 'tab', 115: 'caps_lock',
}


def handle_input_text(*, device: Any, step: dict, context: dict, timeout: int) -> None:
    text = step.get("text", "")
    if not text:
        raise ValueError("input_text requires 'text'")
    clear_first = step.get("clear_first", True)
    if clear_first:
        for _ in range(20):
            device.press_key("DEL")
    for char in text:
        lower = char.lower()
        code = _find_code(lower)
        if code is not None:
            if char.isupper():
                from tv_engine.core.device import KEYCODE_MAP
                device.shell(f"input keyevent 59")
            device.shell(f"input keyevent {code}")
            if char.isupper():
                device.shell(f"input keyevent 59")
        else:
            device.shell(f"input text {_shell_escape(char)}")


def _find_code(char: str) -> int | None:
    reverse = {v: k for k, v in _TEXT_KEYCODE_MAP.items()}
    return reverse.get(char)


def _shell_escape(c: str) -> str:
    if c in ' &|;()<>`$!\\"\'#~*?[]{}':
        return f"\\\\{c}"
    return c
