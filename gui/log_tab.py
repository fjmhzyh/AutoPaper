import tkinter as tk
from tkinter import font as tkfont


class LogTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f3f5f9")
        self.font_name = self._pick_font()
        self._build_ui()

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

    def _build_ui(self):
        container = tk.Frame(self, bg="#f3f5f9", padx=28, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="系统日志",
            bg="#f3f5f9",
            fg="#1f2937",
            font=(self.font_name, 24, "bold"),
        ).pack(anchor="w")
