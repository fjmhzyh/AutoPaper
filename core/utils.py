from __future__ import annotations

import sys
import time
from pathlib import Path

from core import gui


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
    _write_clipboard("")
    gui.hotkey("select_all")
    gui.hotkey("copy")
    time.sleep(0.1)
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
    gui.hotkey("focus_address_bar")
    time.sleep(0.5)
    gui.hotkey("copy")
    time.sleep(1)
    gui.press("esc")
    return _read_clipboard()


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
