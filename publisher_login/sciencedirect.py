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

    purchase_pdf, access_through,download_full_issue= utils.check_keywords_exist(
        [
            "purchase pdf",
            "access through",
            "Download full issue"
        ]
    )
    
    logger.info(f"zj:{access_through} issue:{download_full_issue} pdf:{purchase_pdf}")

    # 如果存在access_through，则需要登陆下载
    if access_through and purchase_pdf:
        utils.search_keyword_and_foucus('purchase pdf')
        gui.hotkey('shift_tab')
        gui.press('enter',2,0.1)
        time.sleep(30)
        gui.press('enter',2,1)
        time.sleep(30)
        return True
    
    # 开源或者已登陆
    if download_full_issue:
        logger.info("[网站登陆] 当前文章，无需执行登陆操作")
        return True
    
def _login_use_hotkey()->bool:
    return True

def _login_use_photo() -> bool:
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
