from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("wiley.com"):
        return True

    logger.info("[网站登陆] 执行 wiley 登录流程")

    open_access, full_access, zhejiang_university = utils.check_keywords_exist(["open access", "full access","zhejiang university"])
    if zhejiang_university:
        logger.info("[网站登陆] wiley已登陆，无需再次登陆")
        return True
    if open_access or full_access:
        logger.info("[网站登陆] wiley 检测到 open access，无需登陆")
        return True
    
    return _login_use_hotkey()

    login_button_img = utils.photo("advanced.onlinelibrary.wiley.com1.png")
    submit_button_img = utils.photo("advanced.onlinelibrary.wiley.com2.png")
    return _run_wiley_two_step_flow(login_button_img, submit_button_img)

def _login_use_hotkey()->bool:
    utils.search_keyword_and_foucus('Login / Register')
    # 点击登陆按钮
    gui.press('enter')
    # 选中机构登陆
    gui.press('tab',2,0.2)
    # 点击机构登陆
    gui.press('enter')
    # 等待页面加载
    time.sleep(20)
    # 检查是否有机构登陆字样
    text = 'enter institution name'
    enter_institution_name = utils.check_keywords_exist([text])
    if enter_institution_name:
        # 找到机构输入框，并输入
        utils.search_keyword_and_foucus(text)
        gui.press('tab')
        gui.hotkey('shift_tab')
        gui.write('zhejiang university')
        time.sleep(5)
        gui.press('enter')
        # 等待跳转到浙江登陆页，并登陆
        time.sleep(20)
        utils.get_current_url()
        gui.press('enter')
        return True
    return False

def _run_wiley_two_step_flow(login_button_img: str, submit_button_img: str) -> bool:
    clicked_first = False
    logger.info("[网站登陆] 正在查找 wiley 登录按钮1")
    utils.search_keyword("pdf")
    button_pos = utils.locate_image(login_button_img)
    if button_pos:
        gui.click(button_pos)
        logger.info("[网站登陆] 已点击 wiley 登录按钮1")
        time.sleep(20)
        clicked_first = True

    gui.press("down", 5, 0.2)

    clicked_second = False
    logger.info("[网站登陆] 正在查找 wiley 登录按钮2")
    button_pos = utils.locate_image(submit_button_img)
    if button_pos:
        gui.click(button_pos)
        logger.info("[网站登陆] 已点击 wiley 登录按钮2")
        time.sleep(10)
        gui.press("enter")
        time.sleep(10)
        clicked_second = True

    return clicked_first or clicked_second






