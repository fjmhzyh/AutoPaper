from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.app_config import AppConfig
from core.resolve_doi_url import check_page_loaded, resolve_doi_url


class ResolveDoiUrlTests(unittest.TestCase):
    def test_resolve_success_on_first_check(self) -> None:
        with (
            patch("core.resolve_doi_url.BrowserController") as controller_cls,
            patch("core.resolve_doi_url.get_current_url", side_effect=[
                "https://publisher.com/paper/123",
                "https://publisher.com/paper/123",
            ]),
            patch("core.resolve_doi_url._refresh_page") as refresh_mock,
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("10.1000/xyz")

        controller_cls.return_value.open_tab.assert_called_once_with("https://doi.org/10.1000/xyz")
        refresh_mock.assert_not_called()
        self.assertEqual(result, "https://publisher.com/paper/123")

    def test_resolve_success_after_refresh(self) -> None:
        with (
            patch("core.resolve_doi_url.BrowserController") as controller_cls,
            patch("core.resolve_doi_url.get_current_url", side_effect=[
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
                "https://publisher.com/final",
                "https://publisher.com/final",
            ]),
            patch("core.resolve_doi_url._refresh_page") as refresh_mock,
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("doi:10.1000/xyz")

        controller_cls.return_value.open_tab.assert_called_once_with("https://doi.org/10.1000/xyz")
        refresh_mock.assert_called_once()
        self.assertEqual(result, "https://publisher.com/final")

    def test_resolve_returns_none_after_retry(self) -> None:
        with (
            patch("core.resolve_doi_url.BrowserController") as controller_cls,
            patch("core.resolve_doi_url.get_current_url", side_effect=[
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
                "https://doi.org/10.1000/xyz",
            ]),
            patch("core.resolve_doi_url._refresh_page") as refresh_mock,
            patch("core.resolve_doi_url.time.sleep", return_value=None),
        ):
            result = resolve_doi_url("https://doi.org/10.1000/xyz")

        controller_cls.return_value.open_tab.assert_called_once_with("https://doi.org/10.1000/xyz")
        refresh_mock.assert_called_once()
        self.assertIsNone(result)

    def test_resolve_returns_none_for_empty_doi(self) -> None:
        with patch("core.resolve_doi_url.BrowserController") as controller_cls:
            result = resolve_doi_url("  ")
        controller_cls.assert_not_called()
        self.assertIsNone(result)

    def test_check_page_loaded_success(self) -> None:
        values = iter(["https://publisher.com/a", "https://publisher.com/a"])

        def read_url() -> str:
            return next(values)

        with patch("core.resolve_doi_url.time.sleep", return_value=None):
            loaded, url = check_page_loaded(read_url)
        self.assertTrue(loaded)
        self.assertEqual(url, "https://publisher.com/a")

    def test_check_page_loaded_fails_for_unstable_or_doi_host(self) -> None:
        unstable_values = iter(["https://publisher.com/a", "https://publisher.com/b"])
        doi_values = iter(["https://doi.org/10.1000/xyz", "https://doi.org/10.1000/xyz"])

        with patch("core.resolve_doi_url.time.sleep", return_value=None):
            loaded_1, url_1 = check_page_loaded(lambda: next(unstable_values))
            loaded_2, url_2 = check_page_loaded(lambda: next(doi_values))

        self.assertFalse(loaded_1)
        self.assertIsNone(url_1)
        self.assertFalse(loaded_2)
        self.assertIsNone(url_2)

    def test_read_page_load_sec_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text("[download]\npage_load_sec = 12\n", encoding="utf-8")
            temp_cfg = AppConfig(config_path)
            with (
                patch("core.resolve_doi_url.BrowserController"),
                patch("core.resolve_doi_url.get_current_url", side_effect=[
                    "https://publisher.com/x",
                    "https://publisher.com/x",
                ]),
                patch("core.resolve_doi_url._refresh_page"),
                patch("core.resolve_doi_url.get_config", return_value=temp_cfg),
                patch("core.resolve_doi_url.time.sleep", return_value=None) as sleep_mock,
            ):
                result = resolve_doi_url("10.1000/xyz")

        self.assertEqual(result, "https://publisher.com/x")
        self.assertTrue(sleep_mock.called)


if __name__ == "__main__":
    unittest.main()
