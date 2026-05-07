from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gui.main_window import MainWindow


class MainWindowTests(unittest.TestCase):
    def test_on_window_close_calls_task_manager_shutdown_and_destroy(self) -> None:
        with (
            patch.object(MainWindow, "__init__", return_value=None),
            patch.object(MainWindow, "destroy") as destroy_mock,
        ):
            window = MainWindow()
            shutdown_called = {"value": False}

            class _TaskManager:
                @staticmethod
                def shutdown() -> None:
                    shutdown_called["value"] = True

            window.task_manager_tab = _TaskManager()  # type: ignore[attr-defined]
            MainWindow._on_window_close(window)

        self.assertTrue(shutdown_called["value"])
        destroy_mock.assert_called_once()

    def test_handle_callback_exception_writes_gui_error_log(self) -> None:
        with (
            patch.object(MainWindow, "__init__", return_value=None),
            patch("gui.main_window.messagebox.showerror") as showerror_mock,
        ):
            window = MainWindow()
            with tempfile.TemporaryDirectory() as temp_dir:
                fake_log_dir = Path(temp_dir) / "logs"
                with patch("gui.main_window.get_log_dir", return_value=fake_log_dir):
                    try:
                        raise RuntimeError("boom")
                    except RuntimeError as exc:
                        MainWindow._handle_callback_exception(window, type(exc), exc, exc.__traceback__)

                log_path = fake_log_dir / "gui_error.log"
                self.assertTrue(log_path.exists())
                content = log_path.read_text(encoding="utf-8")
                self.assertIn("[GUI异常]", content)
                self.assertIn("RuntimeError: boom", content)
                showerror_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
