
from __future__ import annotations

import os
import re
import shutil
import sys
import time
import logging
from pathlib import Path

from core import gui

PARTIAL_SUFFIXES = {".crdownload", ".part", ".download", ".tmp"}
ALLOWED_DOWNLOAD_SUFFIXES = {".pdf", ".zip", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".html", ".htm"}
logger = logging.getLogger(__name__)


def default_download_dir() -> Path:
    return Path.home() / "Downloads"


def snapshot_download_names(download_dir: str | Path | None = None) -> set[str]:
    folder = Path(download_dir) if download_dir else default_download_dir()
    if not folder.exists():
        return set()
    return {item.name for item in folder.iterdir() if item.is_file()}


def move_latest_download_to_task(
    *,
    project_root: str | Path,
    task_name: str,
    subfolder: str,
    doi: str,
    item_index: int,
    prefix: str,
    before_names: set[str] | None = None,
    timeout_sec: float = 60.0,
    poll_sec: float = 0.5,
    download_dir: str | Path | None = None,
) -> str | None:
    folder = Path(download_dir) if download_dir else default_download_dir()
    if not folder.exists() or not folder.is_dir():
        return None

    previous = before_names or set()
    deadline = time.time() + max(0.0, float(timeout_sec))
    source = _wait_new_file(folder, previous, deadline, max(0.1, float(poll_sec)))
    if source is None:
        return None

    root = Path(project_root).resolve()
    target_dir = resolve_download_root(root) / str(task_name).strip() / str(subfolder).strip()
    target_dir.mkdir(parents=True, exist_ok=True)

    suffix = _normalize_download_suffix(source.suffix)
    safe_doi = _normalize_doi_for_name(doi)
    base_name = f"{prefix}_{max(1, int(item_index)):02d}_{safe_doi}{suffix}"
    target = _dedupe_target(target_dir, base_name)
    shutil.move(str(source), str(target))

    return _to_output_path(root, target)


def print_download(
    *,
    project_root: str | Path,
    task_name: str,
    subfolder: str,
    doi: str,
    item_index: int,
    prefix: str,
) -> str | None:
    root = Path(project_root).resolve()
    target_dir = resolve_download_root(root) / str(task_name).strip() / str(subfolder).strip()
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_doi = _normalize_doi_for_name(doi)
    filename = f"{prefix}_{max(1, int(item_index)):02d}_{safe_doi}.pdf"
    target_name = _dedupe_target(target_dir, filename).name
    before_names = snapshot_download_names()

    time.sleep(20)

    gui.hotkey("print_page")
    time.sleep(5)
    gui.press("enter")
    time.sleep(5)
    gui.hotkey("select_all")
    time.sleep(1)
    _paste_text(target_name)

    time.sleep(2)
    gui.press("enter")
    time.sleep(1)
    gui.press("enter", presses=3, interval=0.2)
    gui.hotkey("close_tab")
    moved_path = move_latest_download_to_task(
        project_root=root,
        task_name=task_name,
        subfolder=subfolder,
        doi=doi,
        item_index=item_index,
        prefix=prefix,
        before_names=before_names,
        timeout_sec=30.0,
        poll_sec=0.5,
    )
    if moved_path:
        logger.info(f"[论文下载] 打印保存后已搬运到任务目录 - {moved_path}")
    else:
        logger.warning("[论文下载] 打印保存后搬运失败 - 未检测到新下载文件")
    return moved_path


def resolve_download_root(project_root: str | Path) -> Path:
    root = Path(project_root).resolve()
    if getattr(sys, "frozen", False):
        return _packaged_download_root()
    return root / "download"


def save_html_content(
    *,
    project_root: str | Path,
    task_name: str,
    doi: str,
    item_index: int,
    html_content: str,
    prefix: str = "html",
) -> str | None:
    root = Path(project_root).resolve()
    target_dir = resolve_download_root(root) / str(task_name).strip() / "html"
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_doi = _normalize_doi_for_name(doi)
    filename = f"{prefix}_{max(1, int(item_index)):02d}_{safe_doi}.html"
    target = _dedupe_target(target_dir, filename)
    target.write_text(str(html_content or ""), encoding="utf-8")
    if not target.exists():
        return None
    return _to_output_path(root, target)


def _wait_new_file(folder: Path, previous: set[str], deadline: float, poll_sec: float) -> Path | None:
    while time.time() <= deadline:
        candidates = []
        for item in folder.iterdir():
            if not item.is_file():
                continue
            if item.name in previous:
                continue
            if item.suffix.lower() in PARTIAL_SUFFIXES:
                continue
            candidates.append(item)
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)
        time.sleep(poll_sec)
    return None


def _wait_file_exists(path: Path, timeout_sec: float, poll_sec: float) -> bool:
    deadline = time.time() + max(0.0, float(timeout_sec))
    wait_sec = max(0.1, float(poll_sec))
    while time.time() <= deadline:
        if path.exists() and path.is_file():
            return True
        time.sleep(wait_sec)
    return False


def _normalize_doi_for_name(doi: str) -> str:
    text = str(doi or "").strip()
    if not text:
        return "unknown_doi"
    normalized = re.sub(r"[^0-9A-Za-z._-]+", "_", text)
    normalized = normalized.strip("._-")
    return normalized.lower() or "unknown_doi"


def _paste_text(text: str) -> None:
    import pyperclip  # type: ignore

    pyperclip.copy(str(text or ""))
    gui.hotkey("paste")


def _normalize_download_suffix(raw_suffix: str | None) -> str:
    suffix = str(raw_suffix or "").strip().lower()
    if not suffix:
        return ".pdf"
    if not suffix.startswith("."):
        suffix = f".{suffix}"
    if suffix in ALLOWED_DOWNLOAD_SUFFIXES:
        return suffix
    return ".pdf"


def _dedupe_target(folder: Path, filename: str) -> Path:
    target = folder / filename
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    index = 1
    while True:
        candidate = folder / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _packaged_download_root() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "AutoPaper" / "download"
    if sys.platform.startswith("win"):
        local_app = os.environ.get("LOCALAPPDATA", "")
        base = Path(local_app) if local_app else (Path.home() / "AppData" / "Local")
        return base / "AutoPaper" / "download"
    return Path.home() / ".autopaper" / "download"


def _to_output_path(project_root: Path, target: Path) -> str:
    try:
        return str(target.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        return str(target).replace("\\", "/")
