from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)

"""
print_download的下载方案，似乎不稳定，有时候明明是成功的，但是保存会失败。tandfonline支持download=true直接下载，后期可以考虑改成直接下载
"""


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("tandfonline.com"):
        return True

    access_provided_by, view_pdf,view_epub= utils.check_keywords_exist([
        "Access provided by",
        "view pdf",
        "view epub"
    ])
    if view_pdf or view_epub:
        logger.info("[网站登陆] 免费oa文章,无需登录")
        return True
    if access_provided_by:
        logger.info("[网站登陆] tandfonline 已登录，无需再次登录")
        return True

    logger.info("[网站登陆] 执行 tandfonline 登录流程")

    # 点击login按钮
    utils.search_keyword_and_foucus('register')
    gui.hotkey("shift_tab")
    gui.press('enter',2,0.1)
    #等待页面跳转,并点击机构登陆
    time.sleep(30)
    utils.search_keyword_and_foucus("access through")
    gui.press('enter',2,0.1)   
    # 等待页面跳转
    time.sleep(30)
    utils.search_keyword_and_foucus("Type the name")
    gui.press("tab", 1, 0.5)
    gui.hotkey("shift_tab")

    gui.write("Zhejiang University", interval=0.1)
    time.sleep(3)
    gui.press("down", 1, 0.2)
    gui.press("enter", 1, 0.2)
    # 等待跳转到浙大登陆页
    time.sleep(15)
    utils.get_current_url()
    time.sleep(5)
    gui.press("enter") 
    return True
    



def _login_use_photo()->bool:
    login_button_img = utils.photo("tandfonline.com1.png")
    if not _open_institution_login(login_button_img):
        return False
    return _select_institution()

def _open_institution_login(login_button_img: str) -> bool:
    max_retries = 3
    for retry_count in range(1, max_retries + 1):
        logger.info(f"[网站登陆] 第 {retry_count}/{max_retries} 次尝试跳转机构登录页")
        if _click_login_button(login_button_img):
            logger.info("[网站登陆] 已成功跳转到机构登录页")
            return True
        gui.hotkey("refresh_page")
        time.sleep(20)

    logger.info("[网站登陆] tandfonline 跳转登录页面失败")
    return False


def _click_login_button(login_button_img: str) -> bool:
    button_pos = utils.locate_image(login_button_img)
    if button_pos:
        gui.click(button_pos)
        time.sleep(2)
        return True

    utils.search_keyword("Access through your institution")
    time.sleep(0.5)
    gui.press("esc", 1, 1)
    gui.press("enter", 2, 1)
    time.sleep(2)
    return False


def _select_institution() -> bool:
    time.sleep(50)
    utils.search_keyword("Type the name")
    gui.press("tab", 1, 0.5)
    gui.hotkey("shift_tab")

    gui.write("Zhejiang University", interval=0.1)
    time.sleep(3)
    gui.press("down", 1, 0.2)
    gui.press("enter", 1, 0.2)
    logger.info("[网站登陆] 等待跳转到浙大登陆页")

    time.sleep(15)
    gui.press("enter")
    time.sleep(20)
    gui.click(200, 200)
    gui.hotkey("close_tab")
    return True



