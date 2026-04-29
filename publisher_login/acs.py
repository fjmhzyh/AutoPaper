from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("acs.org"):
        return True

    logger.info("[网站登陆] 执行 ACS 登录流程")
    access_through, zhejiang_university, open_pdf = utils.check_keywords_exist(
        ["access through", "zhejiang uniersity", "open pdf"]
    )

    if access_through and zhejiang_university:
        if _click_login_btn():
            time.sleep(15)
            _press("enter")
            time.sleep(10)
            return True
        return False

    if access_through and not open_pdf:
        if _click_login_btn():
            time.sleep(30)
            utils.search_keyword("Search By University")
            _press("tab")
            gui.hotkey("shift_tab")
            gui.write("Zhejiang University", interval=0.1)
            time.sleep(3)
            _press("down", 1, 0.2)
            _press("enter", 1, 0.2)
            logger.info("[网站登陆] 等待跳转到浙大登陆页")
            time.sleep(15)
            _press("enter")
            time.sleep(20)
            return True
        return False

    logger.info("[网站登陆] 当前文章无需登陆")
    return True


def _click_login_btn() -> bool:
    login_button_image = utils.photo("pubs.acs.org1.png")
    logger.info("[网站登陆] 正在查找 ACS 登录按钮")
    button_pos = utils.locate_image(login_button_image)
    if not button_pos:
        logger.info("[网站登陆] 未找到 ACS 登录按钮，尝试关键字登录")
        utils.search_keyword("access through")
        time.sleep(0.5)
        _press("esc", 1, 1)
        _press("enter", 2, 1)
        return True

    gui.click(button_pos)
    return True


def _press(key: str, times: int = 1, interval: float = 0.0) -> None:
    for _ in range(max(1, times)):
        gui.press(key)
        if interval > 0:
            time.sleep(interval)
