from __future__ import annotations

import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import logger as logger_module


class LoggerTests(unittest.TestCase):
    def test_get_log_dir_points_to_logs(self) -> None:
        log_dir = logger_module.get_log_dir()
        self.assertEqual(log_dir.name, "logs")

    def test_get_log_dir_packaged_on_mac(self) -> None:
        with (
            patch("core.logger.sys.frozen", True, create=True),
            patch("core.logger.sys.platform", "darwin"),
        ):
            log_dir = logger_module.get_log_dir()
        expected = Path.home() / "Library" / "Application Support" / "AutoPaper" / "logs"
        self.assertEqual(log_dir, expected)

    def test_get_log_dir_packaged_on_windows(self) -> None:
        with (
            patch("core.logger.sys.frozen", True, create=True),
            patch("core.logger.sys.platform", "win32"),
            patch.dict("core.logger.os.environ", {"LOCALAPPDATA": "/tmp/localapp"}, clear=False),
        ):
            log_dir = logger_module.get_log_dir()
        self.assertEqual(log_dir, Path("/tmp/localapp") / "AutoPaper" / "logs")

    def test_setup_script_logging_creates_log_file(self) -> None:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        root_logger = logging.getLogger()

        with tempfile.TemporaryDirectory() as temp_dir:
            fake_log_dir = Path(temp_dir) / "logs"
            with patch("core.logger.get_log_dir", return_value=fake_log_dir):
                path_text = logger_module.setup_script_logging(__file__, script_name="logger_test")

            log_path = Path(path_text)
            self.assertTrue(log_path.exists())
            self.assertEqual(log_path.parent, fake_log_dir)

        # Restore std streams and logging handler streams to avoid affecting other tests.
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                try:
                    handler.setStream(sys.stderr)
                except Exception:
                    continue


if __name__ == "__main__":
    unittest.main()
