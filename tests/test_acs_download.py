from __future__ import annotations

import unittest
from unittest.mock import patch

from publisher_download import acs


class AcsDownloadTests(unittest.TestCase):
    def test_download_uses_print_download_for_paper(self) -> None:
        with (
            patch("publisher_download.acs.BrowserController") as browser_cls,
            patch("publisher_download.acs.print_download", return_value="download/task_a/paper/paper_02_10.1000_x.pdf") as print_mock,
            patch("publisher_download.acs.download_si", return_value=(False, "")),
        ):
            result = acs.download(
                "https://pubs.acs.org/doi/abs/10.1000/x",
                "<html></html>",
                "10.1000/x",
                task_name="task_a",
                item_index=2,
                project_root="/tmp/project",
            )

        browser_cls.return_value.open_tab.assert_called_once_with(
            "https://pubs.acs.org/doi/pdf/10.1000/x?ref=article_openPDF"
        )
        self.assertEqual(print_mock.call_args.kwargs.get("subfolder"), "paper")
        self.assertTrue(bool(result.get("paper_ok")))
        self.assertEqual(result.get("paper_file"), "download/task_a/paper/paper_02_10.1000_x.pdf")

    def test_download_returns_failed_for_unsupported_host(self) -> None:
        result = acs.download("https://example.com/a", "", "10.1000/x", task_name="t", item_index=1)
        self.assertFalse(bool(result.get("paper_ok")))
        self.assertIn("未支持", str(result.get("failed_reason", "")))

    def test_download_si_uses_print_download(self) -> None:
        html = """<a href="/doi/suppl/10.1000/x/suppl_file/suppl.pdf">SI</a>"""
        with (
            patch("publisher_download.acs.BrowserController") as browser_cls,
            patch("publisher_download.acs.print_download", return_value="download/task_a/si/si_02_10.1000_x.pdf") as print_mock,
        ):
            ok, si_file = acs.download_si(
                "https://pubs.acs.org/doi/abs/10.1000/x",
                html,
                "10.1000/x",
                task_name="task_a",
                item_index=2,
                project_root="/tmp/project",
            )
        self.assertTrue(ok)
        self.assertEqual(si_file, "download/task_a/si/si_02_10.1000_x.pdf")
        browser_cls.return_value.open_tab.assert_called_once_with(
            "https://pubs.acs.org/doi/suppl/10.1000/x/suppl_file/suppl.pdf"
        )
        self.assertEqual(print_mock.call_args.kwargs.get("subfolder"), "si")
        print_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
