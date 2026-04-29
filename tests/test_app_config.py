from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.app_config import AppConfig


class AppConfigTests(unittest.TestCase):
    def test_read_existing_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text(
                "[app]\nname = \"AutoPaper\"\n"
                "[download]\npage_load_sec = 12.5\n"
                "[flags]\nenabled = true\n"
                "[num]\ncount = 7\n",
                encoding="utf-8",
            )
            cfg = AppConfig(config_path)
            self.assertEqual(cfg.get_str("app.name", default="x"), "AutoPaper")
            self.assertEqual(cfg.get_float("download.page_load_sec", default=60.0), 12.5)
            self.assertEqual(cfg.get_int("num.count", default=1), 7)
            self.assertTrue(cfg.get_bool("flags.enabled", default=False))

    def test_missing_keys_return_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text("[app]\nname = \"AutoPaper\"\n", encoding="utf-8")
            cfg = AppConfig(config_path)
            self.assertEqual(cfg.get_str("none.missing", default="d"), "d")
            self.assertEqual(cfg.get_int("none.missing", default=9), 9)
            self.assertEqual(cfg.get_float("none.missing", default=1.25), 1.25)
            self.assertTrue(cfg.get_bool("none.missing", default=True))

    def test_missing_or_invalid_file_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.toml"
            cfg_missing = AppConfig(missing_path)
            self.assertEqual(cfg_missing.get_str("a.b", default="ok"), "ok")

            invalid_path = Path(temp_dir) / "invalid.toml"
            invalid_path.write_text("not-an-ini-content", encoding="utf-8")
            cfg_invalid = AppConfig(invalid_path)
            self.assertEqual(cfg_invalid.get_int("x.y", default=3), 3)

    def test_type_mismatch_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text("[download]\npage_load_sec = \"fast\"\n", encoding="utf-8")
            cfg = AppConfig(config_path)
            self.assertEqual(cfg.get_float("download.page_load_sec", default=60.0), 60.0)


if __name__ == "__main__":
    unittest.main()
