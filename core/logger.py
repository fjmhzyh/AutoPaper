from __future__ import annotations

import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import TextIO


_ACTIVE_LOG_HANDLES: list[TextIO] = []


class TeeStream:
    """将输出同时写入多个流（终端 + 日志文件）。"""

    def __init__(self, *streams: TextIO):
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            try:
                stream.write(data)
            except Exception:
                continue
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:
                continue

    def isatty(self) -> bool:
        for stream in self.streams:
            try:
                if stream.isatty():
                    return True
            except Exception:
                continue
        return False


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_log_dir() -> Path:
    return get_project_root() / "logs"


def get_log_index_path() -> Path:
    return get_log_dir() / "index.csv"


def configure_logging(level: int = logging.INFO, force: bool = False) -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers and not force:
        root_logger.setLevel(level)
        formatter = logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        for handler in root_logger.handlers:
            try:
                handler.setFormatter(formatter)
            except Exception:
                continue
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=force,
    )


def setup_script_logging(
    script_file: str,
    script_name: str = "",
    *,
    task_name: str = "",
    filename: str | None = None,
) -> str:
    """
    为脚本开启日志双写:
    - 控制台正常显示
    - 同时写入项目根目录/logs/<script>_<timestamp>.log
    """
    configure_logging()
    script_path = os.path.abspath(script_file)
    resolved_script_name = script_name or os.path.splitext(os.path.basename(script_path))[0]
    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if filename:
        log_path = log_dir / filename
    else:
        log_path = log_dir / f"{resolved_script_name}_{timestamp}.log"
    log_path = _dedupe_file_path(log_path)

    file_stream = open(log_path, "a", encoding="utf-8", buffering=1)
    _ACTIVE_LOG_HANDLES.append(file_stream)

    sys.stdout = TeeStream(sys.stdout, file_stream)
    sys.stderr = TeeStream(sys.stderr, file_stream)

    # 已经初始化过的 logging StreamHandler 也切到新的 stderr，确保被日志文件捕获
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            try:
                handler.setStream(sys.stderr)
            except Exception:
                continue

    print(f"[日志] 运行日志文件: {log_path}")
    if task_name:
        _append_log_index(task_name, log_path, timestamp)
    return str(log_path)


def setup_task_logging(task_name_or_path: str) -> str:
    task_name = Path(str(task_name_or_path or "").strip()).stem
    timestamp = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    filename = f"{timestamp}.log"
    return setup_script_logging(
        __file__,
        script_name="task_executor",
        task_name=task_name,
        filename=filename,
    )


def _append_log_index(task_name: str, log_path: Path, created_at: str) -> None:
    index_path = get_log_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    exists = index_path.exists()

    with index_path.open("a", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=["taskName", "logFile", "createdAt"])
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "taskName": str(task_name).strip(),
                "logFile": log_path.name,
                "createdAt": str(created_at).strip(),
            }
        )


def _dedupe_file_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    index = 1
    while True:
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1
