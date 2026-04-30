import csv
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk


DETAIL_COLUMNS = (
    "DOI",
    "DownloaStatus",
    "SIDownloadStatus",
    "failedReason",
    "PublisherUrl",
    "PaperFile",
    "SIFile",
    "HtmlFile",
    "PaperDownloadUrl",
)
TREE_COLUMNS = ("序号",) + DETAIL_COLUMNS


class TaskDetailTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f3f5f9")
        self.project_root = Path(__file__).resolve().parents[1]
        self.tasks_dir = self.project_root / "tasks"
        self.font_name = self._pick_font()
        self.task_files: list[Path] = []
        self.all_rows: list[tuple[str, ...]] = []
        self._setup_theme()
        self._build_ui()
        self.refresh_task_options()

    def _pick_font(self):
        preferred = [
            "SF Pro Text",
            "PingFang SC",
            "Microsoft YaHei UI",
            "Segoe UI",
            "Helvetica Neue",
            "Arial",
        ]
        families = set(tkfont.families())
        return next((name for name in preferred if name in families), "TkDefaultFont")

    def _setup_theme(self):
        self.colors = {
            "bg": "#f3f5f9",
            "surface": "#ffffff",
            "surface_soft": "#f8faff",
            "border": "#e5eaf3",
            "text": "#1f2937",
            "muted": "#6b7280",
            "primary": "#2563eb",
            "primary_dark": "#1d4ed8",
            "danger": "#dc2626",
            "success": "#059669",
        }

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Card.TFrame",
            background=self.colors["surface"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Muted.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["muted"],
            font=(self.font_name, 12),
        )
        style.configure(
            "Primary.TButton",
            font=(self.font_name, 12, "bold"),
            foreground="#ffffff",
            background=self.colors["primary"],
            borderwidth=0,
            relief="flat",
            padding=(14, 8),
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.colors["primary_dark"])],
        )
        style.configure(
            "Ghost.TButton",
            font=(self.font_name, 12, "bold"),
            foreground=self.colors["text"],
            background=self.colors["surface_soft"],
            borderwidth=1,
            relief="solid",
            padding=(14, 8),
        )
        style.map(
            "Ghost.TButton",
            background=[("active", "#eef2ff")],
        )
        style.configure(
            "Modern.Treeview",
            background=self.colors["surface"],
            fieldbackground=self.colors["surface"],
            foreground=self.colors["text"],
            rowheight=36,
            borderwidth=0,
            relief="flat",
            font=(self.font_name, 11),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=self.colors["surface_soft"],
            foreground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=(self.font_name, 12, "bold"),
            padding=(10, 10),
        )

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = tk.Frame(self, bg=self.colors["bg"], padx=28, pady=20)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header,
            text="任务详情",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font_name, 24, "bold"),
        ).pack(anchor="w")

        summary_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        summary_card.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 14))
        for idx in range(7):
            summary_card.grid_columnconfigure(idx, weight=1)

        tk.Label(
            summary_card,
            text="当前任务：",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(4, 6))

        self.current_task_var = tk.StringVar()
        self.current_task_combo = ttk.Combobox(
            summary_card,
            textvariable=self.current_task_var,
            state="readonly",
            font=(self.font_name, 12),
            width=28,
        )
        self.current_task_combo.grid(row=0, column=1, sticky="w", padx=(0, 24))
        self.current_task_combo.bind("<<ComboboxSelected>>", self._on_task_combo_changed)

        self.total_var = tk.StringVar(value="-")
        self.status_var = tk.StringVar(value="-")
        self.executed_var = tk.StringVar(value="-")
        self.success_var = tk.StringVar(value="-")
        self.failed_var = tk.StringVar(value="-")

        tk.Label(
            summary_card,
            textvariable=self.total_var,
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 15, "bold"),
        ).grid(row=0, column=2, sticky="w")
        tk.Label(
            summary_card,
            textvariable=self.status_var,
            bg=self.colors["surface"],
            fg=self.colors["primary_dark"],
            font=(self.font_name, 15, "bold"),
        ).grid(row=0, column=3, sticky="w")
        tk.Label(
            summary_card,
            textvariable=self.executed_var,
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 15, "bold"),
        ).grid(row=0, column=4, sticky="w")
        tk.Label(
            summary_card,
            textvariable=self.success_var,
            bg=self.colors["surface"],
            fg=self.colors["success"],
            font=(self.font_name, 15, "bold"),
        ).grid(row=0, column=5, sticky="w")
        tk.Label(
            summary_card,
            textvariable=self.failed_var,
            bg=self.colors["surface"],
            fg=self.colors["danger"],
            font=(self.font_name, 15, "bold"),
        ).grid(row=0, column=6, sticky="w")

        detail_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        detail_card.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 24))
        detail_card.grid_columnconfigure(0, weight=1)
        detail_card.grid_rowconfigure(1, weight=1)

        toolbar = tk.Frame(detail_card, bg=self.colors["surface"])
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        toolbar.grid_columnconfigure(3, weight=1)

        tk.Label(
            toolbar,
            text="任务详情",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 18, "bold"),
        ).grid(row=0, column=0, padx=(2, 14), sticky="w")

        self.search_var = tk.StringVar(value="输入查询")
        self.search_entry = tk.Entry(
            toolbar,
            textvariable=self.search_var,
            relief="flat",
            bd=0,
            font=(self.font_name, 12),
            fg=self.colors["muted"],
            bg=self.colors["surface_soft"],
            insertbackground=self.colors["text"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
            width=26,
        )
        self.search_entry.grid(row=0, column=1, ipady=8, padx=(0, 10), sticky="w")
        self.search_entry.bind("<FocusIn>", self._clear_search_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_search_placeholder)

        ttk.Button(
            toolbar,
            text="查询",
            style="Primary.TButton",
            takefocus=False,
            command=self._on_search_clicked,
        ).grid(row=0, column=2, padx=(0, 10), sticky="w")

        ttk.Button(
            toolbar,
            text="打开系统目录",
            style="Ghost.TButton",
            takefocus=False,
            command=self._open_project_root,
        ).grid(row=0, column=4, sticky="e")

        table_frame = tk.Frame(detail_card, bg=self.colors["surface"])
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.detail_tree = ttk.Treeview(
            table_frame,
            columns=TREE_COLUMNS,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse",
        )
        self.detail_tree.grid(row=0, column=0, sticky="nsew")

        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.detail_tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.detail_tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.detail_tree.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

        widths = {
            "序号": 70,
            "DOI": 220,
            "DownloaStatus": 130,
            "SIDownloadStatus": 150,
            "failedReason": 180,
            "PublisherUrl": 220,
            "PaperFile": 160,
            "SIFile": 140,
            "HtmlFile": 180,
            "PaperDownloadUrl": 220,
        }
        for col in TREE_COLUMNS:
            anchor = (
                "w"
                if col in {"DOI", "failedReason", "PublisherUrl", "PaperFile", "SIFile", "HtmlFile", "PaperDownloadUrl"}
                else "center"
            )
            self.detail_tree.heading(col, text=col, anchor=anchor)
            self.detail_tree.column(col, width=widths[col], anchor=anchor, stretch=True)

    def refresh_task_options(self, preferred_task: str | None = None) -> None:
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.task_files = sorted(
            self.tasks_dir.glob("*.csv"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        self.current_task_combo["values"] = [item.name for item in self.task_files]

        if not self.task_files:
            self.current_task_var.set("")
            self._set_summary("-", "-", "-", "-", "-")
            self._render_rows([])
            return

        target = preferred_task or self.current_task_var.get()
        task_file = self._resolve_task_file(target) or self.task_files[0]
        self.current_task_var.set(task_file.name)
        self._load_task(task_file)

    def select_task(self, task_name: str) -> None:
        if not task_name:
            return
        task_file = self._resolve_task_file(task_name)
        if not task_file:
            return
        self.current_task_var.set(task_file.name)
        self._load_task(task_file)

    def _resolve_task_file(self, task_name: str) -> Path | None:
        if not self.task_files:
            return None
        target = task_name.strip()
        if not target:
            return None

        target_stem = Path(target).stem.lower()
        target_name = Path(target).name.lower()
        for item in self.task_files:
            if item.stem.lower() == target_stem or item.name.lower() == target_name:
                return item
        return None

    def _on_task_combo_changed(self, _event):
        task_file = self._resolve_task_file(self.current_task_var.get())
        if task_file:
            self._load_task(task_file)

    def _load_task(self, task_file: Path):
        self.all_rows = self._read_task_rows(task_file)
        self._render_rows(self.all_rows)

        total_count, status, executed, success, failed = self._read_summary_from_statistic(task_file.stem)
        self._set_summary(total_count, status, executed, success, failed)

    def _set_summary(self, total_count: str, status: str, executed: str, success: str, failed: str):
        self.total_var.set(f"DOI总数：{total_count}条")
        self.status_var.set(f"状态：{status}")
        self.executed_var.set(f"已执行：{executed}条")
        self.success_var.set(f"成功{success}条")
        self.failed_var.set(f"失败{failed}条")

    def _read_task_rows(self, task_file: Path) -> list[tuple[str, ...]]:
        rows: list[tuple[str, ...]] = []
        try:
            with task_file.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                if not reader.fieldnames:
                    return rows

                field_map = {name: (name or "").strip() for name in reader.fieldnames}
                for raw in reader:
                    if not any((value or "").strip() for value in raw.values()):
                        continue

                    normalized_row = {}
                    for old_key, value in raw.items():
                        normalized_row[field_map.get(old_key, old_key)] = str(value or "").strip()
                    if "HtmlFile" not in normalized_row and "htmlFile" in normalized_row:
                        normalized_row["HtmlFile"] = normalized_row.get("htmlFile", "")
                    rows.append(tuple(normalized_row.get(column, "") for column in DETAIL_COLUMNS))
        except Exception:
            return []
        return rows

    def _find_statistic_csv(self) -> Path | None:
        preferred = [self.project_root / "statistic.csv", self.project_root / "statistic.csv "]
        for path in preferred:
            if path.exists() and path.is_file():
                return path
        for path in sorted(self.project_root.glob("statistic.csv*")):
            if path.is_file():
                return path
        return None

    def _map_status_display(self, raw_status: str) -> str:
        text = str(raw_status or "").strip()
        if not text:
            return "-"
        mapping = {
            "finished": "已完成",
            "pending": "待执行",
            "running": "执行中",
        }
        return mapping.get(text.lower(), text)

    def _read_summary_from_statistic(self, task_stem: str) -> tuple[str, str, str, str, str]:
        csv_path = self._find_statistic_csv()
        if not csv_path:
            return "-", "-", "-", "-", "-"

        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for raw in reader:
                    row = {str(key).strip().lower(): str(value or "").strip() for key, value in raw.items()}
                    task_name = row.get("taskname", "")
                    if not task_name:
                        continue
                    if Path(task_name).stem.lower() != task_stem.lower():
                        continue

                    total_count = str(self._to_int(row.get("totalcount", "0")))
                    status = self._map_status_display(row.get("status", ""))
                    success = self._to_int(row.get("papersuccesscount", "0"))
                    failed = self._to_int(row.get("paperfailedcount", "0"))
                    executed = success + failed
                    return total_count, status, str(executed), str(success), str(failed)
        except Exception:
            return "-", "-", "-", "-", "-"

        return "-", "-", "-", "-", "-"

    def _on_search_clicked(self):
        keyword = self.search_var.get().strip()
        if keyword == "输入查询":
            keyword = ""

        if not keyword:
            self._render_rows(self.all_rows)
            return

        key = keyword.lower()
        filtered = []
        for row in self.all_rows:
            if any(key in str(cell).lower() for cell in row):
                filtered.append(row)
        self._render_rows(filtered)

    def _render_rows(self, rows: list[tuple[str, ...]]):
        self.detail_tree.delete(*self.detail_tree.get_children())
        for idx, row in enumerate(rows, start=1):
            self.detail_tree.insert("", "end", values=(str(idx),) + tuple(row))

    def _clear_search_placeholder(self, _event):
        if self.search_var.get() == "输入查询":
            self.search_var.set("")
            self.search_entry.configure(fg=self.colors["text"])

    def _restore_search_placeholder(self, _event):
        if not self.search_var.get().strip():
            self.search_var.set("输入查询")
            self.search_entry.configure(fg=self.colors["muted"])

    def _open_project_root(self):
        target = str(self.project_root)
        try:
            if sys.platform.startswith("win"):
                os.startfile(target)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception as exc:
            messagebox.showerror("打开失败", f"无法打开目录：{exc}")

    @staticmethod
    def _to_int(value: str | None) -> int:
        text = str(value or "").strip()
        if not text:
            return 0
        try:
            return int(float(text))
        except (TypeError, ValueError):
            return 0
