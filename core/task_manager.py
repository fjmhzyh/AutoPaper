from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.csv_manager import CSVManager

TASK_FIELDNAMES = [
    "DOI",
    "DownloaStatus",
    "PaperFile",
    "PaperDownloadUrl",
    "SIDownloadStatus",
    "SIFile",
    "SIDownloadUrl",
    "htmlFile",
]

STATISTIC_FIELDNAMES = [
    "taskName",
    "status",
    "totalCount",
    "paperSuccessCount",
    "paperFailedCount",
    "siSuccessCount",
    "createTime",
    "updateTime",
]

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", flags=re.IGNORECASE)


class InvalidCSVFormatError(ValueError):
    pass


@dataclass
class ImportResult:
    total_rows: int
    imported_rows: int
    deleted_rows: int
    invalid_rows: int
    duplicate_rows: int
    task_name: str
    task_file: Path


class TaskManager:
    def __init__(self, project_root: str | Path | None = None):
        self.project_root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        self.tasks_dir = self.project_root / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        self.statistic_path = self._resolve_statistic_path()

    def import_csv(self, upload_path: str | Path) -> ImportResult:
        upload_path = Path(upload_path)
        rows, doi_column = self._read_upload_csv(upload_path)
        total_rows = len(rows)
        if total_rows == 0:
            raise InvalidCSVFormatError("文件格式不正确")

        valid_dois: list[str] = []
        seen: set[str] = set()
        invalid_rows = 0
        duplicate_rows = 0

        for row in rows:
            raw_value = row.get(doi_column, "")
            doi = self._normalize_doi(raw_value)
            if not self._is_valid_doi(doi):
                invalid_rows += 1
                continue

            key = doi.lower()
            if key in seen:
                duplicate_rows += 1
                continue
            seen.add(key)
            valid_dois.append(doi)

        imported_rows = len(valid_dois)
        deleted_rows = invalid_rows + duplicate_rows
        if imported_rows == 0:
            raise InvalidCSVFormatError("文件格式不正确")

        task_name = self._generate_task_name()
        task_file = self.tasks_dir / f"{task_name}.csv"
        self._write_task_file(task_file, valid_dois)
        self._upsert_statistic_row(task_name=task_name, total_count=imported_rows)

        return ImportResult(
            total_rows=total_rows,
            imported_rows=imported_rows,
            deleted_rows=deleted_rows,
            invalid_rows=invalid_rows,
            duplicate_rows=duplicate_rows,
            task_name=task_name,
            task_file=task_file,
        )

    def _read_upload_csv(self, upload_path: Path) -> tuple[list[dict[str, str]], str]:
        if not upload_path.exists() or not upload_path.is_file():
            raise InvalidCSVFormatError("文件格式不正确")

        try:
            with upload_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                fieldnames = reader.fieldnames or []
                if not fieldnames:
                    raise InvalidCSVFormatError("文件格式不正确")

                doi_column = self._find_doi_column(fieldnames)
                if not doi_column:
                    raise InvalidCSVFormatError("文件格式不正确")

                rows = []
                for row in reader:
                    # ignore completely empty lines
                    if not any((value or "").strip() for value in row.values()):
                        continue
                    rows.append(row)
                return rows, doi_column
        except UnicodeDecodeError as exc:
            raise InvalidCSVFormatError("文件格式不正确") from exc
        except csv.Error as exc:
            raise InvalidCSVFormatError("文件格式不正确") from exc

    def _find_doi_column(self, fieldnames: list[str]) -> str | None:
        for original in fieldnames:
            if (original or "").strip().lower() == "doi":
                return original
        return None

    def _normalize_doi(self, value: str | None) -> str:
        text = (value or "").strip()
        text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/)", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
        return text.strip()

    def _is_valid_doi(self, doi: str) -> bool:
        if not doi or " " in doi:
            return False
        return DOI_PATTERN.match(doi) is not None

    def _generate_task_name(self) -> str:
        base = datetime.now().strftime("tasks_%Y_%m%d_%H%M")
        candidate = base
        index = 1
        while (self.tasks_dir / f"{candidate}.csv").exists():
            candidate = f"{base}_{index:02d}"
            index += 1
        return candidate

    def _write_task_file(self, task_file: Path, dois: list[str]) -> None:
        manager = CSVManager(task_file, fieldnames=TASK_FIELDNAMES)
        manager.load()
        for doi in dois:
            manager.add_row(
                {
                    "DOI": doi,
                    "DownloaStatus": "",
                    "PaperFile": "",
                    "PaperDownloadUrl": "",
                    "SIDownloadStatus": "",
                    "SIFile": "",
                    "SIDownloadUrl": "",
                    "htmlFile": "",
                }
            )

    def _upsert_statistic_row(self, task_name: str, total_count: int) -> None:
        now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
        manager = CSVManager(self.statistic_path, fieldnames=STATISTIC_FIELDNAMES)
        manager.upsert_by(
            "taskName",
            task_name,
            {
                "taskName": task_name,
                "status": "pending",
                "totalCount": str(total_count),
                "paperSuccessCount": "0",
                "paperFailedCount": "0",
                "siSuccessCount": "0",
                "createTime": now_text,
                "updateTime": now_text,
            },
        )

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
