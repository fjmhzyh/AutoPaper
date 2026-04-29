import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk


class ConfigTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f3f5f9")
        self.project_root = Path(__file__).resolve().parents[1]
        self.config_dir = self.project_root / "config"
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
        }

        self.config_files: list[Path] = []
        self.file_var = tk.StringVar()
        self.status_var = tk.StringVar(value="就绪")
        self.dirty = False
        self._internal_update = False

        self._setup_theme()
        self._build_ui()
        self.refresh_file_list()

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
            text="系统配置",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=(self.font_name, 24, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="配置目录：config/（TOML）",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=(self.font_name, 12),
        ).pack(anchor="w", pady=(4, 0))

        top_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        top_card.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 14))
        top_card.grid_columnconfigure(1, weight=1)

        tk.Label(
            top_card,
            text="当前配置文件：",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 13, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(2, 8))

        self.file_combo = ttk.Combobox(
            top_card,
            textvariable=self.file_var,
            state="readonly",
            font=(self.font_name, 12),
        )
        self.file_combo.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.file_combo.bind("<<ComboboxSelected>>", self._on_select_file)

        ttk.Button(top_card, text="刷新", style="Ghost.TButton", command=self.refresh_file_list).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(top_card, text="打开目录", style="Ghost.TButton", command=self._open_config_dir).grid(
            row=0, column=3, padx=(0, 8)
        )
        ttk.Button(top_card, text="保存", style="Primary.TButton", command=self.save_current_file).grid(
            row=0, column=4
        )

        editor_card = ttk.Frame(self, style="Card.TFrame", padding=14)
        editor_card.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 24))
        editor_card.grid_columnconfigure(0, weight=1)
        editor_card.grid_rowconfigure(0, weight=1)

        editor_frame = tk.Frame(editor_card, bg=self.colors["surface"])
        editor_frame.grid(row=0, column=0, sticky="nsew")
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(0, weight=1)

        self.editor = tk.Text(
            editor_frame,
            wrap="none",
            bd=0,
            relief="flat",
            font=(self.font_name, 12),
            bg=self.colors["surface"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            undo=True,
        )
        self.editor.grid(row=0, column=0, sticky="nsew")
        self.editor.bind("<<Modified>>", self._on_editor_modified)
        self.editor.bind("<Control-s>", self._on_ctrl_save)
        self.editor.bind("<Command-s>", self._on_ctrl_save)

        x_scroll = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.editor.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        y_scroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.editor.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.editor.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

        status_bar = tk.Frame(editor_card, bg=self.colors["surface"])
        status_bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        status_bar.grid_columnconfigure(0, weight=1)
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            bg=self.colors["surface"],
            fg=self.colors["muted"],
            font=(self.font_name, 11),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

    def refresh_file_list(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        old = self.file_var.get()
        patterns = ("*.toml",)
        files = []
        for pattern in patterns:
            files.extend(self.config_dir.glob(pattern))
        self.config_files = sorted(set(files), key=lambda p: p.name.lower())

        names = [item.name for item in self.config_files]
        self.file_combo["values"] = names
        if not names:
            self.file_var.set("")
            self._set_editor_text("")
            self.status_var.set("config 目录下暂无配置文件")
            return

        target = old if old in names else ("config.toml" if "config.toml" in names else names[0])
        self.file_var.set(target)
        self._load_selected_file()

    def _on_select_file(self, _event):
        self._load_selected_file()

    def _selected_path(self) -> Path | None:
        current = self.file_var.get().strip()
        for path in self.config_files:
            if path.name == current:
                return path
        return None

    def _load_selected_file(self):
        path = self._selected_path()
        if not path:
            self._set_editor_text("")
            self.status_var.set("未选中配置文件")
            return

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            self._set_editor_text("")
            self.status_var.set(f"读取失败：{exc}")
            return

        self._set_editor_text(content)
        self.dirty = False
        self.status_var.set(f"已加载：{path.name}")

    def save_current_file(self):
        path = self._selected_path()
        if not path:
            messagebox.showerror("保存失败", "未选中配置文件")
            return

        content = self.editor.get("1.0", "end-1c")
        try:
            path.write_text(content, encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("保存失败", f"写入失败：{exc}")
            return

        self.dirty = False
        self.status_var.set(f"已保存：{path.name}")
        messagebox.showinfo("保存成功", f"{path.name} 已保存")

    def _set_editor_text(self, content: str):
        self._internal_update = True
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.editor.edit_modified(False)
        self._internal_update = False

    def _on_editor_modified(self, _event):
        if self._internal_update:
            self.editor.edit_modified(False)
            return
        if self.editor.edit_modified():
            self.dirty = True
            current = self.file_var.get().strip() or "未命名"
            self.status_var.set(f"已修改：{current}（Ctrl/Cmd + S 保存）")
            self.editor.edit_modified(False)

    def _on_ctrl_save(self, _event):
        self.save_current_file()
        return "break"

    def _open_config_dir(self):
        target = str(self.config_dir.resolve())
        try:
            if sys.platform.startswith("win"):
                os.startfile(target)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target])
            else:
                subprocess.Popen(["xdg-open", target])
        except Exception as exc:
            messagebox.showerror("打开失败", f"无法打开目录：{exc}")
