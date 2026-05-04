from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import call, patch

from core import utils


class UtilsPlaceholderTests(unittest.TestCase):
    def test_get_current_url_uses_expected_steps(self) -> None:
        with (
            patch("core.utils.gui.hotkey") as hotkey_mock,
            patch("core.utils.gui.press") as press_mock,
            patch("core.utils.time.sleep", return_value=None) as sleep_mock,
            patch("core.utils._read_clipboard", return_value="https://example.com/paper"),
        ):
            url = utils.get_current_url()

        self.assertEqual(url, "https://example.com/paper")
        self.assertEqual(hotkey_mock.call_args_list, [call("focus_address_bar"), call("copy")])
        self.assertEqual(sleep_mock.call_args_list, [call(0.5), call(1)])
        press_mock.assert_called_once_with("esc")

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

    def test_loop_close_tabs_returns_true_when_current_is_baidu(self) -> None:
        with (
            patch("core.utils.get_current_url", return_value="https://www.baidu.com/s?wd=test"),
            patch("core.utils.gui.hotkey") as hotkey_mock,
        ):
            ok = utils.loop_close_tabs()
        self.assertTrue(ok)
        hotkey_mock.assert_not_called()

    def test_loop_close_tabs_closes_until_baidu(self) -> None:
        with (
            patch("core.utils.get_current_url", side_effect=["https://example.com/a", "https://example.org/b", "https://www.baidu.com"]),
            patch("core.utils.gui.hotkey") as hotkey_mock,
            patch("core.utils.time.sleep", return_value=None),
        ):
            ok = utils.loop_close_tabs(max_rounds=10)
        self.assertTrue(ok)
        self.assertEqual(hotkey_mock.call_count, 2)
        for item in hotkey_mock.call_args_list:
            self.assertEqual(item.args[0], "close_tab")

    def test_loop_close_tabs_stops_at_max_rounds(self) -> None:
        with (
            patch("core.utils.get_current_url", return_value="https://example.com/a"),
            patch("core.utils.gui.hotkey") as hotkey_mock,
            patch("core.utils.time.sleep", return_value=None),
        ):
            ok = utils.loop_close_tabs(max_rounds=3)
        self.assertFalse(ok)
        self.assertEqual(hotkey_mock.call_count, 3)


if __name__ == "__main__":
    unittest.main()
