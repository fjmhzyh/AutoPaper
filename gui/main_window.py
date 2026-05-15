import tkinter as tk
import traceback
from tkinter import ttk
from tkinter import font as tkfont
from tkinter import messagebox
from datetime import datetime

from core.logger import get_log_dir
from .config_tab import ConfigTab
from .log_tab import LogTab
from .task_detail_tab import TaskDetailTab
from .task_manager_tab import TaskManagerTab


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.font_name = self._pick_font()
        self.report_callback_exception = self._handle_callback_exception
        self._setup_window()
        self._setup_styles()
        self._build_tabs()
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self.bind_all("<Command-w>", self._ignore_close_hotkey)
        self.bind_all("<Control-w>", self._ignore_close_hotkey)

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

    def _setup_window(self):
        width, height = 1200, 650
        self.title("AutoPaper - 论文全自动下载管理工具")
        self.minsize(width, height)
        self._center_window(width, height)
        self.configure(bg="#f3f5f9")

    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(0, (screen_w - width) // 2)
        pos_y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Main.TNotebook", background="#f3f5f9", borderwidth=0)
        style.configure(
            "Main.TNotebook.Tab",
            font=(self.font_name, 12, "bold"),
            padding=(20, 10),
            width=12,
            background="#e9eef8",
            foreground="#1f2937",
            borderwidth=0,
        )
        style.map(
            "Main.TNotebook.Tab",
            background=[("selected", "#2563eb"), ("active", "#dbeafe")],
            foreground=[("selected", "#ffffff"), ("!selected", "#1f2937")],
            # Keep selected/unselected tab size identical.
            padding=[("selected", (20, 10)), ("!selected", (20, 10))],
            expand=[("selected", (0, 0, 0, 0)), ("!selected", (0, 0, 0, 0))],
        )

    def _build_tabs(self):
        container = tk.Frame(self, bg="#f3f5f9", padx=18, pady=16)
        container.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(container, style="Main.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.task_detail_tab = TaskDetailTab(self.notebook)
        self.task_manager_tab = TaskManagerTab(
            self.notebook,
            on_view_detail=self.open_task_detail,
            on_tasks_changed=self._on_tasks_changed,
        )
        self.log_tab = LogTab(self.notebook)
        self.config_tab = ConfigTab(self.notebook)

        self.notebook.add(self.task_manager_tab, text="首页")
        self.notebook.add(self.log_tab, text="系统日志")
        self.notebook.add(self.task_detail_tab, text="任务详情")
        self.notebook.add(self.config_tab, text="系统配置")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tasks_changed(self, preferred_task: str | None = None):
        self.task_detail_tab.refresh_task_options(preferred_task=preferred_task)
        self.log_tab.refresh_task_options(preferred_task=preferred_task)

    def open_task_detail(self, task_name: str):
        self.task_detail_tab.refresh_task_options(preferred_task=task_name)
        self.task_detail_tab.select_task(task_name)
        self.notebook.select(self.task_detail_tab)

    def _on_tab_changed(self, _event=None):
        current = self.notebook.select()
        if current == str(self.task_manager_tab):
            self.task_manager_tab._load_rows()
            return
        if current == str(self.task_detail_tab):
            self.task_detail_tab.refresh_task_options(preferred_task=self.task_detail_tab.current_task_var.get())
            return
        if current == str(self.log_tab):
            self.log_tab.refresh_task_options(preferred_task=self.log_tab.task_name_var.get())

    def _on_window_close(self):
        self._write_gui_event_log("收到主窗口关闭事件")
        try:
            self.task_manager_tab.shutdown()
        except Exception:
            pass
        self.destroy()

    def _ignore_close_hotkey(self, _event=None):
        self._write_gui_event_log("已拦截关闭快捷键")
        return "break"

    def _write_gui_event_log(self, message: str) -> None:
        try:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_dir = get_log_dir()
            log_dir.mkdir(parents=True, exist_ok=True)
            with (log_dir / "gui_event.log").open("a", encoding="utf-8") as file_obj:
                file_obj.write(f"{stamp} [GUI事件] {message}\n")
        except Exception:
            pass

    def _handle_callback_exception(self, exc, val, tb):
        detail = "".join(traceback.format_exception(exc, val, tb))
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "gui_error.log"
        with log_path.open("a", encoding="utf-8") as file_obj:
            file_obj.write(f"{stamp} [GUI异常]\n{detail}\n")
        messagebox.showerror("程序异常", f"界面操作发生异常，错误已记录：\n{log_path}")


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
