from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("sciencedirect.com"):
        return True

    open_access, full_access, purchase_pdf = utils.check_keywords_exist(
        ["open access", "full access", "purchase pdf"]
    )
    if open_access or full_access:
        logger.info("[网站登陆] ScienceDirect 文章为 open access，无需登陆")
        return True

    if purchase_pdf:
        return _dispatch_login()

    return _dispatch_login()


def _dispatch_login() -> bool:
    login_button_image = utils.photo("sciencedirect.com1.png")
    gui.click(700, 1000)
    logger.info("[网站登陆] 正在查找 ScienceDirect 登录按钮")
    button_pos = utils.locate_image(login_button_image)
    if not button_pos:
        logger.info("[网站登陆] 未找到 ScienceDirect 登录按钮")
        return False

    gui.click(button_pos)
    time.sleep(10)
    gui.press("enter")
    time.sleep(10)
    return True
