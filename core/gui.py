from __future__ import annotations

import sys
from typing import Any

HOTKEYS_MAC: dict[str, tuple[str, ...]] = {
    "focus_address_bar": ("command", "l"),
    "refresh_page": ("command", "r"),
    "select_all": ("command", "a"),
    "copy": ("command", "c"),
    "paste": ("command", "v"),
    "save": ("command", "s"),
    "view_source": ("command", "option", "u"),
    "print_page": ("command", "p"),
    "close_tab": ("command", "w"),
    "shift_tab": ("shift", "tab"),
    "search": ("command", "f"),
}

HOTKEYS_WIN: dict[str, tuple[str, ...]] = {
    "focus_address_bar": ("ctrl", "l"),
    "refresh_page": ("ctrl", "r"),
    "select_all": ("ctrl", "a"),
    "copy": ("ctrl", "c"),
    "paste": ("ctrl", "v"),
    "save": ("ctrl", "s"),
    "view_source": ("ctrl", "u"),
    "print_page": ("ctrl", "p"),
    "close_tab": ("ctrl", "w"),
    "shift_tab": ("shift", "tab"),
    "search": ("ctrl", "f"),
}


def click(x: Any = None, y: Any = None, **kwargs: Any) -> None:
    if y is None and x is not None and not isinstance(x, (int, float)):
        _backend().click(x, **kwargs)
        return
    _backend().click(x, y, **kwargs)


def press(key: str, presses: int = 1, interval: float = 0.0) -> None:
    _backend().press(key, presses=max(1, int(presses)), interval=max(0.0, float(interval)))


def hotkey(*keys_or_action: str) -> None:
    if len(keys_or_action) == 1:
        action = keys_or_action[0]
        if action in _mapping():
            _backend().hotkey(*get_hotkey(action))
            return
    _backend().hotkey(*keys_or_action)


def write(text: str, interval: float = 0.0) -> None:
    _backend().write(text, interval=max(0.0, float(interval)))


def scroll(clicks: int) -> None:
    _backend().scroll(clicks)


def moveTo(x: int, y: int, duration: float = 0.0) -> None:
    _backend().moveTo(x, y, duration=max(0.0, float(duration)))


def size() -> Any:
    return _backend().size()


def position() -> Any:
    return _backend().position()


def get_hotkey(action: str) -> tuple[str, ...]:
    key = str(action or "").strip()
    mapping = _mapping()
    if key not in mapping:
        raise KeyError(f"Unsupported hotkey action: {action}")
    return mapping[key]


def _mapping() -> dict[str, tuple[str, ...]]:
    return HOTKEYS_MAC if is_mac() else HOTKEYS_WIN


def is_mac() -> bool:
    return sys.platform == "darwin"


def _backend():
    import pyautogui  # type: ignore

    return pyautogui
