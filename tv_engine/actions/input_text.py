import logging
from typing import Any

logger = logging.getLogger(__name__)

_TEXT_KEYCODE_MAP: dict[str, int] = {
    'a': 29, 'b': 30, 'c': 31, 'd': 32, 'e': 33, 'f': 34, 'g': 35,
    'h': 36, 'i': 37, 'j': 38, 'k': 39, 'l': 40, 'm': 41, 'n': 42,
    'o': 43, 'p': 44, 'q': 45, 'r': 46, 's': 47, 't': 48, 'u': 49,
    'v': 50, 'w': 51, 'x': 52, 'y': 53, 'z': 54,
    '0': 7, '1': 8, '2': 9, '3': 10, '4': 11, '5': 12, '6': 13, '7': 14, '8': 15, '9': 16,
    ' ': 62, '\t': 61, 'enter': 66, 'del': 67, 'caps_lock': 115,
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
    return _TEXT_KEYCODE_MAP.get(char)


def _shell_escape(c: str) -> str:
    if c in ' &|;()<>`$!\\"\'#~*?[]{}':
        return f"\\\\{c}"
    return c
