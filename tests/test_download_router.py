from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
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

    def test_unmatched_domain_marks_failed_with_unsupported_site(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertLogs("publisher_download.router", level="INFO") as cm:
                result = download_by_url(
                    "https://example.com/a",
                    "",
                    "10.1000/x",
                    task_name="task_a",
                    item_index=2,
                    project_root=root,
                )
            self.assertFalse(bool(result.get("paper_ok")))
            self.assertFalse(bool(result.get("si_ok")))
            self.assertEqual(result.get("failed_reason"), "unsupported site")
            self.assertIn("未匹配下载器", "\n".join(cm.output))

            unsupported_csv = root / "unsupported_sites.csv"
            self.assertTrue(unsupported_csv.exists())
            content = unsupported_csv.read_text(encoding="utf-8-sig")
            self.assertIn("time,taskName,doi,host,url", content)
            self.assertIn("task_a,10.1000/x,example.com,https://example.com/a", content)

    def test_unmatched_domain_records_deduplicated_by_host(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            download_by_url(
                "https://example.com/a",
                "",
                "10.1000/x1",
                task_name="task_a",
                project_root=root,
            )
            download_by_url(
                "https://example.com/b",
                "",
                "10.1000/x2",
                task_name="task_b",
                project_root=root,
            )
            download_by_url(
                "https://another.example.org/p",
                "",
                "10.1000/y1",
                task_name="task_c",
                project_root=root,
            )

            unsupported_csv = root / "unsupported_sites.csv"
            self.assertTrue(unsupported_csv.exists())
            lines = [line for line in unsupported_csv.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
            self.assertEqual(len(lines), 3)
            content = "\n".join(lines)
            self.assertIn("task_b,10.1000/x2,example.com,https://example.com/b", content)
            self.assertNotIn("task_a,10.1000/x1,example.com,https://example.com/a", content)
            self.assertIn("task_c,10.1000/y1,another.example.org,https://another.example.org/p", content)


if __name__ == "__main__":
    unittest.main()
