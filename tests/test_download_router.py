from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from publisher_download.router import download_by_url


class DownloadRouterTests(unittest.TestCase):
    def test_wiley_domain_routes_to_wiley_downloader(self) -> None:
        with patch("publisher_download.router.wiley.download", return_value={"paper_ok": True, "si_ok": False}) as mock_dl:
            result = download_by_url(
                "https://onlinelibrary.wiley.com/doi/10.1000/x",
                "<html></html>",
                "10.1000/x",
                task_name="task_a",
                item_index=2,
            )
        self.assertTrue(bool(result.get("paper_ok")))
        mock_dl.assert_called_once()

    def test_acs_domain_routes_to_acs_downloader(self) -> None:
        mock_dl = Mock(return_value={"paper_ok": True, "si_ok": False})
        with patch.dict("publisher_download.router.DOWNLOADERS", {"pubs.acs.org": mock_dl}, clear=False):
            result = download_by_url(
                "https://pubs.acs.org/doi/10.1000/x",
                "<html></html>",
                "10.1000/x",
                task_name="task_a",
                item_index=2,
            )
        self.assertTrue(bool(result.get("paper_ok")))
        mock_dl.assert_called_once()

    def test_unmatched_domain_skips_with_success_defaults(self) -> None:
        with self.assertLogs("publisher_download.router", level="INFO") as cm:
            result = download_by_url("https://example.com/a", "", "10.1000/x")
        self.assertTrue(bool(result.get("paper_ok")))
        self.assertTrue(bool(result.get("si_ok")))
        self.assertIn("未匹配下载器", "\n".join(cm.output))


if __name__ == "__main__":
    unittest.main()
