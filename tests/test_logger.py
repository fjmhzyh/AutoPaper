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
