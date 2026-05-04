from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("nature.com"):
        return True

    access_through_institution,buy_or_subscribe,download_pdf = utils.check_keywords_exist([
        "access through your institution",
        "Buy or subscribe",
        "download pdf"
    ])
    if download_pdf:
        logger.info("[网站登陆] 该文章 无需登陆，可直接下载")
        return True
    if access_through_institution or buy_or_subscribe:
        logger.info("[网站登陆] 该文章需要登陆下载")
        return _login_use_hotkey()
    return True

def _login_use_hotkey()->bool:
    logger.info("[网站登陆] 开始执行 nature 登录流程")
    
    # 查找登陆按钮
    utils.search_keyword_and_foucus('access through your institution')
    # 点击登陆按钮
    gui.press('enter',2,0.2)
    time.sleep(30)
    # 找到输入框
    utils.search_keyword_and_foucus("Find your institution")
    gui.press('tab')
    # 在输入框输入浙大，并下拉9次选中
    time.sleep(40)
    gui.write("Zhejiang University", interval=0.1)
    time.sleep(15)
    gui.press("down", 9, 0.1)
    gui.press("enter", 1, 0.2)
    # 跳转到浙大登陆页，点击登陆
    time.sleep(20)
    gui.press("enter")
    time.sleep(30)
    return True







