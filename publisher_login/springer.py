from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("springer.com"):
        return True

    log_in_via, = utils.check_keywords_exist(["log in via"])
    if not log_in_via:
        logger.info("[网站登陆] Springer 无需执行登陆流程")
        return True
    
    logger.info("[网站登陆] 执行 Springer 登录流程")
    
    # 查找登陆按钮
    utils.search_keyword_and_foucus('Log in via an institution')
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
    return True



def _login_use_photo()->bool:
    login_button_img = utils.photo("link.springer.com1.png")
    institution_input_img = utils.photo("link.springer.com3.png")

    if not _open_institution_login(login_button_img):
        return False
    return _select_institution(institution_input_img)


def _open_institution_login(login_button_img: str) -> bool:
    button_pos = utils.locate_image(login_button_img)
    if not button_pos:
        logger.info("[网站登陆] 未找到 Springer 登录按钮1")
        return False

    gui.click(button_pos)
    time.sleep(5)
    return True


def _select_institution(institution_input_img: str) -> bool:
    input_pos = utils.locate_image(institution_input_img)
    if not input_pos:
        logger.info("[网站登陆] 未找到 Springer 机构输入框")
        return False

    gui.click(input_pos)
    time.sleep(40)
    gui.write("Zhejiang University", interval=0.1)
    time.sleep(15)
    gui.press("down", 9, 0.1)
    gui.press("enter", 1, 0.2)
    time.sleep(20)
    gui.press("enter")
    return True


