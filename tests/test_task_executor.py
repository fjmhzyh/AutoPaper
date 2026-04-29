from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.task_executor import TaskExecutor


class TaskExecutorTests(unittest.TestCase):
    def test_run_updates_task_and_statistic_with_stub_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            task_path = tasks_dir / "task_demo.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,PaperFile,SIFile,htmlFile\n"
                    "10.1000/a,,,\n"
                    "10.1000/b,,,\n"
                ),
                encoding="utf-8",
            )

            statistic_path = root / "statistic.csv"
            statistic_path.write_text(
                (
                    "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                    "task_demo,pending,2,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
                ),
                encoding="utf-8",
            )

            executor = TaskExecutor(project_root=root)

            with (
                patch("core.task_executor.resolve_doi_url", side_effect=["https://publisher.com/a", None]) as resolve_mock,
                patch("core.task_executor.login_by_url", return_value=True) as login_mock,
                patch("core.task_executor.get_html_content", return_value="<html>a</html>"),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                executor.run("task_demo")

            self.assertEqual(resolve_mock.call_count, 2)
            self.assertEqual(resolve_mock.call_args_list[0].args[0], "10.1000/a")
            self.assertEqual(resolve_mock.call_args_list[1].args[0], "10.1000/b")
            login_mock.assert_called_once_with("https://publisher.com/a")

            task_content = task_path.read_text(encoding="utf-8-sig")
            self.assertIn("10.1000/a,success", task_content)
            self.assertIn("10.1000/b,failed", task_content)
            self.assertIn("网页无法打开", task_content)

            stat_content = statistic_path.read_text(encoding="utf-8-sig")
            self.assertIn("task_demo,finished,2,1,1", stat_content)

    def test_run_skips_already_finished_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            task_path = tasks_dir / "task_done.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,PaperFile,SIFile,htmlFile\n"
                    "10.1000/a,success,,,\n"
                    "10.1000/b,failed,,,\n"
                    "10.1000/c,,,\n"
                ),
                encoding="utf-8",
            )

            statistic_path = root / "statistic.csv"
            statistic_path.write_text(
                (
                    "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                    "task_done,pending,3,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
                ),
                encoding="utf-8",
            )

            executor = TaskExecutor(project_root=root)
            with (
                patch("core.task_executor.resolve_doi_url", return_value="https://publisher.com/c") as resolve_mock,
                patch("core.task_executor.login_by_url", return_value=True),
                patch("core.task_executor.get_html_content", return_value="<html>c</html>"),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                executor.run("task_done")

            resolve_mock.assert_called_once_with("10.1000/c")

    def test_login_failure_marks_current_doi_failed_and_continue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            task_path = tasks_dir / "task_login.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,PaperFile,SIFile,htmlFile\n"
                    "10.1000/a,,,\n"
                    "10.1000/b,,,\n"
                ),
                encoding="utf-8",
            )
            (root / "statistic.csv").write_text(
                (
                    "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                    "task_login,pending,2,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
                ),
                encoding="utf-8",
            )

            executor = TaskExecutor(project_root=root)
            with (
                patch("core.task_executor.resolve_doi_url", side_effect=["https://onlinelibrary.wiley.com/a", "https://publisher.com/b"]),
                patch("core.task_executor.login_by_url", side_effect=[False, True]),
                patch("core.task_executor.get_html_content", return_value="<html>x</html>"),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                executor.run("task_login")

            content = task_path.read_text(encoding="utf-8-sig")
            self.assertIn("10.1000/a,failed", content)
            self.assertIn("10.1000/b,success", content)


if __name__ == "__main__":
    unittest.main()
