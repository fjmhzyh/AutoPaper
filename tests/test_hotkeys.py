from __future__ import annotations

import unittest
from unittest.mock import patch

from core import gui


class HotkeysTests(unittest.TestCase):
    def test_get_hotkey_returns_mac_mapping(self) -> None:
        with patch("core.gui.is_mac", return_value=True):
            self.assertEqual(gui.get_hotkey("focus_address_bar"), ("command", "l"))

    def test_get_hotkey_returns_win_mapping(self) -> None:
        with patch("core.gui.is_mac", return_value=False):
            self.assertEqual(gui.get_hotkey("focus_address_bar"), ("ctrl", "l"))

    def test_send_hotkey_uses_backend(self) -> None:
        calls: list[tuple[str, ...]] = []

        with patch("core.gui.is_mac", return_value=True), patch(
            "core.gui._backend"
        ) as backend_mock:
            backend_mock.return_value.hotkey.side_effect = lambda *keys: calls.append(tuple(keys))
            gui.hotkey("close_tab")
        self.assertEqual(calls, [("command", "w")])

    def test_hotkey_allows_raw_keys(self) -> None:
        calls: list[tuple[str, ...]] = []
        with patch("core.gui._backend") as backend_mock:
            backend_mock.return_value.hotkey.side_effect = lambda *keys: calls.append(tuple(keys))
            gui.hotkey("command", "w")
        self.assertEqual(calls, [("command", "w")])

    def test_hotkey_unknown_action_falls_back_to_raw(self) -> None:
        calls: list[tuple[str, ...]] = []
        with patch("core.gui._backend") as backend_mock:
            backend_mock.return_value.hotkey.side_effect = lambda *keys: calls.append(tuple(keys))
            gui.hotkey("not_an_action")
        self.assertEqual(calls, [("not_an_action",)])


if __name__ == "__main__":
    unittest.main()
