from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path
from typing import Any


class BrowserController:
    def __init__(self, backend: Any | None = None):
        self._backend = backend

    def open_tab(self, url: str) -> None:
        target = str(url or "").strip()
        if not target:
            raise ValueError("URL must be a non-empty string")
        browser = self._chrome_browser()
        ok = browser.open_new_tab(target)
        if not ok:
            raise RuntimeError(f"Failed to open URL in Chrome: {target}")

    def close_tab(self) -> None:
        backend = self._backend_or_raise()
        backend.hotkey(self._modifier(), "w")

    def _backend_or_raise(self) -> Any:
        if self._backend is not None:
            return self._backend
        try:
            import pyautogui  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError("pyautogui is not installed") from exc
        pyautogui.FAILSAFE = True
        self._backend = pyautogui
        return self._backend

    def _chrome_browser(self):
        chrome_path = self._chrome_path()
        webbrowser.register(
            "autopaper-chrome",
            None,
            webbrowser.BackgroundBrowser(chrome_path),
            preferred=True,
        )
        return webbrowser.get("autopaper-chrome")

    @staticmethod
    def _modifier() -> str:
        return "command" if sys.platform == "darwin" else "ctrl"

    @staticmethod
    def _chrome_path() -> str:
        if sys.platform == "darwin":
            path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            return path

        if sys.platform.startswith("win"):
            candidates = [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
            ]
            for path in candidates:
                if path and Path(path).exists():
                    return path
            return "chrome"

        return "google-chrome"
