from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core import gui


class GuiTests(unittest.TestCase):
    def test_click_with_point_tuple(self) -> None:
        backend = SimpleNamespace(click=Mock())
        with patch("core.gui._backend", return_value=backend):
            gui.click((10, 20))
        backend.click.assert_called_once_with((10, 20))

    def test_press_uses_presses_and_interval(self) -> None:
        backend = SimpleNamespace(press=Mock())
        with patch("core.gui._backend", return_value=backend):
            gui.press("enter", presses=2, interval=0.3)
        backend.press.assert_called_once_with("enter", presses=2, interval=0.3)

    def test_hotkey_passthrough(self) -> None:
        backend = SimpleNamespace(hotkey=Mock())
        with patch("core.gui._backend", return_value=backend):
            gui.hotkey("command", "w")
        backend.hotkey.assert_called_once_with("command", "w")


if __name__ == "__main__":
    unittest.main()
