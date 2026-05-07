from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont

from core.browser_controller import BrowserController
from publisher_login.router import get_supported_login_sites


class OnboardingWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.font_name = self._pick_font()
        self.colors = {
            "bg": "#edf2f7",
            "surface": "#ffffff",
            "line": "#dbe4f0",
            "text": "#1f2937",
            "muted": "#64748b",
            "brand": "#1e3a8a",
            "brand_soft": "#dbeafe",
            "btn_bg": "#f8fafc",
        }
        self._completed = False
        self._step = 1
        self._sites = get_supported_login_sites()
        self._build_window()
        self._render_step()

    def run(self) -> bool:
        self.mainloop()
        return self._completed

    def _pick_font(self) -> str:
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

    def _build_window(self) -> None:
        width, height = 1150, 650
        self.title("AutoPaper - 引导")
        self.minsize(width, height)
        self._center_window(width, height)
        self.configure(bg=self.colors["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root_card = tk.Frame(
            self,
            bg=self.colors["surface"],
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )
        self.root_card.pack(fill="both", expand=True, padx=18, pady=16)

    def _center_window(self, width: int, height: int) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = max(0, (screen_w - width) // 2)
        pos_y = max(0, (screen_h - height) // 2)
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

    def _render_step(self) -> None:
        for child in self.root_card.winfo_children():
            child.destroy()
        if self._step == 1:
            self._render_step_one()
        else:
            self._render_step_two()

    def _render_step_one(self) -> None:
        tk.Label(
            self.root_card,
            text="欢迎使用 AutoPaper",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 29, "bold"),
        ).pack(pady=(36, 10))

        tk.Label(
            self.root_card,
            text="开始前请先检查系统分辨率设置",
            bg=self.colors["surface"],
            fg=self.colors["muted"],
            font=(self.font_name, 13),
        ).pack()

        box = tk.Frame(self.root_card, bg=self.colors["surface"])
        box.pack(fill="both", expand=True, padx=42, pady=(26, 20))

        self._resolution_card(box, "Windows", "1920 × 1080")
        self._resolution_card(box, "macOS", "1280 × 820")

        footer = tk.Frame(self.root_card, bg=self.colors["surface"])
        footer.pack(side="bottom", fill="x", padx=36, pady=(0, 22))
        tk.Button(
            footer,
            text="下一步",
            font=(self.font_name, 15, "bold"),
            bg=self.colors["surface"],
            fg=self.colors["brand"],
            activebackground="#e8eefc",
            activeforeground=self.colors["brand"],
            relief="flat",
            bd=0,
            padx=30,
            pady=10,
            command=self._go_step_two,
            takefocus=False,
            cursor="hand2",
        ).pack(anchor="center")

    def _resolution_card(self, parent: tk.Widget, os_name: str, resolution: str) -> None:
        card = tk.Frame(
            parent,
            bg=self.colors["btn_bg"],
            highlightthickness=1,
            highlightbackground=self.colors["line"],
            padx=20,
            pady=16,
        )
        card.pack(fill="x", pady=8)
        tk.Label(
            card,
            text=os_name,
            bg=self.colors["btn_bg"],
            fg=self.colors["brand"],
            font=(self.font_name, 18, "bold"),
            width=10,
            anchor="w",
        ).pack(side="left")
        tk.Label(
            card,
            text=f"请将分辨率设为 {resolution}",
            bg=self.colors["btn_bg"],
            fg=self.colors["text"],
            font=(self.font_name, 19, "bold"),
            anchor="w",
        ).pack(side="left", padx=(14, 0))

    def _render_step_two(self) -> None:
        top = tk.Frame(self.root_card, bg=self.colors["surface"])
        top.pack(fill="x", padx=34, pady=(28, 10))

        tk.Label(
            top,
            text="步骤 2 / 2",
            bg=self.colors["brand_soft"],
            fg=self.colors["brand"],
            font=(self.font_name, 11, "bold"),
            padx=12,
            pady=5,
        ).pack(anchor="center")

        tk.Label(
            top,
            text="请先在 Chrome 浏览器中登录以下网站",
            bg=self.colors["surface"],
            fg=self.colors["text"],
            font=(self.font_name, 22, "bold"),
        ).pack(pady=(14, 8))

        tk.Label(
            top,
            text="点击站点按钮可直接打开登录入口，完成后点击下一步进入主界面",
            bg=self.colors["surface"],
            fg=self.colors["muted"],
            font=(self.font_name, 12),
        ).pack()

        grid = tk.Frame(self.root_card, bg=self.colors["surface"])
        grid.pack(fill="x", padx=30, pady=(12, 6))

        columns = 4
        rows = max(1, math.ceil(len(self._sites) / columns))
        for col in range(columns):
            grid.grid_columnconfigure(col, weight=1, uniform="site")

        for idx, site in enumerate(self._sites):
            label = str(site.get("label", "") or "").strip()
            row = idx // columns
            col = idx % columns
            btn = _RoundedSiteButton(
                grid,
                text=label,
                font_name=self.font_name,
                command=lambda item=site: self._open_site(item),
            )
            btn.grid(row=row, column=col, padx=8, pady=4)

        footer = tk.Frame(self.root_card, bg=self.colors["surface"])
        footer.pack(side="bottom", fill="x", padx=34, pady=(0, 22))
        nav = tk.Frame(footer, bg=self.colors["surface"])
        nav.pack(anchor="center")
        tk.Button(
            nav,
            text="上一步",
            font=(self.font_name, 15, "bold"),
            bg=self.colors["surface"],
            fg=self.colors["brand"],
            activebackground="#e8eefc",
            activeforeground=self.colors["brand"],
            relief="flat",
            bd=0,
            padx=30,
            pady=10,
            command=self._go_step_one,
            takefocus=False,
            cursor="hand2",
        ).pack(side="left", padx=(0, 12))
        tk.Button(
            nav,
            text="下一步",
            font=(self.font_name, 15, "bold"),
            bg=self.colors["surface"],
            fg=self.colors["brand"],
            activebackground="#e8eefc",
            activeforeground=self.colors["brand"],
            relief="flat",
            bd=0,
            padx=30,
            pady=10,
            command=self._finish,
            takefocus=False,
            cursor="hand2",
        ).pack(side="left")

    def _go_step_two(self) -> None:
        self._step = 2
        self._render_step()

    def _go_step_one(self) -> None:
        self._step = 1
        self._render_step()

    def _open_site(self, site: dict[str, str]) -> None:
        target = str(site.get("open_url", "")).strip()
        label = str(site.get("label", "")).strip() or target
        if not target:
            messagebox.showwarning("提示", f"{label} 未配置可打开的网址")
            return
        try:
            BrowserController().open_tab(target)
        except Exception as exc:
            messagebox.showwarning("提示", f"打开网站失败：{label}\n{exc}")

    def _finish(self) -> None:
        self._completed = True
        self.destroy()

    def _on_close(self) -> None:
        self._completed = False
        self.destroy()


class _RoundedSiteButton(tk.Canvas):
    def __init__(self, master, text: str, font_name: str, command):
        super().__init__(
            master,
            width=220,
            height=46,
            bg="#ffffff",
            highlightthickness=0,
            bd=0,
            relief="flat",
            takefocus=False,
            cursor="hand2",
        )
        self._command = command
        self._normal_fill = "#f8fafc"
        self._hover_fill = "#e8eefc"
        self._text_color = "#1e3a8a"
        self._font = (font_name, 13, "bold")
        self._draw(self._normal_fill, text)
        self.bind("<Enter>", lambda _e: self._draw(self._hover_fill, text))
        self.bind("<Leave>", lambda _e: self._draw(self._normal_fill, text))

    def _draw(self, fill: str, text: str) -> None:
        self.delete("all")
        x1, y1, x2, y2, r = 2, 2, 218, 44, 14
        tag = ("hit",)
        self.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline=fill, tags=tag)
        self.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline=fill, tags=tag)
        self.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline=fill, tags=tag)
        self.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline=fill, tags=tag)
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=fill, tags=tag)
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=fill, tags=tag)
        self.create_line(x1 + r, y1, x2 - r, y1, fill="#d5dfed", tags=tag)
        self.create_line(x1 + r, y2, x2 - r, y2, fill="#d5dfed", tags=tag)
        self.create_line(x1, y1 + r, x1, y2 - r, fill="#d5dfed", tags=tag)
        self.create_line(x2, y1 + r, x2, y2 - r, fill="#d5dfed", tags=tag)
        self.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="arc", outline="#d5dfed", tags=tag)
        self.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="arc", outline="#d5dfed", tags=tag)
        self.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="arc", outline="#d5dfed", tags=tag)
        self.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="arc", outline="#d5dfed", tags=tag)
        self.create_text(110, 23, text=text, font=self._font, fill=self._text_color, tags=tag)
        self.tag_bind("hit", "<Button-1>", self._on_click)

    def _on_click(self, _event=None) -> None:
        if callable(self._command):
            self._command()
