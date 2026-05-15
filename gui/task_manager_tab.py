import csv
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import Callable

try:
    from core.csv_manager import CSVManager
    from core.create_rss_task import create_rss_task
    from core.task_manager import InvalidCSVFormatError, TaskManager
except ModuleNotFoundError:
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.csv_manager import CSVManager
    from core.create_rss_task import create_rss_task
    from core.task_manager import InvalidCSVFormatError, TaskManager


class TaskManagerTab(tk.Frame):
    """Task list page driven by statistic.csv."""

    REFRESH_MS = 2000

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
        self.project_root = Path(__file__).resolve().parents[1]
        self.tasks_dir = self.project_root / "tasks"
        self._executor_proc: subprocess.Popen[str] | None = None
        self._running_task_name = ""
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
            "text": "#374151",
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
            width=20,
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
            command=self._on_create_rss_task_clicked,
        ).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(
            toolbar_card,
            text="导入 CSV 文件",
            style="Ghost.TButton",
            takefocus=False,
            command=self._on_import_csv_clicked,
        ).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(
            toolbar_card,
            text="刷新列表",
            style="Ghost.TButton",
            takefocus=False,
            command=self._load_rows,
        ).grid(row=0, column=4)

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
            "run_action",
            "detail_action",
            "delete_action",
        )
        self.run_action_column_id = f"#{columns.index('run_action') + 1}"
        self.detail_action_column_id = f"#{columns.index('detail_action') + 1}"
        self.delete_action_column_id = f"#{columns.index('delete_action') + 1}"
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
            "run_action": "开始/停止",
            "detail_action": "查看详情",
            "delete_action": "删除任务",
        }
        widths = {
            "task": 200,
            "status": 90,
            "create_time": 160,
            "doi_total": 100,
            "done": 100,
            "success": 100,
            "failed": 100,
            "run_action": 110,
            "detail_action": 100,
            "delete_action": 100,
        }
        anchors = {
            "task": "w",
            "status": "center",
            "create_time": "center",
            "doi_total": "center",
            "done": "center",
            "success": "center",
            "failed": "center",
            "run_action": "center",
            "detail_action": "center",
            "delete_action": "center",
        }
        for col in columns:
            self.tree.heading(col, text=headers[col], anchor=anchors[col])
            self.tree.column(col, width=widths[col], anchor=anchors[col], stretch=True)

        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f9fbff")

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

    def _on_create_rss_task_clicked(self):
        keyword = self._read_keyword()
        if not keyword:
            messagebox.showwarning("提示", "请输入关键词")
            return

        try:
            result = create_rss_task(keyword=keyword)
        except ValueError as exc:
            messagebox.showerror("创建失败", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("创建失败", f"创建 RSS 任务失败：{exc}")
            return

        self._load_rows()
        if callable(self.on_tasks_changed):
            self.on_tasks_changed(str(result.get("task_name", "") or ""))
        messagebox.showinfo(
            "创建成功",
            (
                f"任务名：{result.get('task_name', '')}\n"
                f"提取DOI：{result.get('total_extracted', 0)}条\n"
                f"有效DOI：{result.get('valid_count', 0)}条\n"
                f"重复DOI：{result.get('duplicate_count', 0)}条\n"
                f"无效DOI：{result.get('invalid_count', 0)}条"
            ),
        )

    def _read_keyword(self) -> str:
        text = str(self.keyword_entry.get() or "").strip()
        if text == "请输入关键词":
            return ""
        return text

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        if not row_id or not column_id:
            return

        values = self.tree.item(row_id, "values")
        if not values:
            return
        task_name = str(values[0]).strip()
        if not task_name:
            return

        if column_id == self.run_action_column_id:
            run_text = str(values[7]).strip() if len(values) > 7 else ""
            if run_text == "-":
                return
            self._on_run_action_clicked(task_name, run_text)
            return
        if column_id == self.detail_action_column_id:
            if callable(self.on_view_detail):
                self.on_view_detail(task_name)
            return
        if column_id == self.delete_action_column_id:
            self._on_delete_action_clicked(task_name)

    def _on_run_action_clicked(self, task_name: str, run_text: str) -> None:
        if self._is_running_task(task_name):
            self._stop_running_task()
            return
        if run_text == "一键重试":
            self._retry_task(task_name)
            return
        self._start_task(task_name)

    def _retry_task(self, task_name: str) -> None:
        if self._is_executor_running():
            messagebox.showwarning("提示", "已有任务执行中，请先停止当前任务")
            return
        task_path = self._task_csv_path(task_name)
        if not task_path.exists():
            messagebox.showerror("重试失败", f"任务文件不存在：{task_path.name}")
            self._load_rows()
            return

        _, _, failed_count = self._get_task_paper_stats(task_name)
        if failed_count <= 0:
            messagebox.showinfo("提示", "当前没有可重试的失败记录")
            self._load_rows()
            return

        confirmed = messagebox.askyesno(
            "一键重试",
            f"共有 {failed_count} 条失败记录，将重试下载",
        )
        if not confirmed:
            return

        self._reset_failed_rows_for_retry(task_path)
        self._start_task(task_name)

    def _start_task(self, task_name: str) -> None:
        if self._is_executor_running():
            messagebox.showwarning("提示", "已有任务执行中，请先停止当前任务")
            return
        task_path = self._task_csv_path(task_name)
        if not task_path.exists():
            messagebox.showerror("启动失败", f"任务文件不存在：{task_path.name}")
            self._load_rows()
            return
        try:
            cmd = self._build_executor_command(task_path)
            self._executor_proc = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
            )
            self._running_task_name = Path(task_name).stem
            self._load_rows()
            if callable(self.on_tasks_changed):
                self.on_tasks_changed(task_name)
        except Exception as exc:
            self._executor_proc = None
            self._running_task_name = ""
            messagebox.showerror("启动失败", f"无法启动任务执行：{exc}")

    def _build_executor_command(self, task_path: Path) -> list[str]:
        parent_pid = str(os.getpid())
        if getattr(sys, "frozen", False):
            worker = Path(sys.executable).resolve().with_name(_worker_name())
            if not worker.exists():
                raise FileNotFoundError(f"未找到任务执行器: {worker}")
            return [str(worker), "--run-task", str(task_path), "--parent-pid", parent_pid]
        return [sys.executable, "-m", "core.task_executor", "--task", str(task_path), "--parent-pid", parent_pid]

    def _task_csv_path(self, task_name: str) -> Path:
        return (self.tasks_dir / f"{Path(task_name).stem}.csv").resolve()

    def _reset_failed_rows_for_retry(self, task_path: Path) -> None:
        manager = CSVManager(task_path)
        rows = manager.get_all()
        clear_keys = [
            "DownloaStatus",
            "SIDownloadStatus",
            "failedReason",
            "PublisherUrl",
            "PaperFile",
            "SIFile",
            "HtmlFile",
            "PaperDownloadUrl",
        ]
        changed = False
        for row in rows:
            status = str(row.get("DownloaStatus", "") or "").strip().lower()
            if status != "failed":
                continue
            for key in clear_keys:
                if row.get(key, "") != "":
                    changed = True
                row[key] = ""
            changed = True
        if changed:
            manager.rows = rows
            manager.save()

    def _stop_running_task(self) -> None:
        proc = self._executor_proc
        if not proc:
            self._running_task_name = ""
            self._load_rows()
            return
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        except Exception as exc:
            messagebox.showerror("停止失败", f"停止任务失败：{exc}")
        finally:
            self._executor_proc = None
            self._running_task_name = ""
            self._load_rows()
            if callable(self.on_tasks_changed):
                self.on_tasks_changed(None)

    def shutdown(self) -> None:
        if self._is_executor_running():
            self._stop_running_task()

    def _on_delete_action_clicked(self, task_name: str) -> None:
        task_stem = Path(task_name).stem
        if self._is_running_task(task_stem):
            messagebox.showwarning("提示", "任务正在执行中，请先停止执行后再删除")
            return
        if not messagebox.askyesno("确认删除", f"确认删除任务 {task_stem} 吗？"):
            return

        task_file = (self.tasks_dir / f"{task_stem}.csv").resolve()
        try:
            if task_file.exists():
                task_file.unlink()
            self._delete_statistic_row(task_stem)
            self._load_rows()
            if callable(self.on_tasks_changed):
                self.on_tasks_changed(None)
            messagebox.showinfo("删除成功", f"任务 {task_stem} 已删除")
        except Exception as exc:
            messagebox.showerror("删除失败", f"删除任务失败：{exc}")

    def _delete_statistic_row(self, task_stem: str) -> None:
        csv_path = self._find_statistic_csv()
        if not csv_path:
            return
        manager = CSVManager(csv_path)
        rows = manager.get_all()
        filtered = []
        target = Path(task_stem).stem.lower()
        for row in rows:
            name = Path(str(row.get("taskName", "") or "").strip()).stem.lower()
            if name == target:
                continue
            filtered.append(row)
        manager.rows = filtered
        manager.save()

    def _is_running_task(self, task_name: str) -> bool:
        return (
            self._is_executor_running()
            and Path(str(self._running_task_name)).stem.lower() == Path(str(task_name)).stem.lower()
        )

    def _is_executor_running(self) -> bool:
        return self._executor_proc is not None and self._executor_proc.poll() is None

    def _render_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for idx, row in enumerate(rows):
            base_tag = "odd" if idx % 2 == 0 else "even"
            self.tree.insert("", "end", values=row, tags=(base_tag,))

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
        preferred = [self.project_root / "statistic.csv", self.project_root / "statistic.csv "]
        for file_path in preferred:
            if file_path.exists() and file_path.is_file():
                return file_path
        for file_path in sorted(self.project_root.glob("statistic.csv*")):
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
                    status_text = self._format_status_text(status)
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
                    run_action = self._resolve_run_action_text(task_name, status)

                    rows.append(
                        (
                            task_name,
                            status_text,
                            str(total_count),
                            str(done_count),
                            str(success_count),
                            str(failed_count),
                            create_time,
                            run_action,
                            "查看详情",
                            "删除任务",
                        )
                    )
        except Exception:
            return []

        return sorted(rows, key=self._sort_key_create_time, reverse=True)

    def _format_status_text(self, status: str) -> str:
        return str(status or "").strip()

    def _resolve_run_action_text(self, task_name: str, status: str) -> str:
        if self._is_running_task(task_name):
            return "停止执行"
        total_count, success_count, failed_count = self._get_task_paper_stats(task_name)
        if total_count > 0 and success_count >= total_count:
            return "-"
        if status == "已完成" and failed_count > 0:
            return "一键重试"
        return "开始执行"

    def _get_task_paper_stats(self, task_name: str) -> tuple[int, int, int]:
        task_path = self._task_csv_path(task_name)
        if not task_path.exists():
            return 0, 0, 0
        try:
            manager = CSVManager(task_path)
            rows = manager.get_all()
        except Exception:
            return 0, 0, 0

        total = 0
        success = 0
        failed = 0
        for row in rows:
            doi = str(row.get("DOI", "") or "").strip()
            if not doi:
                continue
            total += 1
            status = str(row.get("DownloaStatus", "") or "").strip().lower()
            if status == "success":
                success += 1
            elif status == "failed":
                failed += 1
        return total, success, failed

    def _sort_key_create_time(self, row):
        text = str(row[6] if len(row) > 6 else "").strip()
        if not text or text == "-":
            return datetime.min
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M")
        except Exception:
            return datetime.min

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


def _worker_name() -> str:
    return "AutoPaperWorker.exe" if sys.platform.startswith("win") else "AutoPaperWorker"


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
