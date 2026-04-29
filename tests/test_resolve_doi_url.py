from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.app_config import AppConfig
from core.resolve_doi_url import check_page_loaded, resolve_doi_url


class _FakeBrowser:
    def __init__(self, copied_urls: list[str]):
        self.copied_urls = copied_urls
        self._copy_index = 0
        self.new_tab_urls: list[str] = []
        self.refresh_calls = 0
        self.launch_calls = 0
        self.ensure_ready_calls = 0

        class _Config:
            launch_wait_sec = 0

        self.config = _Config()

    def new_tab(self, url: str | None = None) -> None:
        self.new_tab_urls.append(url or "")

    def refresh_page(self) -> None:
        self.refresh_calls += 1

    def launch_browser(self, url: str | None = None) -> None:
        self.launch_calls += 1

    def ensure_ready(self) -> None:
        self.ensure_ready_calls += 1

    def copy_current_tab_url(self) -> str:
        if not self.copied_urls:
            return ""
        if self._copy_index >= len(self.copied_urls):
            return self.copied_urls[-1]
        value = self.copied_urls[self._copy_index]
        self._copy_index += 1
        return value


class ResolveDoiUrlTests(unittest.TestCase):
    def test_resolve_success_on_first_check(self) -> None:
        browser = _FakeBrowser(
            copied_urls=[
                "https://publisher.com/paper/123",
                "https://publisher.com/paper/123",
            ]
        )
        with (
            patch("core.resolve_doi_url.BrowserController", return_value=browser),
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("10.1000/xyz")
        self.assertEqual(result, "https://publisher.com/paper/123")
        self.assertEqual(browser.new_tab_urls, ["https://doi.org/10.1000/xyz"])
        self.assertEqual(browser.refresh_calls, 0)
        self.assertEqual(browser.launch_calls, 0)
        self.assertEqual(browser.ensure_ready_calls, 1)

    def test_resolve_success_after_refresh(self) -> None:
        browser = _FakeBrowser(
            copied_urls=[
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
                "https://publisher.com/final",
                "https://publisher.com/final",
            ]
        )
        with (
            patch("core.resolve_doi_url.BrowserController", return_value=browser),
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("doi:10.1000/xyz")
        self.assertEqual(result, "https://publisher.com/final")
        self.assertEqual(browser.refresh_calls, 1)
        self.assertEqual(browser.new_tab_urls, ["https://doi.org/10.1000/xyz"])
        self.assertEqual(browser.launch_calls, 0)
        self.assertEqual(browser.ensure_ready_calls, 1)

    def test_resolve_returns_none_after_retry(self) -> None:
        browser = _FakeBrowser(
            copied_urls=[
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
            ]
        )
        with (
            patch("core.resolve_doi_url.BrowserController", return_value=browser),
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("https://doi.org/10.1000/xyz")
        self.assertIsNone(result)
        self.assertEqual(browser.refresh_calls, 1)
        self.assertEqual(browser.ensure_ready_calls, 1)

    def test_resolve_returns_none_for_empty_doi(self) -> None:
        browser = _FakeBrowser(copied_urls=[])
        with (
            patch("core.resolve_doi_url.BrowserController", return_value=browser),
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("  ")
        self.assertIsNone(result)
        self.assertEqual(browser.new_tab_urls, [])

    def test_resolve_retries_new_tab_once_after_ready_recheck(self) -> None:
        from core.browser_controller import BrowserController

        class _FailHotkeyBackend:
            def __init__(self):
                self.fail_once = True
                self.hotkey_calls: list[tuple[str, ...]] = []

            def hotkey(self, *keys: str) -> None:
                if self.fail_once and len(keys) == 2 and keys[1] == "t":
                    self.fail_once = False
                    raise RuntimeError("tab open failed once")
                self.hotkey_calls.append(keys)

            def typewrite(self, _text: str, interval: float = 0.0) -> None:  # noqa: ARG002
                return

            def press(self, _key: str) -> None:  # noqa: ARG002
                return

        controller = BrowserController(backend=_FailHotkeyBackend())
        ensure_ready_calls = 0

        def fake_ensure_ready() -> None:
            nonlocal ensure_ready_calls
            ensure_ready_calls += 1

        copy_calls = 0

        def fake_copy_current_tab_url() -> str:
            nonlocal copy_calls
            copy_calls += 1
            return "https://publisher.com/paper/1"

        with (
            patch("core.resolve_doi_url.BrowserController", return_value=controller),
            patch.object(controller, "ensure_ready", side_effect=fake_ensure_ready),
            patch.object(controller, "copy_current_tab_url", side_effect=fake_copy_current_tab_url),
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("10.1000/xyz")

        self.assertEqual(result, "https://publisher.com/paper/1")
        self.assertEqual(ensure_ready_calls, 2)

    def test_check_page_loaded_success(self) -> None:
        browser = _FakeBrowser(["https://publisher.com/a", "https://publisher.com/a"])
        with patch("core.resolve_doi_url.time.sleep", return_value=None):
            loaded, url = check_page_loaded(browser)
        self.assertTrue(loaded)
        self.assertEqual(url, "https://publisher.com/a")

    def test_check_page_loaded_fails_for_unstable_or_doi_host(self) -> None:
        unstable_browser = _FakeBrowser(["https://publisher.com/a", "https://publisher.com/b"])
        with patch("core.resolve_doi_url.time.sleep", return_value=None):
            loaded_1, url_1 = check_page_loaded(unstable_browser)
        self.assertFalse(loaded_1)
        self.assertIsNone(url_1)

        doi_browser = _FakeBrowser(["https://doi.org/10.1000/xyz", "https://doi.org/10.1000/xyz"])
        with patch("core.resolve_doi_url.time.sleep", return_value=None):
            loaded_2, url_2 = check_page_loaded(doi_browser)
        self.assertFalse(loaded_2)
        self.assertIsNone(url_2)

    def test_read_page_load_sec_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text("[download]\npage_load_sec = 12\n", encoding="utf-8")
            browser = _FakeBrowser(["https://publisher.com/x", "https://publisher.com/x"])
            temp_cfg = AppConfig(config_path)
            with (
                patch("core.resolve_doi_url.BrowserController", return_value=browser),
                patch("core.resolve_doi_url.get_config", return_value=temp_cfg),
                patch("core.resolve_doi_url.time.sleep", return_value=None) as sleep_mock,
            ):
                result = resolve_doi_url("10.1000/xyz")
        self.assertEqual(result, "https://publisher.com/x")
        self.assertTrue(sleep_mock.called)


if __name__ == "__main__":
    unittest.main()
