from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from create_rss_task import create_rss_task, extract_strict_dois


class CreateRssTaskTests(unittest.TestCase):
    def test_extract_strict_dois_cleans_tag_and_punctuation(self) -> None:
        text = (
            "abc doi: 10.1088/2057-1976/adf8ee.</dc:identifier>\n"
            "def DOI:10.1000/XYZ123."
        )
        dois = extract_strict_dois(text)
        self.assertEqual(dois, ["10.1088/2057-1976/adf8ee", "10.1000/xyz123"])

    def test_create_rss_task_writes_task_and_statistic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            rss_text = (
                "doi: 10.1000/abc\n"
                "doi: 10.1000/ABC\n"
                "doi: 10.1000/xyz.\n"
                "doi: 10.1000/has space\n"
            )
            fixed_now = datetime(2026, 5, 7, 9, 30)
            with patch("create_rss_task.datetime") as datetime_mock:
                datetime_mock.now.return_value = fixed_now
                datetime_mock.strftime = datetime.strftime
                result = create_rss_task("PCL", rss_text, project_root=root)

            self.assertEqual(result["task_name"], "rss-pcl-0507")
            self.assertEqual(result["total_extracted"], 4)
            self.assertEqual(result["valid_count"], 3)
            self.assertEqual(result["duplicate_count"], 1)
            self.assertEqual(result["invalid_count"], 0)

            task_file = root / "tasks" / "rss-pcl-0507.csv"
            self.assertTrue(task_file.exists())
            with task_file.open("r", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["DOI"], "10.1000/abc")
            self.assertEqual(rows[1]["DOI"], "10.1000/xyz")
            self.assertEqual(rows[2]["DOI"], "10.1000/has")
            self.assertEqual(rows[0]["DownloaStatus"], "")
            self.assertEqual(rows[0]["PaperDownloadUrl"], "")

            stat_file = root / "statistic.csv"
            self.assertTrue(stat_file.exists())
            with stat_file.open("r", encoding="utf-8-sig", newline="") as f:
                stat_rows = list(csv.DictReader(f))
            self.assertEqual(len(stat_rows), 1)
            self.assertEqual(stat_rows[0]["taskName"], "rss-pcl-0507")
            self.assertEqual(stat_rows[0]["status"], "pending")
            self.assertEqual(stat_rows[0]["totalCount"], "3")

    def test_create_rss_task_name_dedup_with_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks = root / "tasks"
            tasks.mkdir(parents=True, exist_ok=True)
            (tasks / "rss-pcl-0507.csv").write_text("DOI\n", encoding="utf-8")

            fixed_now = datetime(2026, 5, 7, 9, 30)
            with patch("create_rss_task.datetime") as datetime_mock:
                datetime_mock.now.return_value = fixed_now
                datetime_mock.strftime = datetime.strftime
                result = create_rss_task("pcl", "doi: 10.1000/a", project_root=root)

            self.assertEqual(result["task_name"], "rss-pcl-0507-02")
            self.assertTrue((tasks / "rss-pcl-0507-02.csv").exists())

    def test_create_rss_task_invalid_params(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "keyword不能为空"):
                create_rss_task("", "doi: 10.1000/a", project_root=root)
            with self.assertRaisesRegex(ValueError, "rss_text不能为空"):
                create_rss_task("pcl", "", project_root=root)
            with self.assertRaisesRegex(ValueError, "未提取到DOI"):
                create_rss_task("pcl", "no doi here", project_root=root)


if __name__ == "__main__":
    unittest.main()
