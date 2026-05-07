from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.downloader import (
    move_latest_download_to_task,
    print_download,
    resolve_download_root,
    save_html_content,
    snapshot_download_names,
)


class DownloaderTests(unittest.TestCase):
    def test_move_latest_download_to_task_moves_new_file_with_indexed_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            downloads = root / "downloads"
            downloads.mkdir(parents=True, exist_ok=True)
            (downloads / "old.pdf").write_text("old", encoding="utf-8")
            before = snapshot_download_names(downloads)

            source = downloads / "new.pdf"
            source.write_text("new", encoding="utf-8")

            moved = move_latest_download_to_task(
                project_root=root,
                task_name="task_demo",
                subfolder="paper",
                doi="10.1000/a",
                item_index=1,
                prefix="paper",
                before_names=before,
                timeout_sec=0.1,
                poll_sec=0.05,
                download_dir=downloads,
            )

            self.assertEqual(moved, "download/task_demo/paper/paper_01_10.1000_a.pdf")
            self.assertFalse(source.exists())
            self.assertTrue((root / moved).exists())

    def test_resolve_download_root_uses_project_download_when_not_packaged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = resolve_download_root(root)
            self.assertEqual(target.resolve(), (root / "download").resolve())

    def test_print_download_windows_returns_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with (
                patch("core.downloader.gui.hotkey") as hotkey_mock,
                patch("core.downloader.gui.press"),
                patch("core.downloader.gui.write") as write_mock,
                patch("core.downloader.time.sleep", return_value=None),
                patch("core.downloader.snapshot_download_names", return_value={"old.pdf"}) as snapshot_mock,
                patch(
                    "core.downloader.move_latest_download_to_task",
                    return_value="download/task_a/paper/paper_03_10.1000_x.pdf",
                ) as move_mock,
            ):
                saved = print_download(
                    project_root=root,
                    task_name="task_a",
                    subfolder="paper",
                    doi="10.1000/x",
                    item_index=3,
                    prefix="paper",
                )

            self.assertEqual(saved, "download/task_a/paper/paper_03_10.1000_x.pdf")
            self.assertEqual(write_mock.call_args.args[0], "paper_03_10.1000_x.pdf")
            snapshot_mock.assert_called_once()
            move_mock.assert_called_once()
            hotkey_mock.assert_any_call("select_all")

    def test_print_download_si_path_contains_si_subfolder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with (
                patch("core.downloader.gui.hotkey"),
                patch("core.downloader.gui.press"),
                patch("core.downloader.gui.write") as write_mock,
                patch("core.downloader.time.sleep", return_value=None),
                patch("core.downloader.snapshot_download_names", return_value=set()),
                patch(
                    "core.downloader.move_latest_download_to_task",
                    return_value="download/task_a/si/si_03_10.1000_x.pdf",
                ),
            ):
                saved = print_download(
                    project_root=root,
                    task_name="task_a",
                    subfolder="si",
                    doi="10.1000/x",
                    item_index=3,
                    prefix="si",
                )

            self.assertEqual(saved, "download/task_a/si/si_03_10.1000_x.pdf")
            self.assertEqual(write_mock.call_args.args[0], "si_03_10.1000_x.pdf")

    def test_save_html_content_writes_expected_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            content = "<html><body>demo</body></html>"
            saved = save_html_content(
                project_root=root,
                task_name="task_a",
                doi="10.1000/x",
                item_index=3,
                html_content=content,
            )

            self.assertEqual(saved, "download/task_a/html/html_03_10.1000_x.html")
            target = root / saved
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
