from __future__ import annotations

import unittest
from unittest.mock import patch

from core.browser_controller import BrowserController


class _FakeBackend:
    def __init__(self):
        self.hotkey_calls: list[tuple[str, ...]] = []

    def hotkey(self, *keys: str) -> None:
        self.hotkey_calls.append(keys)


class _FakeChromeBrowser:
    def __init__(self, result: bool = True):
        self.result = result
        self.opened_urls: list[str] = []

    def open_new_tab(self, url: str) -> bool:
        self.opened_urls.append(url)
        return self.result


class BrowserControllerTests(unittest.TestCase):
    def test_open_tab_opens_url_in_chrome(self) -> None:
        controller = BrowserController()
        fake_chrome = _FakeChromeBrowser(result=True)

        with patch.object(controller, "_chrome_browser", return_value=fake_chrome):
            controller.open_tab("https://doi.org/10.1000/xyz")

        self.assertEqual(fake_chrome.opened_urls, ["https://doi.org/10.1000/xyz"])

    def test_open_tab_raises_for_empty_url(self) -> None:
        controller = BrowserController()
        with self.assertRaises(ValueError):
            controller.open_tab("  ")

    def test_open_tab_raises_when_browser_open_fails(self) -> None:
        controller = BrowserController()
        fake_chrome = _FakeChromeBrowser(result=False)

        with patch.object(controller, "_chrome_browser", return_value=fake_chrome):
            with self.assertRaises(RuntimeError):
                controller.open_tab("https://doi.org/10.1000/xyz")

    def test_close_tab_uses_platform_modifier(self) -> None:
        backend = _FakeBackend()
        controller = BrowserController(backend=backend)

        with patch("core.browser_controller.sys.platform", "darwin"):
            controller.close_tab()

        self.assertEqual(backend.hotkey_calls, [("command", "w")])


if __name__ == "__main__":
    unittest.main()
