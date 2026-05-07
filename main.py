from __future__ import annotations

import argparse
from pathlib import Path

from core.logger import configure_logging, setup_task_logging
from core.task_executor import TaskExecutor
from core.yanzhen import run as run_yanzhen
from gui import launch_app


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AutoPaper launcher")
    parser.add_argument("--run-task", default="", help="run task executor with task csv path/name")
    parser.add_argument("--run-yanzhen", action="store_true", help="run yanzhen helper process")
    parser.add_argument("--parent-pid", type=int, default=0, help="parent pid for yanzhen mode")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.run_yanzhen:
        raise SystemExit(run_yanzhen(parent_pid=max(0, int(args.parent_pid))))
    task = str(args.run_task or "").strip()
    if task:
        configure_logging()
        setup_task_logging(task)
        project_root = Path(__file__).resolve().parent
        TaskExecutor(project_root=project_root).run(task, parent_pid=max(0, int(args.parent_pid)))
        return
    launch_app()


if __name__ == "__main__":
    main()
