from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from core.app_config import get_config
    from core.csv_manager import CSVManager
    from core.logger import configure_logging
    from publisher_login.router import login_by_url
    from core.resolve_doi_url import resolve_doi_url
    from core.task_manager import STATISTIC_FIELDNAMES
    from core.utils import get_html_content
except ModuleNotFoundError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.app_config import get_config
    from core.csv_manager import CSVManager
    from core.logger import configure_logging
    from publisher_login.router import login_by_url
    from core.resolve_doi_url import resolve_doi_url
    from core.task_manager import STATISTIC_FIELDNAMES
    from core.utils import get_html_content


logger = logging.getLogger(__name__)

TASK_FIELD_ALIASES = {
    "doi": ["DOI"],
    "status": ["DownloaStatus"],
    "failed_reason": ["failedReason", "FailedReason"],
    "paper_file": ["PaperFile"],
    "si_file": ["SIFile"],
    "html_file": ["htmlFile", "HtmlFile"],
}


class TaskExecutor:
    def __init__(self, project_root: str | Path | None = None):
        self.project_root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        self.tasks_dir = self.project_root / "tasks"
        self.statistic_path = self._resolve_statistic_path()
        self.interval_sec = max(
            0.0,
            get_config().get_float("download.doi_download_interval_sec", default=30.0),
        )

    def run(self, task_name_or_path: str) -> None:
        task_path = self._resolve_task_path(task_name_or_path)
        task_name = task_path.stem
        task_csv = CSVManager(task_path)
        rows = task_csv.get_all()
        if not rows:
            logger.warning(f"[任务获取] 任务名-{task_name} DOI总数-0条")
            self._update_statistic(task_name, status="finished", total_count=0, success_count=0, failed_count=0)
            return

        fields = self._resolve_task_fields(task_csv.fieldnames)
        pending = self._collect_pending_rows(rows, fields)
        total = len(pending)
        logger.info(f"[任务获取] 任务名-{task_name} DOI总数-{total}条")

        self._update_statistic(task_name, status="running", total_count=total, success_count=0, failed_count=0)

        for index, row in enumerate(pending, start=1):
            doi = row.get(fields["doi"], "").strip()
            logger.info(f"[任务进度] 共{total}条，当前第{index}条: DOI - {doi}")

            resolved_url = resolve_doi_url(doi)
            if not resolved_url:
                task_csv.update_by(
                    fields["doi"],
                    doi,
                    {
                        fields["status"]: "failed",
                        fields["failed_reason"]: "网页无法打开",
                    },
                )
                logger.info(f"[执行结果] 第{index}条执行结束：论文下载-失败， si下载-失败")
                if index < total:
                    logger.info(f"[执行间隔] 等待{int(self.interval_sec)}秒，开始执行第{index + 1}条")
                    time.sleep(self.interval_sec)
                continue

            login_ok = True
            login_ok = login_by_url(resolved_url)
            html_ok = True
            html_content = ""
            if login_ok:
                logger.info("[源码获取] 正在获取网页源码")
                try:
                    html_content = get_html_content()
                except Exception as exc:
                    html_ok = False
                    logger.warning(f"[源码获取] 获取网页源码失败: {exc}")
            else:
                logger.info("[源码获取] 未获取到可用地址或登录失败，跳过源码获取")
            self.publisher_download_stub(resolved_url or "", html_content, doi)
            self.check_result_stub(doi)

            ok = bool(login_ok) and bool(html_ok)
            status_text = "success" if ok else "failed"
            updates = {
                fields["status"]: status_text,
                fields["failed_reason"]: "" if ok else "处理失败",
                fields["paper_file"]: "",
                fields["si_file"]: "",
                fields["html_file"]: "",
            }
            task_csv.update_by(fields["doi"], doi, updates)

            paper_status = "成功" if ok else "失败"
            si_status = "成功" if ok else "失败"
            logger.info(f"[执行结果] 第{index}条执行结束：论文下载-{paper_status}， si下载-{si_status}")

            if index < total:
                logger.info(f"[执行间隔] 等待{int(self.interval_sec)}秒，开始执行第{index + 1}条")
                time.sleep(self.interval_sec)

        rows_after = task_csv.get_all()
        success_count = self._count_status(rows_after, fields["status"], "success")
        failed_count = self._count_status(rows_after, fields["status"], "failed")
        self._update_statistic(
            task_name,
            status="finished",
            total_count=total,
            success_count=success_count,
            failed_count=failed_count,
        )

    def publisher_download_stub(self, _url: str, _html: str, _doi: str) -> dict[str, Any]:
        logger.info("[论文下载] 正在执行论文下载 - 占位实现")
        logger.info("[资料下载] 正在执行si下载 - 占位实现")
        return {"paper_ok": False, "si_ok": False, "paper_file": "", "si_file": ""}

    def check_result_stub(self, _doi: str) -> dict[str, Any]:
        return {"paper_ok": False, "si_ok": False}

    def _resolve_task_path(self, task_name_or_path: str) -> Path:
        raw = str(task_name_or_path or "").strip()
        if not raw:
            raise ValueError("task is required")

        candidate = Path(raw)
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

        name = candidate.name
        if not name.lower().endswith(".csv"):
            name = f"{name}.csv"
        task_path = (self.tasks_dir / name).resolve()
        if not task_path.exists() or not task_path.is_file():
            raise FileNotFoundError(f"Task file not found: {task_path}")
        return task_path

    @staticmethod
    def _resolve_task_fields(fieldnames: list[str]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for target, aliases in TASK_FIELD_ALIASES.items():
            selected = TaskExecutor._select_field(fieldnames, aliases)
            mapping[target] = selected if selected else aliases[0]
        if not mapping["doi"]:
            raise ValueError("Task file missing DOI field")
        return mapping

    @staticmethod
    def _select_field(fieldnames: list[str], candidates: list[str]) -> str | None:
        lowered = {name.lower(): name for name in fieldnames}
        for item in candidates:
            key = item.lower()
            if key in lowered:
                return lowered[key]
        return None

    @staticmethod
    def _collect_pending_rows(rows: list[dict[str, str]], fields: dict[str, str]) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        doi_key = fields["doi"]
        status_key = fields["status"]
        for row in rows:
            doi = str(row.get(doi_key, "") or "").strip()
            if not doi:
                continue
            status = str(row.get(status_key, "") or "").strip().lower()
            if status in {"success", "failed"}:
                continue
            result.append(row)
        return result

    @staticmethod
    def _count_status(rows: list[dict[str, str]], status_field: str, expected: str) -> int:
        target = expected.lower()
        count = 0
        for row in rows:
            status = str(row.get(status_field, "") or "").strip().lower()
            if status == target:
                count += 1
        return count

    def _resolve_statistic_path(self) -> Path:
        preferred = [
            self.project_root / "statistic.csv",
            self.project_root / "statistic.csv ",
        ]
        for item in preferred:
            if item.exists():
                return item

        existing = sorted(self.project_root.glob("statistic.csv*"))
        if existing:
            return existing[0]
        return preferred[0]

    def _update_statistic(
        self,
        task_name: str,
        *,
        status: str,
        total_count: int,
        success_count: int,
        failed_count: int,
    ) -> None:
        manager = CSVManager(self.statistic_path, fieldnames=STATISTIC_FIELDNAMES)
        rows = manager.get_all()
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M")

        index = self._find_stat_row_index(rows, task_name)
        if index < 0:
            rows.append(
                {
                    "taskName": task_name,
                    "status": status,
                    "totalCount": str(total_count),
                    "paperSuccessCount": str(success_count),
                    "paperFailedCount": str(failed_count),
                    "siSuccessCount": "0",
                    "createTime": now_text,
                    "updateTime": now_text,
                }
            )
        else:
            current = rows[index]
            create_time = current.get("createTime", "").strip() or now_text
            rows[index] = {
                "taskName": current.get("taskName", "").strip() or task_name,
                "status": status,
                "totalCount": str(total_count),
                "paperSuccessCount": str(success_count),
                "paperFailedCount": str(failed_count),
                "siSuccessCount": current.get("siSuccessCount", "").strip() or "0",
                "createTime": create_time,
                "updateTime": now_text,
            }

        manager.rows = rows
        manager.save()

    @staticmethod
    def _find_stat_row_index(rows: list[dict[str, str]], task_name: str) -> int:
        target = Path(task_name).stem.lower()
        for idx, row in enumerate(rows):
            name = Path(str(row.get("taskName", "") or "").strip()).stem.lower()
            if name == target:
                return idx
        return -1


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute one task csv by DOI workflow.")
    parser.add_argument("--task", required=True, help="task name or task csv path")
    return parser


if __name__ == "__main__":
    configure_logging()
    args = _build_arg_parser().parse_args()
    executor = TaskExecutor()
    executor.run(args.task)
