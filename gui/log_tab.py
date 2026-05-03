import csv
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk


class LogTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f3f5f9")
        self.project_root = Path(__file__).resolve().parents[1]
        self.log_dir = self.project_root / "logs"
        self.index_path = self.log_dir / "index.csv"
        self.statistic_path = self._find_statistic_csv()

        self.font_name = self._pick_font()
        self.colors = {
            "bg": "#f3f5f9",
            "surface": "#ffffff",
            "surface_soft": "#f8faff",
            "border": "#e5eaf3",
            "text": "#374151",
            "muted": "#6b7280",
            "primary": "#2563eb",
            "primary_dark": "#1d4ed8",
            "danger": "#dc2626",
            "success": "#059669",
        }

        self.task_to_logs: dict[str, list[dict[str, str]]] = {}
        self.task_name_var = tk.StringVar()
        self.log_name_var = tk.StringVar()
        self.keyword_var = tk.StringVar()
        self.executed_var = tk.StringVar(value="已执行：-")
        self.success_var = tk.StringVar(value="成功：-")
        self.failed_var = tk.StringVar(value="失败：-")
        self.current_log_content = ""

        self._setup_theme()
        self._build_ui()
        self._reload_all()

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
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Card.TFrame",
            background=self.colors["surface"],
            borderwidth=1,
            relief="solid",
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
        style.map("Primary.TButton", background=[("active", self.colors["primary_dark"])])
        style.configure(
            "Ghost.TButton",
            font=(self.font_name, 12, "bold"),
            foreground=self.colors["text"],
            background=self.colors["surface_soft"],
            borderwidth=1,
            relief="solid",
            padding=(14, 8),
        )
        style.map("Ghost.TButton", background=[("active", "#eef2ff")])

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = tk.Frame(self, bg=self.colors["bg"], padx=28, pady=20)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header,
            text="系统日志",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font_name, 24, "bold"),
        ).pack(anchor="w")

        top_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        top_card.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 14))
        for i in range(6):
            top_card.grid_columnconfigure(i, weight=1 if i in {1, 2, 3} else 0)

        tk.Label(
            top_card,
            text="任务名",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 13, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(4, 10))

        self.task_combo = ttk.Combobox(
            top_card,
            textvariable=self.task_name_var,
            state="readonly",
            font=(self.font_name, 12),
            width=30,
        )
        self.task_combo.grid(row=0, column=1, sticky="ew", padx=(0, 16))
        self.task_combo.bind("<<ComboboxSelected>>", self._on_task_changed)

        tk.Label(
            top_card,
            textvariable=self.executed_var,
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 12, "bold"),
        ).grid(row=0, column=2, sticky="w")
        tk.Label(
            top_card,
            textvariable=self.success_var,
            bg=self.colors["surface"],
            fg=self.colors["success"],
            font=(self.font_name, 12, "bold"),
        ).grid(row=0, column=3, sticky="w")
        tk.Label(
            top_card,
            textvariable=self.failed_var,
            bg=self.colors["surface"],
            fg=self.colors["danger"],
            font=(self.font_name, 12, "bold"),
        ).grid(row=0, column=4, sticky="w")

        ttk.Button(
            top_card,
            text="刷新",
            style="Ghost.TButton",
            takefocus=False,
            command=self._reload_all,
        ).grid(row=0, column=5, sticky="e")

        log_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        log_card.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 24))
        log_card.grid_columnconfigure(1, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        toolbar = tk.Frame(log_card, bg=self.colors["surface"])
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        toolbar.grid_columnconfigure(1, weight=1)
        toolbar.grid_columnconfigure(5, weight=1)

        tk.Label(
            toolbar,
            text="系统日志",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 18, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(2, 16))

        self.keyword_entry = tk.Entry(
            toolbar,
            textvariable=self.keyword_var,
            relief="flat",
            bd=0,
            font=(self.font_name, 12),
            fg=self.colors["text"],
            bg=self.colors["surface_soft"],
            insertbackground=self.colors["text"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
        )
        self.keyword_entry.grid(row=0, column=1, sticky="ew", ipady=8, padx=(0, 10))
        self.keyword_entry.bind("<Return>", self._search_keyword_in_current_log)

        ttk.Button(
            toolbar,
            text="查询",
            style="Primary.TButton",
            takefocus=False,
            command=self._search_keyword_in_current_log,
        ).grid(row=0, column=2, sticky="w", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="清空日志",
            style="Ghost.TButton",
            takefocus=False,
            command=self._clear_log_view,
        ).grid(row=0, column=3, sticky="w", padx=(0, 10))

        self.log_combo = ttk.Combobox(
            toolbar,
            textvariable=self.log_name_var,
            state="readonly",
            font=(self.font_name, 11),
            width=34,
        )
        self.log_combo.grid(row=0, column=6, sticky="e")
        self.log_combo.bind("<<ComboboxSelected>>", self._on_log_changed)

        self.log_text = tk.Text(
            log_card,
            wrap="word",
            font=(self.font_name, 11),
            bg=self.colors["surface_soft"],
            fg=self.colors["text"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
        )
        self.log_text.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.log_text.configure(state="disabled")

    def _reload_all(self):
        self.statistic_path = self._find_statistic_csv()
        self.task_to_logs = self._build_task_log_mapping()
        task_names = list(self.task_to_logs.keys())
        self.task_combo["values"] = task_names

        if not task_names:
            self.task_name_var.set("")
            self.log_name_var.set("")
            self.log_combo["values"] = []
            self._set_summary("-", "-", "-")
            self.current_log_content = ""
            self._set_log_text("暂无日志")
            return

        self.task_name_var.set(task_names[0])
        self._sync_task_combobox_selection(task_names[0])
        self._on_task_changed()

    def _build_task_log_mapping(self) -> dict[str, list[dict[str, str]]]:
        if not self.index_path.exists() or not self.index_path.is_file():
            return {}

        task_to_logs: dict[str, list[dict[str, str]]] = {}
        try:
            with self.index_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    task_name = Path(str(row.get("taskName", "") or "").strip()).stem
                    log_file = str(row.get("logFile", "") or "").strip()
                    created_at = str(row.get("createdAt", "") or "").strip()
                    if not task_name or not log_file:
                        continue
                    task_to_logs.setdefault(task_name, []).append(
                        {"logFile": log_file, "createdAt": created_at}
                    )
        except Exception:
            return {}

        for task_name in task_to_logs.keys():
            task_to_logs[task_name].sort(
                key=lambda item: str(item.get("createdAt", "") or ""),
                reverse=True,
            )

        sorted_items = sorted(
            task_to_logs.items(),
            key=lambda item: str(item[1][0].get("createdAt", "") if item[1] else ""),
            reverse=True,
        )
        return {name: logs for name, logs in sorted_items}

    def _on_task_changed(self, _event=None):
        task_name = Path(str(self.task_name_var.get() or "").strip()).stem
        if not task_name:
            self.log_combo["values"] = []
            self.log_name_var.set("")
            self._set_summary("-", "-", "-")
            self.current_log_content = ""
            self._set_log_text("暂无日志")
            return

        self._sync_task_combobox_selection(task_name)
        logs = self.task_to_logs.get(task_name, [])
        log_names = [str(item.get("logFile", "") or "") for item in logs if item.get("logFile")]
        self.log_combo["values"] = log_names

        self._update_summary_for_task(task_name)

        if not log_names:
            self.log_name_var.set("")
            self.current_log_content = ""
            self._set_log_text("暂无日志")
            return

        self.log_name_var.set(log_names[0])
        self._load_current_log_content()
        self._set_log_text(self.current_log_content if self.current_log_content else "暂无日志")

    def _on_log_changed(self, _event=None):
        self._load_current_log_content()
        self._set_log_text(self.current_log_content if self.current_log_content else "暂无日志")

    def _load_current_log_content(self):
        log_name = str(self.log_name_var.get() or "").strip()
        if not log_name:
            self.current_log_content = ""
            return
        log_path = self.log_dir / log_name
        if not log_path.exists() or not log_path.is_file():
            self.current_log_content = ""
            return
        try:
            content = log_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            self.current_log_content = ""
            return
        self.current_log_content = content if content.strip() else ""

    def _search_keyword_in_current_log(self, _event=None):
        if not self.current_log_content:
            self._set_log_text("暂无日志")
            return

        keyword = str(self.keyword_var.get() or "").strip()
        if not keyword:
            self._set_log_text(self.current_log_content)
            return

        key = keyword.lower()
        lines = self.current_log_content.splitlines()
        matched: list[str] = []
        for idx, line in enumerate(lines, start=1):
            if key in line.lower():
                matched.append(f"{idx:04d}: {line}")

        if not matched:
            self._set_log_text("未找到关键词")
            return
        self._set_log_text("\n".join(matched))

    def _clear_log_view(self):
        self.keyword_var.set("")
        self._set_log_text("")

    def _sync_task_combobox_selection(self, task_name: str):
        normalized = Path(str(task_name or "").strip()).stem
        self.task_name_var.set(normalized)
        self.task_combo.set(normalized)

    def _set_summary(self, executed: str, success: str, failed: str):
        self.executed_var.set(f"已执行：{executed}")
        self.success_var.set(f"成功：{success}")
        self.failed_var.set(f"失败：{failed}")

    def _update_summary_for_task(self, task_name: str):
        if not self.statistic_path or not self.statistic_path.exists():
            self._set_summary("-", "-", "-")
            return

        target = Path(str(task_name or "").strip()).stem.lower()
        try:
            with self.statistic_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for raw in reader:
                    row = {str(k).strip().lower(): str(v or "").strip() for k, v in raw.items()}
                    name = Path(row.get("taskname", "")).stem.lower()
                    if name != target:
                        continue
                    success = self._to_int(row.get("papersuccesscount", "0"))
                    failed = self._to_int(row.get("paperfailedcount", "0"))
                    executed = success + failed
                    self._set_summary(str(executed), str(success), str(failed))
                    return
        except Exception:
            self._set_summary("-", "-", "-")
            return

        self._set_summary("-", "-", "-")

    def _find_statistic_csv(self) -> Path | None:
        preferred = [self.project_root / "statistic.csv", self.project_root / "statistic.csv "]
        for path in preferred:
            if path.exists() and path.is_file():
                return path
        for path in sorted(self.project_root.glob("statistic.csv*")):
            if path.is_file():
                return path
        return None

    def _set_log_text(self, content: str):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("1.0", str(content or ""))
        self.log_text.configure(state="disabled")

    @staticmethod
    def _to_int(value: str | None) -> int:
        text = str(value or "").strip()
        if not text:
            return 0
        try:
            return int(float(text))
        except Exception:
            return 0
