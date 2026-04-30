from __future__ import annotations

import unittest
from unittest.mock import patch

from publisher_download import wiley


class WileyDownloadTests(unittest.TestCase):
    def test_download_builds_paper_url_and_moves_file(self) -> None:
        with (
            patch(
                "publisher_download.wiley.download_paper_file",
                return_value=(True, "download/task_a/paper/paper_03_10.1000_x.pdf"),
            ) as paper_mock,
            patch("publisher_download.wiley.download_si", return_value=(False, "")),
        ):
            result = wiley.download(
                "https://onlinelibrary.wiley.com/doi/10.1000/x",
                "<html></html>",
                "10.1000/x",
                task_name="task_a",
                item_index=3,
            )

        self.assertEqual(
            paper_mock.call_args.args[0],
            "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1000/x?download=true"
        )
        self.assertTrue(bool(result.get("paper_ok")))
        self.assertEqual(result.get("paper_file"), "download/task_a/paper/paper_03_10.1000_x.pdf")

    def test_download_returns_failed_for_unsupported_host(self) -> None:
        result = wiley.download("https://example.wiley.com/a", "", "10.1000/x", task_name="t", item_index=1)
        self.assertFalse(bool(result.get("paper_ok")))
        self.assertIn("未支持", str(result.get("failed_reason", "")))

    def test_download_supports_any_onlinelibrary_subdomain(self) -> None:
        with (
            patch("publisher_download.wiley.download_paper_file", return_value=(True, "download/task_b/paper/paper_02_10.1000_x.pdf")) as paper_mock,
            patch("publisher_download.wiley.download_si", return_value=(False, "")),
        ):
            result = wiley.download(
                "https://chemistry-europe.onlinelibrary.wiley.com/doi/10.1000/x",
                "<html></html>",
                "10.1000/x",
                task_name="task_b",
                item_index=2,
            )
        self.assertTrue(bool(result.get("paper_ok")))
        self.assertEqual(
            paper_mock.call_args.args[0],
            "https://chemistry-europe.onlinelibrary.wiley.com/doi/pdfdirect/10.1000/x?download=true",
        )
        self.assertEqual(result.get("paper_download_url"), "https://chemistry-europe.onlinelibrary.wiley.com/doi/pdfdirect/10.1000/x?download=true")

    def test_download_si_delegates_to_site_flow(self) -> None:
        with (
            patch("publisher_download.wiley.extract_first_si_url", return_value="https://onlinelibrary.wiley.com/doi/suppl/10.1000/x/suppl_file/suppl.pdf"),
            patch("publisher_download.wiley.snapshot_download_names", return_value={"old.pdf"}),
            patch("publisher_download.wiley.BrowserController") as browser_cls,
            patch("publisher_download.wiley.move_latest_download_to_task", return_value="download/task_a/si/si_01_10.1000_x.pdf"),
        ):
            ok, si_file = wiley.download_si(
                "https://onlinelibrary.wiley.com/doi/10.1000/x",
                "<html></html>",
                "10.1000/x",
                task_name="task_a",
                item_index=1,
                project_root=None,
            )
        self.assertTrue(ok)
        self.assertEqual(si_file, "download/task_a/si/si_01_10.1000_x.pdf")
        browser_cls.return_value.open_tab.assert_called_once_with(
            "https://onlinelibrary.wiley.com/doi/suppl/10.1000/x/suppl_file/suppl.pdf"
        )


if __name__ == "__main__":
    unittest.main()
