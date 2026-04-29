from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CSVManager:
    """Generic CSV CRUD manager backed by a local file."""

    def __init__(self, path: str | Path, fieldnames: list[str] | None = None):
        self.path = Path(path)
        self.fieldnames = list(fieldnames) if fieldnames else []
        self.rows: list[dict[str, str]] = []

    def load(self) -> list[dict[str, str]]:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.rows = []
            if self.fieldnames:
                self.save()
            return self.rows

        with self.path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            actual_fields = [f.strip() for f in (reader.fieldnames or []) if f and f.strip()]
            if not self.fieldnames:
                self.fieldnames = actual_fields
            if not self.fieldnames:
                self.rows = []
                return self.rows

            loaded_rows: list[dict[str, str]] = []
            for item in reader:
                row = {}
                for field in self.fieldnames:
                    row[field] = str(item.get(field, "") or "").strip()
                loaded_rows.append(row)

            self.rows = loaded_rows
            return self.rows

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.fieldnames and self.rows:
            self.fieldnames = list(self.rows[0].keys())

        with self.path.open("w", encoding="utf-8-sig", newline="") as csv_file:
            if not self.fieldnames:
                csv_file.write("")
                return
            writer = csv.DictWriter(csv_file, fieldnames=self.fieldnames)
            writer.writeheader()
            for row in self.rows:
                writer.writerow({field: row.get(field, "") for field in self.fieldnames})

    def get_all(self) -> list[dict[str, str]]:
        self.load()
        return list(self.rows)

    def get_page(self, page: int, size: int) -> list[dict[str, str]]:
        if page < 1:
            page = 1
        if size < 1:
            size = 1
        rows = self.get_all()
        start = (page - 1) * size
        end = start + size
        return rows[start:end]

    def find_by(self, field: str, value: str) -> dict[str, str] | None:
        target = str(value)
        for row in self.get_all():
            if row.get(field, "") == target:
                return row
        return None

    def update_by(self, field: str, value: str, updates: dict[str, Any]) -> bool:
        self.load()
        target = str(value)
        for row in self.rows:
            if row.get(field, "") == target:
                self._merge_fields(updates)
                for key, update_value in updates.items():
                    row[key] = self._to_text(update_value)
                self.save()
                return True
        return False

    def add_row(self, row: dict[str, Any]) -> None:
        self.load()
        self._merge_fields(row)
        normalized = {field: self._to_text(row.get(field, "")) for field in self.fieldnames}
        self.rows.append(normalized)
        self.save()

    def delete_by(self, field: str, value: str) -> bool:
        self.load()
        target = str(value)
        for idx, row in enumerate(self.rows):
            if row.get(field, "") == target:
                self.rows.pop(idx)
                self.save()
                return True
        return False

    def upsert_by(self, field: str, value: str, row: dict[str, Any]) -> None:
        self.load()
        target = str(value)
        self._merge_fields(row)

        normalized = {name: self._to_text(row.get(name, "")) for name in self.fieldnames}
        for idx, item in enumerate(self.rows):
            if item.get(field, "") == target:
                self.rows[idx] = normalized
                self.save()
                return

        self.rows.append(normalized)
        self.save()

    def _merge_fields(self, row_like: dict[str, Any]) -> None:
        for key in row_like.keys():
            if key not in self.fieldnames:
                self.fieldnames.append(key)

    @staticmethod
    def _to_text(value: Any) -> str:
        return "" if value is None else str(value).strip()
