from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.task_executor import TaskExecutor


class TaskExecutorTests(unittest.TestCase):
    def _prepare_task_env(self, temp_dir: str, task_name: str, csv_rows: str) -> tuple[Path, Path]:
        root = Path(temp_dir)
        tasks_dir = root / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_path = tasks_dir / f"{task_name}.csv"
        task_path.write_text(
            "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl\n"
            + csv_rows,
            encoding="utf-8",
        )
        statistic_path = root / "statistic.csv"
        statistic_path.write_text(
            (
                "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                f"{task_name},pending,1,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
            ),
            encoding="utf-8",
        )
        return root, task_path

    def test_run_updates_task_and_statistic_with_stub_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            task_path = tasks_dir / "task_demo.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl\n"
                    "10.1000/a,,,,,,,,\n"
                    "10.1000/b,,,,,,,,\n"
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
            self.assertIn("10.1000/a,failed", task_content)
            self.assertIn("unsupported site", task_content)
            self.assertIn("10.1000/b,failed", task_content)
            self.assertIn("网页无法打开", task_content)

            stat_content = statistic_path.read_text(encoding="utf-8-sig")
            self.assertIn("task_demo,finished,2,0,2", stat_content)

    def test_run_skips_already_finished_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            task_path = tasks_dir / "task_done.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl\n"
                    "10.1000/a,success,,,,,,,\n"
                    "10.1000/b,failed,,,,,,,\n"
                    "10.1000/c,,,,,,,,\n"
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
                    "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl\n"
                    "10.1000/a,,,,,,,,\n"
                    "10.1000/b,,,,,,,,\n"
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
            self.assertIn("10.1000/b,failed", content)
            self.assertIn("unsupported site", content)

    def test_run_writes_absolute_paths_for_paper_and_si_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            task_path = tasks_dir / "task_path.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl\n"
                    "10.1000/a,,,,,,,,\n"
                ),
                encoding="utf-8",
            )
            (root / "statistic.csv").write_text(
                (
                    "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                    "task_path,pending,1,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
                ),
                encoding="utf-8",
            )

            executor = TaskExecutor(project_root=root)
            with (
                patch("core.task_executor.resolve_doi_url", return_value="https://publisher.com/a"),
                patch("core.task_executor.login_by_url", return_value=True),
                patch("core.task_executor.get_html_content", return_value="<html>a</html>"),
                patch(
                    "core.task_executor.download_by_url",
                    return_value={
                        "paper_ok": True,
                        "si_ok": True,
                        "paper_download_url": "https://publisher.com/pdf",
                        "paper_file": "download/task_path/paper/paper_01_10.1000_a.pdf",
                        "si_file": "download/task_path/si/si_01_10.1000_a.pdf",
                        "failed_reason": "",
                    },
                ),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                executor.run("task_path")

            content = task_path.read_text(encoding="utf-8-sig")
            self.assertIn(str((root / "download/task_path/paper/paper_01_10.1000_a.pdf").resolve()), content)
            self.assertIn(str((root / "download/task_path/si/si_01_10.1000_a.pdf").resolve()), content)

    def test_resume_uses_absolute_item_index_for_naming(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)

            rows = [
                "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl",
            ]
            for i in range(1, 21):
                rows.append(f"10.1000/{i},success,,,,,,,")
            rows.append("10.1000/21,,,,,,,,")
            task_path = tasks_dir / "task_resume.csv"
            task_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            (root / "statistic.csv").write_text(
                (
                    "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                    "task_resume,pending,21,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
                ),
                encoding="utf-8",
            )

            executor = TaskExecutor(project_root=root)
            captured_item_index: dict[str, int] = {}

            def fake_download(*_args, **kwargs):
                captured_item_index["value"] = int(kwargs.get("item_index", -1))
                return {
                    "paper_ok": True,
                    "si_ok": False,
                    "paper_download_url": "",
                    "paper_file": "",
                    "si_file": "",
                    "failed_reason": "",
                }

            with (
                patch("core.task_executor.resolve_doi_url", return_value="https://pubs.acs.org/doi/10.1000/21"),
                patch("core.task_executor.login_by_url", return_value=True),
                patch("core.task_executor.get_html_content", return_value="<html></html>"),
                patch("core.task_executor.download_by_url", side_effect=fake_download),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                executor.run("task_resume")

            self.assertEqual(captured_item_index.get("value"), 21)

    def test_run_starts_and_stops_yanzhen_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _ = self._prepare_task_env(temp_dir, "task_proc", "10.1000/a,,,,,,,,\n")
            fake_proc = SimpleNamespace(pid=12345, poll=lambda: None, terminate=lambda: None, wait=lambda timeout=0: None, kill=lambda: None)
            executor = TaskExecutor(project_root=root)

            with (
                patch("core.task_executor.subprocess.Popen", return_value=fake_proc) as popen_mock,
                patch("core.task_executor.BrowserController") as browser_cls,
                patch("core.task_executor.loop_close_tabs", return_value=True),
                patch("core.task_executor.resolve_doi_url", return_value="https://publisher.com/a"),
                patch("core.task_executor.login_by_url", return_value=True),
                patch("core.task_executor.get_html_content", return_value="<html>a</html>"),
                patch("core.task_executor.download_by_url", return_value={"paper_ok": True, "si_ok": False, "failed_reason": ""}),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                executor.run("task_proc")

            browser_cls.return_value.open_tab.assert_called_once_with("https://www.baidu.com")
            called_with_yanzhen = any("-m" in call.args[0] and "core.yanzhen" in call.args[0] for call in popen_mock.call_args_list)
            self.assertTrue(called_with_yanzhen)
            self.assertIsNone(executor._yanzhen_proc)

    def test_run_starts_yanzhen_with_main_entry_when_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _ = self._prepare_task_env(temp_dir, "task_proc_frozen", "10.1000/a,,,,,,,,\n")
            fake_proc = SimpleNamespace(pid=22345, poll=lambda: None, terminate=lambda: None, wait=lambda timeout=0: None, kill=lambda: None)
            executor = TaskExecutor(project_root=root)
            original_has_frozen = hasattr(sys, "frozen")
            original_frozen = getattr(sys, "frozen", None)

            with (
                patch("core.task_executor.subprocess.Popen", return_value=fake_proc) as popen_mock,
                patch("core.task_executor.BrowserController"),
                patch("core.task_executor.loop_close_tabs", return_value=True),
                patch("core.task_executor.resolve_doi_url", return_value="https://publisher.com/a"),
                patch("core.task_executor.login_by_url", return_value=True),
                patch("core.task_executor.get_html_content", return_value="<html>a</html>"),
                patch("core.task_executor.download_by_url", return_value={"paper_ok": True, "si_ok": False, "failed_reason": ""}),
                patch("core.task_executor.time.sleep", return_value=None),
                patch.object(sys, "frozen", True, create=True),
                patch("core.task_executor.sys.executable", "/Applications/AutoPaper.app/Contents/MacOS/AutoPaper"),
                patch("pathlib.Path.exists", return_value=True),
            ):
                executor.run("task_proc_frozen")

            called_with_main_entry = any("--run-yanzhen" in call.args[0] for call in popen_mock.call_args_list)
            self.assertTrue(called_with_main_entry)
            used_worker = any(call.args[0][0].endswith("AutoPaperWorker") for call in popen_mock.call_args_list if "--run-yanzhen" in call.args[0])
            self.assertTrue(used_worker)
            if original_has_frozen:
                setattr(sys, "frozen", original_frozen)
            elif hasattr(sys, "frozen"):
                delattr(sys, "frozen")

    def test_run_raises_when_yanzhen_quick_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _ = self._prepare_task_env(temp_dir, "task_quit", "10.1000/a,,,,,,,,\n")
            fake_proc = SimpleNamespace(pid=12346, poll=lambda: 1, terminate=lambda: None, wait=lambda timeout=0: None, kill=lambda: None)
            executor = TaskExecutor(project_root=root)

            with (
                patch("core.task_executor.subprocess.Popen", return_value=fake_proc),
                patch("core.task_executor.resolve_doi_url") as resolve_mock,
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                with self.assertRaises(RuntimeError):
                    executor.run("task_quit")

            resolve_mock.assert_not_called()
            self.assertIsNone(executor._yanzhen_proc)

    def test_run_still_stops_yanzhen_when_main_flow_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root, _ = self._prepare_task_env(temp_dir, "task_err", "10.1000/a,,,,,,,,\n")
            fake_proc = SimpleNamespace(pid=12347, poll=lambda: None, terminate=lambda: None, wait=lambda timeout=0: None, kill=lambda: None)
            executor = TaskExecutor(project_root=root)

            with (
                patch("core.task_executor.subprocess.Popen", return_value=fake_proc),
                patch("core.task_executor.resolve_doi_url", side_effect=RuntimeError("boom")),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                with self.assertRaises(RuntimeError):
                    executor.run("task_err")

            self.assertIsNone(executor._yanzhen_proc)

    def test_run_opens_baidu_and_calls_loop_close_tabs_each_round(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            task_path = tasks_dir / "task_tabs.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl\n"
                    "10.1000/a,,,,,,,,\n"
                    "10.1000/b,,,,,,,,\n"
                ),
                encoding="utf-8",
            )
            (root / "statistic.csv").write_text(
                (
                    "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                    "task_tabs,pending,2,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
                ),
                encoding="utf-8",
            )

            fake_browser = SimpleNamespace(open_tab=lambda _url: None)
            executor = TaskExecutor(project_root=root)
            with (
                patch("core.task_executor.BrowserController", return_value=fake_browser) as browser_cls,
                patch("core.task_executor.loop_close_tabs", return_value=True) as close_tabs_mock,
                patch("core.task_executor.resolve_doi_url", side_effect=["https://publisher.com/a", "https://publisher.com/b"]),
                patch("core.task_executor.login_by_url", return_value=True),
                patch("core.task_executor.get_html_content", return_value="<html></html>"),
                patch("core.task_executor.download_by_url", return_value={"paper_ok": False, "si_ok": False, "failed_reason": "unsupported site"}),
                patch("core.task_executor.time.sleep", return_value=None),
            ):
                executor.run("task_tabs")

            browser_cls.assert_called_once()
            self.assertEqual(close_tabs_mock.call_count, 2)

    def test_run_stops_when_parent_pid_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tasks_dir = root / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            task_path = tasks_dir / "task_parent.csv"
            task_path.write_text(
                (
                    "DOI,DownloaStatus,SIDownloadStatus,failedReason,PublisherUrl,PaperFile,SIFile,HtmlFile,PaperDownloadUrl\n"
                    "10.1000/a,,,,,,,,\n"
                    "10.1000/b,,,,,,,,\n"
                ),
                encoding="utf-8",
            )
            (root / "statistic.csv").write_text(
                (
                    "taskName,status,totalCount,paperSuccessCount,paperFailedCount,siSuccessCount,createTime,updateTime\n"
                    "task_parent,pending,2,0,0,0,2026-01-01 00:00,2026-01-01 00:00\n"
                ),
                encoding="utf-8",
            )

            executor = TaskExecutor(project_root=root)
            with (
                patch("core.task_executor.BrowserController"),
                patch("core.task_executor.loop_close_tabs", return_value=True),
                patch("core.task_executor.resolve_doi_url", return_value="https://publisher.com/a") as resolve_mock,
                patch("core.task_executor.login_by_url", return_value=True),
                patch("core.task_executor.get_html_content", return_value="<html></html>"),
                patch("core.task_executor.download_by_url", return_value={"paper_ok": False, "si_ok": False, "failed_reason": "unsupported site"}),
                patch("core.task_executor.time.sleep", return_value=None),
                patch.object(TaskExecutor, "_is_parent_alive", side_effect=[True, False, False]),
            ):
                executor.run("task_parent", parent_pid=99999)

            resolve_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
