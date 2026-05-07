from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

import main


class MainEntryTests(unittest.TestCase):
    def test_main_launches_gui_by_default(self) -> None:
        with (
            patch.object(sys, "argv", ["main.py"]),
            patch("main.launch_app") as launch_mock,
            patch("main.TaskExecutor") as executor_cls,
            patch("main.run_yanzhen") as yanzhen_mock,
        ):
            main.main()

        launch_mock.assert_called_once()
        executor_cls.assert_not_called()
        yanzhen_mock.assert_not_called()

    def test_main_runs_task_executor_when_run_task_provided(self) -> None:
        with (
            patch.object(sys, "argv", ["main.py", "--run-task", "tasks/demo.csv", "--parent-pid", "456"]),
            patch("main.launch_app") as launch_mock,
            patch("main.TaskExecutor") as executor_cls,
            patch("main.configure_logging") as configure_logging_mock,
            patch("main.setup_task_logging") as setup_task_logging_mock,
            patch("main.run_yanzhen") as yanzhen_mock,
        ):
            executor = executor_cls.return_value
            main.main()

        launch_mock.assert_not_called()
        yanzhen_mock.assert_not_called()
        configure_logging_mock.assert_called_once()
        setup_task_logging_mock.assert_called_once_with("tasks/demo.csv")
        executor_cls.assert_called_once()
        executor.run.assert_called_once_with("tasks/demo.csv", parent_pid=456)

    def test_main_runs_yanzhen_when_flag_provided(self) -> None:
        with (
            patch.object(sys, "argv", ["main.py", "--run-yanzhen", "--parent-pid", "123"]),
            patch("main.launch_app") as launch_mock,
            patch("main.TaskExecutor") as executor_cls,
            patch("main.run_yanzhen", return_value=0) as yanzhen_mock,
        ):
            with self.assertRaises(SystemExit) as cm:
                main.main()

        self.assertEqual(cm.exception.code, 0)
        yanzhen_mock.assert_called_once_with(parent_pid=123)
        launch_mock.assert_not_called()
        executor_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
