from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.browser_controller import (
    BrowserAutomationError,
    BrowserConfig,
    BrowserController,
    BrowserErrorCode,
)


class _FakeBackend:
    def __init__(self):
        self.hotkey_calls: list[tuple[str, ...]] = []
        self.typewrite_calls: list[tuple[str, float]] = []
        self.press_calls: list[str] = []
        self.fail_hotkey_once = False
        self.fail_hotkey_always = False

    def hotkey(self, *keys: str) -> None:
        if self.fail_hotkey_always:
            raise RuntimeError("hotkey failed")
        if self.fail_hotkey_once:
            self.fail_hotkey_once = False
            raise RuntimeError("hotkey failed once")
        self.hotkey_calls.append(keys)

    def typewrite(self, text: str, interval: float = 0.0) -> None:
        self.typewrite_calls.append((text, interval))

    def press(self, key: str) -> None:
        self.press_calls.append(key)


class BrowserControllerTests(unittest.TestCase):
    def _make_controller(self, config_text: str | None = None) -> BrowserController:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        config_dir = root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.toml"
        if config_text is not None:
            config_path.write_text(config_text, encoding="utf-8")
        fake_backend = _FakeBackend()
        controller = BrowserController(
            project_root=root,
            config_path=config_path,
            backend=fake_backend,
        )
        self.addCleanup(self.temp_dir.cleanup)
        return controller

    def test_config_defaults_when_browser_section_missing(self) -> None:
        controller = self._make_controller(config_text="[app]\nname = \"AutoPaper\"\n")
        self.assertEqual(controller.config, BrowserConfig())

    def test_config_reads_browser_values(self) -> None:
        controller = self._make_controller(
            config_text=(
                "[browser]\n"
                "prefer = \"chrome\"\n"
                "launch_wait_sec = 5\n"
                "action_interval_sec = 0.1\n"
            )
        )
        self.assertEqual(controller.config.prefer, "chrome")
        self.assertEqual(controller.config.launch_wait_sec, 5.0)
        self.assertEqual(controller.config.action_interval_sec, 0.1)

    def test_focus_tab_invalid_argument(self) -> None:
        controller = self._make_controller()
        with self.assertRaises(BrowserAutomationError) as ctx:
            controller.focus_tab(0)
        self.assertEqual(ctx.exception.code, BrowserErrorCode.INVALID_ARGUMENT)

    def test_switch_tab_invalid_argument(self) -> None:
        controller = self._make_controller()
        with self.assertRaises(BrowserAutomationError) as ctx:
            controller.switch_tab("left")
        self.assertEqual(ctx.exception.code, BrowserErrorCode.INVALID_ARGUMENT)

    def test_open_url_issues_expected_key_actions(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        fake_backend = controller._backend  # type: ignore[assignment]
        modifier = controller._modifier()

        controller.open_url("https://doi.org/10.1000/xyz123")

        self.assertEqual(fake_backend.hotkey_calls[0], (modifier, "l"))
        self.assertEqual(fake_backend.typewrite_calls[0][0], "https://doi.org/10.1000/xyz123")
        self.assertEqual(fake_backend.press_calls[0], "enter")

    def test_new_tab_with_url_issues_expected_key_actions(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        fake_backend = controller._backend  # type: ignore[assignment]
        modifier = controller._modifier()

        controller.new_tab("https://example.com")

        self.assertEqual(fake_backend.hotkey_calls[0], (modifier, "t"))
        self.assertEqual(fake_backend.typewrite_calls[0][0], "https://example.com")
        self.assertEqual(fake_backend.press_calls[0], "enter")

    def test_new_tab_retries_once_and_succeeds(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        fake_backend = controller._backend  # type: ignore[assignment]
        fake_backend.fail_hotkey_once = True
        with patch.object(controller, "ensure_ready") as ensure_ready_mock:
            controller.new_tab("https://example.com")
        ensure_ready_mock.assert_called_once()
        self.assertGreaterEqual(len(fake_backend.hotkey_calls), 1)

    def test_new_tab_fails_after_retry(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        fake_backend = controller._backend  # type: ignore[assignment]
        fake_backend.fail_hotkey_always = True
        with patch.object(controller, "ensure_ready") as ensure_ready_mock:
            with self.assertRaises(BrowserAutomationError) as ctx:
                controller.new_tab("https://example.com")
        ensure_ready_mock.assert_called_once()
        self.assertEqual(ctx.exception.code, BrowserErrorCode.TAB_OPEN_FAILED)

    def test_close_current_tab_issues_expected_key_actions(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        fake_backend = controller._backend  # type: ignore[assignment]
        modifier = controller._modifier()

        controller.close_current_tab()

        self.assertEqual(fake_backend.hotkey_calls[0], (modifier, "w"))

    def test_launch_browser_fallback_failure_raises_structured_error(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        with patch.object(controller, "_launch_chrome", return_value=False), patch.object(
            controller, "_launch_default_browser", return_value=False
        ):
            with self.assertRaises(BrowserAutomationError) as ctx:
                controller.launch_browser("https://doi.org")
        self.assertEqual(ctx.exception.code, BrowserErrorCode.LAUNCH_FAILED)

    def test_refresh_page_issues_expected_key_actions(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        fake_backend = controller._backend  # type: ignore[assignment]
        modifier = controller._modifier()

        controller.refresh_page()

        self.assertEqual(fake_backend.hotkey_calls[0], (modifier, "r"))

    def test_copy_current_tab_url_success(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        fake_backend = controller._backend  # type: ignore[assignment]
        modifier = controller._modifier()

        with patch.object(controller, "_read_clipboard_text", return_value="https://example.com/paper"):
            url = controller.copy_current_tab_url()

        self.assertEqual(url, "https://example.com/paper")
        self.assertEqual(fake_backend.hotkey_calls[0], (modifier, "l"))
        self.assertEqual(fake_backend.hotkey_calls[1], (modifier, "c"))

    def test_copy_current_tab_url_empty_clipboard_raises(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        with patch.object(controller, "_read_clipboard_text", return_value="  "):
            with self.assertRaises(BrowserAutomationError) as ctx:
                controller.copy_current_tab_url()
        self.assertEqual(ctx.exception.code, BrowserErrorCode.URL_COPY_FAILED)

    def test_is_running_returns_true_when_match_found_on_windows(self) -> None:
        controller = self._make_controller()
        with patch("core.browser_controller.sys.platform", "win32"), patch(
            "core.browser_controller.subprocess.check_output", return_value="chrome.exe 1234 Console"
        ):
            self.assertTrue(controller.is_running())

    def test_ensure_ready_skips_launch_when_running(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        with patch.object(controller, "is_running", return_value=True), patch.object(
            controller, "launch_browser"
        ) as launch_mock, patch.object(controller, "_activate_browser_window") as activate_mock:
            controller.ensure_ready()
        launch_mock.assert_not_called()
        activate_mock.assert_called_once()

    def test_ensure_ready_launches_when_not_running(self) -> None:
        controller = self._make_controller(
            config_text="[browser]\naction_interval_sec = 0\nlaunch_wait_sec = 0\n"
        )
        with patch.object(controller, "is_running", return_value=False), patch.object(
            controller, "launch_browser"
        ) as launch_mock, patch.object(controller, "_activate_browser_window") as activate_mock:
            controller.ensure_ready()
        launch_mock.assert_called_once()
        activate_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
