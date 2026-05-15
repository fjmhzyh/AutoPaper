from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from core import gui


logger = logging.getLogger(__name__)


def is_mac() -> bool:
    return sys.platform == "darwin"


def photo(name: str) -> str:
    width, height = _screen_size()
    profile = f"{'mac' if is_mac() else 'win'}_{width}_{height}"
    root = Path(__file__).resolve().parents[1]
    path = (root / "photos" / profile / name).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Photo not found for profile '{profile}': {name}")
    return str(path)


def check_keywords_exist(keywords: list[str]) -> tuple[bool, ...]:
    gui.press('esc',2,0.5)    
    _write_clipboard("")
    gui.hotkey("select_all")
    gui.hotkey("copy")
    time.sleep(2)
    content = _read_clipboard().lower()
    cancel_select_all()
    return tuple(bool(str(keyword or "").strip()) and str(keyword).lower() in content for keyword in keywords)

def cancel_select_all():
    gui.hotkey('search')
    time.sleep(1) 
    # 3. 输入搜索内容
    gui.write(' ', interval=0.1)
    time.sleep(1)  # 稍微等待，让浏览器完成查找高亮
    gui.press('enter',2,0.5)
    # 4. 按下 ESC 键关闭查找框
    gui.press('esc')

def locate_image(image_path: str, confidence: float = 0.8) -> tuple[int, int] | None:
    location = _locate_on_screen(image_path, confidence)
    if location:
        center_x = location.left + location.width // 2
        center_y = location.top + location.height // 2
        if is_mac():
            center_x //= 2
            center_y //= 2
        return center_x, center_y
    return None


def _locate_on_screen(image_path: str, confidence: float):
    try:
        import pyautogui  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("pyautogui is not installed") from exc
    return pyautogui.locateOnScreen(image_path, confidence=confidence)


def search_keyword_and_clear(keyword)->None:
    gui.hotkey('search')
    time.sleep(1) 
    # 3. 输入搜索内容
    gui.write(keyword, interval=0.1)
    time.sleep(1)  # 稍微等待，让浏览器完成查找高亮
    # 4. 按下 ESC 键关闭查找框
    gui.press('backspace',presses=len(keyword), interval=0.1)
    gui.press('esc')

def search_keyword_and_foucus(keyword)->None:
    gui.hotkey('search')
    time.sleep(1) 
    # 3. 输入搜索内容
    gui.write(keyword, interval=0.1)
    time.sleep(1)  # 稍微等待，让浏览器完成查找高亮
    # 4. 按下 ESC 键关闭查找框
    gui.press('esc')


def get_html_content(wait_sec: float = 5.0) -> str:
    gui.hotkey("view_source")
    time.sleep(max(0.0, float(wait_sec)))
    gui.hotkey("select_all")
    gui.hotkey("copy")
    gui.hotkey("close_tab")
    return _read_clipboard()


def get_current_url() -> str:
    for _ in range(3):
        _write_clipboard("")
        gui.hotkey("focus_address_bar")
        time.sleep(0.8)
        gui.hotkey("copy")
        time.sleep(0.3)
        current_url = _read_clipboard().strip()
        if _looks_like_url(current_url):
            gui.press("esc")
            return current_url
    gui.press("esc")
    logger.warning("[地址解析] 未能从地址栏复制到有效URL")
    return ""


def loop_close_tabs(anchor_url: str = "https://www.baidu.com", max_rounds: int = 10) -> bool:
    target_host = _normalize_host(anchor_url)
    if not target_host:
        return False

    try:
        from core.browser_controller import BrowserController

        BrowserController().open_tab("https://www.qianwen.com/")
        time.sleep(1)
    except Exception as exc:
        logger.warning(f"[标签清理] 聚焦Chrome失败: {exc}")

    rounds = max(1, int(max_rounds))
    for _ in range(rounds):
        current_url = get_current_url()
        if not current_url:
            logger.warning("[标签清理] 未获取到当前URL，停止清理")
            return False
        current_host = _normalize_host(current_url)
        if current_host.endswith("baidu.com") or current_host == target_host:
            return True
        gui.hotkey("close_tab")
        time.sleep(0.3)
    return False


def _normalize_host(url: str) -> str:
    text = str(url or "").strip().lower()
    if not text:
        return ""
    if "://" not in text:
        text = f"https://{text}"
    parsed = urlparse(text)
    return str(parsed.hostname or "").strip().lower()


def _looks_like_url(value: str) -> bool:
    text = str(value or "").strip()
    if not text or any(ch.isspace() for ch in text):
        return False
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def _read_clipboard() -> str:
    try:
        import pyperclip  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("pyperclip is not installed") from exc
    return str(pyperclip.paste() or "")


def _write_clipboard(text: str) -> None:
    try:
        import pyperclip  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("pyperclip is not installed") from exc
    pyperclip.copy(text)


def _screen_size() -> tuple[int, int]:
    size = gui.size()
    return int(size.width), int(size.height)
