import csv
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import Callable

try:
    from core.task_manager import InvalidCSVFormatError, TaskManager
except ModuleNotFoundError:
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.task_manager import InvalidCSVFormatError, TaskManager


class TaskManagerTab(tk.Frame):
    """Task list page driven by statistic.csv."""

    def __init__(
        self,
        master,
        on_view_detail: Callable[[str], None] | None = None,
        on_tasks_changed: Callable[[str | None], None] | None = None,
    ):
        super().__init__(master, bg="#f3f5f9")
        self.on_view_detail = on_view_detail
        self.on_tasks_changed = on_tasks_changed
        self.task_manager = TaskManager()
        self._setup_theme()
        self._build_ui()
        self._load_rows()

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
        self.font_name = self._pick_font()
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
            padding=(16, 10),
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
            padding=(16, 10),
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
            rowheight=42,
            borderwidth=0,
            relief="flat",
            font=(self.font_name, 12),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=self.colors["surface_soft"],
            foreground=self.colors["text"],
            relief="flat",
            borderwidth=0,
            font=(self.font_name, 12, "bold"),
            padding=(10, 12),
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", self.colors["text"])],
        )

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        page_header = tk.Frame(self, bg=self.colors["bg"], padx=28, pady=20)
        page_header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            page_header,
            text="任务列表",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font_name, 24, "bold"),
        ).pack(anchor="w")
        tk.Label(
            page_header,
            text="首页 · 任务概览（数据来源：statistic.csv）",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font_name, 12),
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=self.colors["bg"], padx=28)
        body.grid(row=1, column=0, sticky="nsew", pady=(0, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        toolbar_card = ttk.Frame(body, style="Card.TFrame", padding=16)
        toolbar_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        toolbar_card.grid_columnconfigure(1, weight=1)

        tk.Label(
            toolbar_card,
            text="筛选",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 13, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(2, 14))

        self.keyword_entry = tk.Entry(
            toolbar_card,
            relief="flat",
            bd=0,
            font=(self.font_name, 12),
            fg=self.colors["muted"],
            bg=self.colors["surface_soft"],
            insertbackground=self.colors["text"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["primary"],
        )
        self.keyword_entry.grid(row=0, column=1, sticky="ew", ipady=10, padx=(0, 12))
        self.keyword_entry.insert(0, "请输入关键词")
        self.keyword_entry.bind("<FocusIn>", self._clear_placeholder)
        self.keyword_entry.bind("<FocusOut>", self._restore_placeholder)

        ttk.Button(
            toolbar_card,
            text="创建 RSS 任务",
            style="Primary.TButton",
            takefocus=False,
        ).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(
            toolbar_card,
            text="导入 CSV 文件",
            style="Ghost.TButton",
            takefocus=False,
            command=self._on_import_csv_clicked,
        ).grid(row=0, column=3)

        list_card = ttk.Frame(body, style="Card.TFrame", padding=14)
        list_card.grid(row=1, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(0, weight=1)

        columns = (
            "task",
            "status",
            "doi_total",
            "done",
            "success",
            "failed",
            "create_time",
            "action",
        )
        self.action_column_id = f"#{len(columns)}"
        self.tree = ttk.Treeview(
            list_card,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
            selectmode="browse",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Button-1>", self._on_tree_click, add="+")

        headers = {
            "task": "任务名",
            "status": "状态",
            "doi_total": "DOI总数",
            "done": "已执行数",
            "success": "成功数量",
            "failed": "失败数量",
            "create_time": "创建时间",
            "action": "操作",
        }
        widths = {
            "task": 220,
            "status": 90,
            "create_time": 180,
            "doi_total": 100,
            "done": 100,
            "success": 100,
            "failed": 100,
            "action": 240,
        }
        anchors = {
            "task": "w",
            "status": "center",
            "create_time": "center",
            "doi_total": "center",
            "done": "center",
            "success": "center",
            "failed": "center",
            "action": "w",
        }
        for col in columns:
            self.tree.heading(col, text=headers[col], anchor=anchors[col])
            self.tree.column(col, width=widths[col], anchor=anchors[col], stretch=True)

        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f9fbff")
        self.tree.tag_configure("running", foreground=self.colors["primary_dark"])
        self.tree.tag_configure("success", foreground=self.colors["success"])
        self.tree.tag_configure("danger", foreground=self.colors["danger"])
        self.tree.tag_configure("pending", foreground=self.colors["muted"])

        footer = tk.Frame(body, bg=self.colors["bg"], pady=12)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        ttk.Button(footer, text="上一页", style="Ghost.TButton", takefocus=False).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            footer,
            text="第 1 页",
            style="Muted.TLabel",
        ).grid(row=0, column=1)
        ttk.Button(footer, text="下一页", style="Ghost.TButton", takefocus=False).grid(
            row=0, column=2, sticky="e"
        )

    def _load_rows(self):
        rows = self._read_rows_from_statistic_csv()
        self._render_rows(rows)

    def _on_import_csv_clicked(self):
        file_path = filedialog.askopenfilename(
            title="选择要导入的 CSV 文件",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )
        if not file_path:
            return

        try:
            result = self.task_manager.import_csv(file_path)
        except InvalidCSVFormatError:
            messagebox.showerror("导入失败", "文件格式不正确")
            return
        except Exception as exc:
            messagebox.showerror("导入失败", f"导入过程中发生错误：{exc}")
            return

        self._load_rows()
        if callable(self.on_tasks_changed):
            self.on_tasks_changed(result.task_name)
        messagebox.showinfo(
            "导入成功",
            (
                "CSV 导入完成\n"
                f"总行数：{result.total_rows}\n"
                f"成功导入：{result.imported_rows}\n"
                f"删除行数：{result.deleted_rows} "
                f"(无效 {result.invalid_rows} + 重复 {result.duplicate_rows})\n"
                f"任务文件：{result.task_file.name}"
            ),
        )

    def _on_tree_click(self, event):
        if not callable(self.on_view_detail):
            return

        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        if not row_id or not column_id:
            return

        if column_id != self.action_column_id:
            return

        values = self.tree.item(row_id, "values")
        if not values:
            return
        task_name = str(values[0]).strip()
        if not task_name:
            return

        self.on_view_detail(task_name)

    def _render_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for idx, row in enumerate(rows):
            base_tag = "odd" if idx % 2 == 0 else "even"
            status_tag = self._status_tag(row[1])
            self.tree.insert("", "end", values=row, tags=(base_tag, status_tag))

    def _status_tag(self, status_text):
        text = str(status_text).strip().lower()
        if any(word in text for word in ("失败", "fail", "error")):
            return "danger"
        if any(word in text for word in ("待执行", "pending", "queued")):
            return "pending"
        if any(word in text for word in ("执行中", "进行中", "running", "processing")):
            return "running"
        if any(word in text for word in ("完成", "success", "done", "finished", "completed")):
            return "success"
        return "running"

    def _map_status_display(self, raw_status):
        status = str(raw_status).strip()
        if not status:
            return "待执行"
        mapping = {
            "finished": "已完成",
            "pending": "待执行",
            "running": "执行中",
        }
        return mapping.get(status.lower(), status)

    def _find_statistic_csv(self):
        project_root = Path(__file__).resolve().parents[1]
        preferred = [project_root / "statistic.csv", project_root / "statistic.csv "]
        for file_path in preferred:
            if file_path.exists() and file_path.is_file():
                return file_path
        for file_path in sorted(project_root.glob("statistic.csv*")):
            if file_path.is_file():
                return file_path
        return None

    def _read_rows_from_statistic_csv(self):
        csv_path = self._find_statistic_csv()
        if not csv_path:
            return []

        rows = []
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
                reader = csv.DictReader(csv_file)
                for raw_row in reader:
                    row = self._normalize_row(raw_row)

                    task_name = self._pick_field(row, "taskname", "task", "任务名")
                    if not task_name:
                        continue

                    raw_status = self._pick_field(row, "status", "状态")
                    status = self._map_status_display(raw_status)
                    total_count = self._to_int(
                        self._pick_field(row, "totalcount", "doitotal", "doi总数")
                    )
                    success_count = self._to_int(
                        self._pick_field(
                            row,
                            "papersuccesscount",
                            "papersuccess",
                            "papersuccess_count",
                            "成功数量",
                        )
                    )
                    failed_count = self._to_int(
                        self._pick_field(
                            row,
                            "paperfailedcount",
                            "failedcount",
                            "paperfailed_count",
                            "失败数量",
                        )
                    )
                    done_count = success_count + failed_count
                    create_time = (
                        self._pick_field(row, "createtime", "create_time", "创建时间") or "-"
                    )

                    rows.append(
                        (
                            task_name,
                            status,
                            str(total_count),
                            str(done_count),
                            str(success_count),
                            str(failed_count),
                            create_time,
                            "查看详情  |  删除任务",
                        )
                    )
        except Exception:
            return []

        return rows

    def _normalize_row(self, row):
        normalized = {}
        for key, value in row.items():
            normalized[str(key).strip().lower()] = value
        return normalized

    def _pick_field(self, row, *keys):
        for key in keys:
            value = row.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    def _to_int(self, value):
        if value in (None, ""):
            return 0
        text = str(value).strip()
        if not text:
            return 0
        try:
            return int(float(text))
        except (TypeError, ValueError):
            return 0

    def _clear_placeholder(self, _event):
        if self.keyword_entry.get() == "请输入关键词":
            self.keyword_entry.delete(0, "end")
            self.keyword_entry.configure(fg=self.colors["text"])

    def _restore_placeholder(self, _event):
        if not self.keyword_entry.get().strip():
            self.keyword_entry.insert(0, "请输入关键词")
            self.keyword_entry.configure(fg=self.colors["muted"])


def launch_task_manager_tab():
    root = tk.Tk()
    root.title("AutoPaper - 任务列表首页")
    root.geometry("1480x820")
    root.minsize(1200, 700)
    TaskManagerTab(root).pack(fill="both", expand=True)
    return root


if __name__ == "__main__":
    app = launch_task_manager_tab()
    app.mainloop()
