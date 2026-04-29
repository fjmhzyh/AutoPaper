from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import utils


class UtilsPlaceholderTests(unittest.TestCase):
    def test_check_keywords_exist_returns_case_insensitive_matches(self) -> None:
        hotkey_calls: list[str] = []
        with (
            patch("core.utils._write_clipboard") as write_mock,
            patch("core.utils.gui.hotkey", side_effect=lambda action: hotkey_calls.append(action)),
            patch("core.utils.time.sleep", return_value=None),
            patch("core.utils._read_clipboard", return_value="Contains PDF and md keyword"),
            patch("core.utils.cancel_select_all", return_value=None),
        ):
            result = utils.check_keywords_exist(["pdf", "MD", "", "xyz"])

        write_mock.assert_called_once_with("")
        self.assertEqual(hotkey_calls, ["select_all", "copy"])
        self.assertEqual(result, (True, True, False, False))

    def test_photo_uses_platform_and_resolution_profile(self) -> None:
        with patch("core.utils._screen_size", return_value=(1280, 828)), patch("core.utils.sys.platform", "darwin"):
            path = utils.photo("advanced.onlinelibrary.wiley.com1.png")
        self.assertIn("photos/mac_1280_828/advanced.onlinelibrary.wiley.com1.png", path)

    def test_photo_raises_when_profile_image_missing(self) -> None:
        with patch("core.utils._screen_size", return_value=(1280, 828)), patch("core.utils.sys.platform", "darwin"):
            with self.assertRaises(FileNotFoundError):
                utils.photo("not_exists.png")

    def test_locate_image_returns_center_point(self) -> None:
        location = SimpleNamespace(left=100, top=200, width=40, height=20)
        with patch("core.utils._locate_on_screen", return_value=location), patch("core.utils.sys.platform", "win32"):
            self.assertEqual(utils.locate_image("x.png", confidence=0.7), (120, 210))

    def test_locate_image_returns_scaled_center_on_mac(self) -> None:
        location = SimpleNamespace(left=100, top=200, width=40, height=20)
        with patch("core.utils._locate_on_screen", return_value=location), patch("core.utils.sys.platform", "darwin"):
            self.assertEqual(utils.locate_image("x.png"), (60, 105))

    def test_locate_image_returns_none_when_not_found(self) -> None:
        with patch("core.utils._locate_on_screen", return_value=None):
            self.assertIsNone(utils.locate_image("x.png"))


if __name__ == "__main__":
    unittest.main()
