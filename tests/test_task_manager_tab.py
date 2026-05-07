from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from gui.task_manager_tab import TaskManagerTab


class TaskManagerTabTests(unittest.TestCase):
    def test_build_executor_command_uses_worker_when_frozen(self) -> None:
        tab = TaskManagerTab.__new__(TaskManagerTab)
        task_path = Path("/tmp/demo.csv")
        with (
            patch.object(sys, "frozen", True, create=True),
            patch("gui.task_manager_tab.sys.executable", "/Applications/AutoPaper.app/Contents/MacOS/AutoPaper"),
            patch("gui.task_manager_tab.os.getpid", return_value=4321),
            patch("pathlib.Path.exists", return_value=True),
        ):
            cmd = TaskManagerTab._build_executor_command(tab, task_path)

        self.assertEqual(cmd[0], "/Applications/AutoPaper.app/Contents/MacOS/AutoPaperWorker")
        self.assertEqual(cmd[1:], ["--run-task", "/tmp/demo.csv", "--parent-pid", "4321"])

    def test_on_create_rss_task_clicked_calls_create_and_refresh(self) -> None:
        tab = TaskManagerTab.__new__(TaskManagerTab)
        tab.project_root = Path("/tmp/project")
        tab.keyword_entry = SimpleNamespace(get=lambda: "pcl")
        tab.on_tasks_changed = None
        tab.rss_text_provider = lambda _k: "doi: 10.1000/a"
        tab._load_rows = lambda: None  # type: ignore[method-assign]

        with (
            patch("gui.task_manager_tab.create_rss_task", return_value={"task_name": "rss-pcl-0507", "total_extracted": 10, "valid_count": 8, "duplicate_count": 1, "invalid_count": 1}) as create_mock,
            patch("gui.task_manager_tab.messagebox.showinfo") as info_mock,
            patch("gui.task_manager_tab.messagebox.showerror") as error_mock,
        ):
            TaskManagerTab._on_create_rss_task_clicked(tab)

        create_mock.assert_called_once()
        info_mock.assert_called_once()
        error_mock.assert_not_called()

    def test_on_create_rss_task_clicked_empty_keyword(self) -> None:
        tab = TaskManagerTab.__new__(TaskManagerTab)
        tab.keyword_entry = SimpleNamespace(get=lambda: "请输入关键词")

        with (
            patch("gui.task_manager_tab.messagebox.showwarning") as warning_mock,
            patch("gui.task_manager_tab.create_rss_task") as create_mock,
        ):
            TaskManagerTab._on_create_rss_task_clicked(tab)

        warning_mock.assert_called_once()
        create_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
