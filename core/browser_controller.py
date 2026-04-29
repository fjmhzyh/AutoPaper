from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from core.app_config import get_config


logger = logging.getLogger(__name__)


class BrowserErrorCode:
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    LAUNCH_FAILED = "LAUNCH_FAILED"
    URL_OPEN_FAILED = "URL_OPEN_FAILED"
    TAB_OPEN_FAILED = "TAB_OPEN_FAILED"
    TAB_CLOSE_FAILED = "TAB_CLOSE_FAILED"
    TAB_FOCUS_FAILED = "TAB_FOCUS_FAILED"
    TAB_SWITCH_FAILED = "TAB_SWITCH_FAILED"
    TAB_REFRESH_FAILED = "TAB_REFRESH_FAILED"
    URL_COPY_FAILED = "URL_COPY_FAILED"


class BrowserAutomationError(RuntimeError):
    def __init__(self, code: str, message: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if not self.context:
            return f"[{self.code}] {self.message}"
        return f"[{self.code}] {self.message} | context={self.context}"


@dataclass
class BrowserConfig:
    prefer: str = "chrome"
    launch_wait_sec: float = 3.0
    action_interval_sec: float = 0.2


class BrowserController:
    """Cross-platform browser operations controller for pyautogui-based automation."""

    def __init__(
        self,
        project_root: str | Path | None = None,
        backend: Any | None = None,
        config_path: str | Path | None = None,
    ):
        self.project_root = (
            Path(project_root).resolve()
            if project_root is not None
            else Path(__file__).resolve().parents[1]
        )
        self.config_path = (
            Path(config_path).resolve()
            if config_path is not None
            else self.project_root / "config" / "config.toml"
        )
        self._backend = backend
        self.config = self._load_config(self.config_path)
        logger.info(
            "BrowserController initialized",
            extra={
                "prefer": self.config.prefer,
                "launch_wait_sec": self.config.launch_wait_sec,
                "action_interval_sec": self.config.action_interval_sec,
            },
        )

    # ------------------------------- Public API ------------------------------- #
    def launch_browser(self, url: str | None = None) -> None:
        start = time.time()
        target_url = (url or "").strip() or "about:blank"
        logger.info("launch_browser called", extra={"url": target_url, "prefer": self.config.prefer})

        try:
            launched = False
            if self.config.prefer.lower() == "chrome":
                launched = self._launch_chrome(target_url)

            if not launched:
                launched = self._launch_default_browser(target_url)

            if not launched:
                raise BrowserAutomationError(
                    BrowserErrorCode.LAUNCH_FAILED,
                    "Failed to launch browser by preferred and fallback strategies",
                    context={"url": target_url, "prefer": self.config.prefer},
                )

            self._sleep(self.config.launch_wait_sec)
            logger.info(
                "launch_browser success",
                extra={"url": target_url, "elapsed_sec": round(time.time() - start, 3)},
            )
        except BrowserAutomationError:
            raise
        except Exception as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.LAUNCH_FAILED,
                "Unexpected error while launching browser",
                context={"url": target_url, "prefer": self.config.prefer, "error": str(exc)},
            ) from exc

    def is_running(self) -> bool:
        try:
            if sys.platform == "darwin":
                return self._command_ok(["pgrep", "-x", "Google Chrome"]) or self._command_ok(["pgrep", "-x", "Safari"])

            if sys.platform.startswith("win"):
                output = subprocess.check_output(["tasklist"], text=True, stderr=subprocess.DEVNULL)
                text = output.lower()
                return "chrome.exe" in text or "msedge.exe" in text or "firefox.exe" in text

            # linux / other unix
            return self._command_ok(["pgrep", "-x", "chrome"]) or self._command_ok(["pgrep", "-x", "chromium"])
        except Exception:
            return False

    def ensure_ready(self) -> None:
        if self.is_running():
            logger.info("ensure_ready: browser is already running")
            self._activate_browser_window()
            self._sleep(max(self.config.action_interval_sec, 0.1))
            return
        logger.info("ensure_ready: browser not running, launching")
        self.launch_browser()
        self._sleep(self.config.launch_wait_sec)
        self._activate_browser_window()
        self._sleep(max(self.config.action_interval_sec, 0.1))

    def open_url(self, url: str) -> None:
        target = self._validate_url(url)
        start = time.time()
        logger.info("open_url called", extra={"url": target})

        try:
            self._hotkey(self._modifier(), "l")
            self._sleep(self.config.action_interval_sec)
            self._typewrite(target)
            self._press("enter")
            self._sleep(self.config.action_interval_sec)
            logger.info("open_url success", extra={"url": target, "elapsed_sec": round(time.time() - start, 3)})
        except BrowserAutomationError:
            raise
        except Exception as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.URL_OPEN_FAILED,
                "Failed to open URL in current browser tab",
                context={"url": target, "error": str(exc)},
            ) from exc

    def new_tab(self, url: str | None = None) -> None:
        start = time.time()
        target = (url or "").strip()
        logger.info("new_tab called", extra={"url": target})

        validated_target = self._validate_url(target) if target else ""

        last_error: Exception | None = None
        for attempt in (1, 2):
            try:
                if attempt == 2:
                    logger.warning(
                        "new_tab first attempt failed, ensuring browser ready before retry",
                        extra={"url": target or None},
                    )
                    self.ensure_ready()

                self._hotkey(self._modifier(), "t")
                self._sleep(self.config.action_interval_sec)
                if validated_target:
                    self._typewrite(validated_target)
                    self._press("enter")
                    self._sleep(self.config.action_interval_sec)
                logger.info(
                    "new_tab success",
                    extra={
                        "url": target or None,
                        "attempt": attempt,
                        "elapsed_sec": round(time.time() - start, 3),
                    },
                )
                return
            except Exception as exc:
                last_error = exc
                if attempt == 1:
                    logger.warning(
                        "new_tab attempt failed",
                        extra={"url": target or None, "attempt": attempt, "error": str(exc)},
                    )
                    continue
                logger.warning(
                    "new_tab retry failed",
                    extra={"url": target or None, "attempt": attempt, "error": str(exc)},
                )

        raise BrowserAutomationError(
            BrowserErrorCode.TAB_OPEN_FAILED,
            "Failed to open new tab",
            context={"url": target or None, "error": str(last_error) if last_error else "unknown"},
        ) from last_error

    def close_current_tab(self) -> None:
        start = time.time()
        logger.info("close_current_tab called")
        try:
            self._hotkey(self._modifier(), "w")
            self._sleep(self.config.action_interval_sec)
            logger.info("close_current_tab success", extra={"elapsed_sec": round(time.time() - start, 3)})
        except BrowserAutomationError:
            raise
        except Exception as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.TAB_CLOSE_FAILED,
                "Failed to close current tab",
                context={"error": str(exc)},
            ) from exc

    def focus_tab(self, index: int) -> None:
        start = time.time()
        if not isinstance(index, int) or index < 1 or index > 9:
            raise BrowserAutomationError(
                BrowserErrorCode.INVALID_ARGUMENT,
                "Tab index must be an integer between 1 and 9",
                context={"index": index},
            )
        logger.info("focus_tab called", extra={"index": index})

        try:
            self._hotkey(self._modifier(), str(index))
            self._sleep(self.config.action_interval_sec)
            logger.info("focus_tab success", extra={"index": index, "elapsed_sec": round(time.time() - start, 3)})
        except BrowserAutomationError:
            raise
        except Exception as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.TAB_FOCUS_FAILED,
                "Failed to focus target tab",
                context={"index": index, "error": str(exc)},
            ) from exc

    def switch_tab(self, direction: Literal["next", "prev"] | str) -> None:
        start = time.time()
        value = str(direction).strip().lower()
        if value not in {"next", "prev"}:
            raise BrowserAutomationError(
                BrowserErrorCode.INVALID_ARGUMENT,
                "direction must be 'next' or 'prev'",
                context={"direction": direction},
            )
        logger.info("switch_tab called", extra={"direction": value})

        try:
            if value == "next":
                self._hotkey(self._modifier(), "tab")
            else:
                self._hotkey(self._modifier(), "shift", "tab")
            self._sleep(self.config.action_interval_sec)
            logger.info("switch_tab success", extra={"direction": value, "elapsed_sec": round(time.time() - start, 3)})
        except BrowserAutomationError:
            raise
        except Exception as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.TAB_SWITCH_FAILED,
                "Failed to switch tab",
                context={"direction": value, "error": str(exc)},
            ) from exc

    def refresh_page(self) -> None:
        start = time.time()
        logger.info("refresh_page called")
        try:
            self._hotkey(self._modifier(), "r")
            self._sleep(self.config.action_interval_sec)
            logger.info("refresh_page success", extra={"elapsed_sec": round(time.time() - start, 3)})
        except BrowserAutomationError:
            raise
        except Exception as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.TAB_REFRESH_FAILED,
                "Failed to refresh current page",
                context={"error": str(exc)},
            ) from exc

    def copy_current_tab_url(self) -> str:
        start = time.time()
        logger.info("copy_current_tab_url called")
        try:
            self._hotkey(self._modifier(), "l")
            self._sleep(self.config.action_interval_sec)
            self._hotkey(self._modifier(), "c")
            self._sleep(self.config.action_interval_sec)
            url = self._read_clipboard_text().strip()
            if not url:
                raise BrowserAutomationError(
                    BrowserErrorCode.URL_COPY_FAILED,
                    "Clipboard URL is empty",
                    context={},
                )
            logger.info("copy_current_tab_url success", extra={"elapsed_sec": round(time.time() - start, 3)})
            return url
        except BrowserAutomationError:
            raise
        except Exception as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.URL_COPY_FAILED,
                "Failed to copy current tab URL",
                context={"error": str(exc)},
            ) from exc

    # ------------------------------- Internals ------------------------------- #
    def _modifier(self) -> str:
        return "command" if sys.platform == "darwin" else "ctrl"

    def _sleep(self, seconds: float) -> None:
        if seconds <= 0:
            return
        time.sleep(seconds)

    def _validate_url(self, url: str) -> str:
        text = str(url or "").strip()
        if not text:
            raise BrowserAutomationError(
                BrowserErrorCode.INVALID_ARGUMENT,
                "URL must be a non-empty string",
                context={"url": url},
            )
        return text

    def _backend_or_raise(self) -> Any:
        if self._backend is not None:
            return self._backend

        try:
            import pyautogui  # type: ignore
        except ModuleNotFoundError as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.BACKEND_UNAVAILABLE,
                "pyautogui is not installed",
                context={"hint": "pip install pyautogui"},
            ) from exc

        # Runtime defaults to improve stability.
        pyautogui.PAUSE = max(float(self.config.action_interval_sec), 0.0)
        pyautogui.FAILSAFE = True
        self._backend = pyautogui
        return self._backend

    def _hotkey(self, *keys: str) -> None:
        backend = self._backend_or_raise()
        backend.hotkey(*keys)

    def _typewrite(self, text: str) -> None:
        backend = self._backend_or_raise()
        interval = min(max(float(self.config.action_interval_sec) / 2.0, 0.0), 0.3)
        backend.typewrite(text, interval=interval)

    def _press(self, key: str) -> None:
        backend = self._backend_or_raise()
        backend.press(key)

    @staticmethod
    def _read_clipboard_text() -> str:
        try:
            import pyperclip  # type: ignore
        except ModuleNotFoundError as exc:
            raise BrowserAutomationError(
                BrowserErrorCode.BACKEND_UNAVAILABLE,
                "pyperclip is not installed",
                context={"hint": "pip install pyperclip"},
            ) from exc
        return str(pyperclip.paste() or "")

    def _launch_chrome(self, url: str) -> bool:
        commands = self._chrome_launch_commands(url)
        for cmd in commands:
            try:
                proc = subprocess.Popen(cmd)
                # Some launch commands (notably macOS `open -a`) can fail immediately.
                # Treat immediate non-zero exit as launch failure so we can fallback.
                self._sleep(0.15)
                return_code = proc.poll()
                if return_code not in (None, 0):
                    logger.warning(
                        "launch chrome command failed quickly",
                        extra={"command": cmd, "return_code": return_code},
                    )
                    continue
                logger.info("launch chrome command executed", extra={"command": cmd})
                return True
            except Exception as exc:
                logger.warning(
                    "launch chrome command failed",
                    extra={"command": cmd, "error": str(exc)},
                )
                continue
        return False

    def _launch_default_browser(self, url: str) -> bool:
        try:
            ok = webbrowser.open_new(url)
            logger.info("fallback default browser open", extra={"url": url, "ok": bool(ok)})
            return bool(ok)
        except Exception:
            return False

    def _chrome_launch_commands(self, url: str) -> list[list[str]]:
        if sys.platform == "darwin":
            return [["open", "-a", "Google Chrome", url]]

        if sys.platform.startswith("win"):
            candidates = [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
            ]
            commands: list[list[str]] = []
            for exe in candidates:
                if exe and os.path.exists(exe):
                    commands.append([exe, url])
            commands.append(["cmd", "/c", "start", "", "chrome", url])
            return commands

        # Linux / other unix.
        return [
            ["google-chrome", url],
            ["google-chrome-stable", url],
            ["chromium-browser", url],
            ["chromium", url],
        ]

    def _load_config(self, path: Path) -> BrowserConfig:
        config = BrowserConfig()
        cfg = get_config(path)
        prefer = cfg.get_str("browser.prefer", default="")
        if prefer:
            config.prefer = prefer
        config.launch_wait_sec = max(
            0.0,
            cfg.get_float("browser.launch_wait_sec", default=config.launch_wait_sec),
        )
        config.action_interval_sec = max(
            0.0,
            cfg.get_float("browser.action_interval_sec", default=config.action_interval_sec),
        )
        return config

    def _activate_browser_window(self) -> None:
        try:
            if sys.platform == "darwin":
                apps: list[str]
                if self.config.prefer.lower() == "chrome":
                    apps = ["Google Chrome", "Safari"]
                else:
                    apps = ["Safari", "Google Chrome"]
                for app in apps:
                    result = subprocess.run(
                        ["osascript", "-e", f'tell application "{app}" to activate'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    if result.returncode == 0:
                        logger.info("activate browser window success", extra={"app": app})
                        return
                logger.warning("activate browser window failed")
                return

            # Windows/Linux: keep no-op for now.
            return
        except Exception as exc:
            logger.warning("activate browser window error", extra={"error": str(exc)})

    @staticmethod
    def _command_ok(cmd: list[str]) -> bool:
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            return result.returncode == 0
        except Exception:
            return False
