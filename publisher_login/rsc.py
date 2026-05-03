from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("rsc.org"):
        return True

    open_access, access_provided_by,using_your_instituition, download_this_article= utils.check_keywords_exist([
        "This article is Open Access",
        "access provided by",
        "Using your institution credentials",
        "download this article"
    ])

    if using_your_instituition:
        return _login_use_hotkey()
    
    if access_provided_by and download_this_article:
        logger.info("[网站登陆] 已登陆，无需再次登陆")
        return True
    
    if open_access:
        logger.info("[网站登陆] 当前文章为 open access，无需登陆")
        return True
    



def _login_use_hotkey() -> bool:
    # 点击登陆按钮
    utils.search_keyword_and_foucus('Using your institution credentials')
    gui.press('enter',2,0.2)

    # 等待页面加载
    time.sleep(30)

    # 点击View all institutions
    utils.search_keyword_and_foucus("View all institutions")
    gui.press('enter',2,0.2)

    # 点击浙江大学
    utils.search_keyword_and_foucus("zhejiang university")
    gui.press('enter',2,0.2)

    # 等待页面加载
    time.sleep(20)
    utils.get_current_url()
    # 点击登陆
    gui.press('enter',2,0.2)
    return True

def _login_use_photo() -> bool:

    logger.info("[网站登陆] 执行 RSC 登录流程")
    login_button_img = utils.photo("pubs.rsc.org1.png")
    submit_button_img = utils.photo("pubs.rsc.org2.png")
    final_button_img = utils.photo("pubs.rsc.org3.png")

    first_pos = utils.locate_image(login_button_img)
    if not first_pos:
        logger.info("[网站登陆] 未找到 RSC 登录按钮1")
        return False
    gui.click(first_pos)
    time.sleep(30)

    second_pos = utils.locate_image(submit_button_img)
    if not second_pos:
        logger.info("[网站登陆] 未找到 RSC 登录按钮2")
        return False
    gui.click(second_pos)
    time.sleep(5)

    utils.search_keyword("zhejiang")
    time.sleep(2)
    third_pos = utils.locate_image(final_button_img)
    if not third_pos:
        logger.info("[网站登陆] 未找到 RSC 登录按钮3")
        return False

    gui.click(third_pos)
    time.sleep(15)
    gui.press("enter")
    time.sleep(5)
    return True