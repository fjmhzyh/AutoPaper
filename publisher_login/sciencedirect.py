from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils


logger = logging.getLogger(__name__)

ELSEVIER_AUTH_HOST = "id.elsevier.com"
ELSEVIER_AUTH_PATH = "/as/authorization.oauth2"


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
    
    logger.info(f"access_through:{access_through} download_full_issue:{download_full_issue} purchase_pdf:{purchase_pdf}")

    # 如果存在access_through，则需要登陆下载
    if access_through and purchase_pdf:
        utils.search_keyword_and_foucus('purchase pdf')
        gui.hotkey('shift_tab')
        gui.press('enter',2,0.1)
        time.sleep(30)
        handle_elsevier_authorization_page()
        gui.press('enter',2,1)
        time.sleep(30)
        handle_elsevier_authorization_page()
        return True
    
    # 开源或者已登陆
    if download_full_issue:
        logger.info("[网站登陆] 当前文章，无需执行登陆操作")
        return True

    handle_elsevier_authorization_page()
    return True


def handle_elsevier_authorization_page(max_rounds: int = 3) -> bool:
    for _ in range(max(1, int(max_rounds))):
        current_url = utils.get_current_url()
        if not is_elsevier_authorization_url(current_url):
            return True

        logger.info("[网站登陆] 检测到 Elsevier 授权确认页，尝试自动确认")
        has_logined =utils.check_keywords_exist([
            'zhejiang university'
        ])
        if has_logined:
            _click_authorization_button()
        else:
            gui.write("zhejiang university library")
            time.sleep(5)
            gui.press('tab')
            time.sleep('2')
            gui.press('enter')

        time.sleep(15)
        gui.press('enter')
        current_url = utils.get_current_url()
        if not is_elsevier_authorization_url(current_url):
            logger.info("[网站登陆] Elsevier 授权确认完成")
            return True

        gui.press("enter")
        time.sleep(5)
    logger.warning("[网站登陆] Elsevier 授权确认失败")
    return False


def is_elsevier_authorization_url(url: str) -> bool:
    parsed = urlparse(str(url or ""))
    host = (parsed.hostname or "").lower().strip()
    path = (parsed.path or "").lower().strip()
    return host == ELSEVIER_AUTH_HOST and path == ELSEVIER_AUTH_PATH


def _click_authorization_button() -> None:
    js = (
        "javascript:(()=>{"
        "let b=document.querySelector('[name=action][value=signInWithInst]');"
        "if(!b)b=[...document.querySelectorAll('button,input,a')].find(e=>"
        "/continue|confirm|authorize|allow|accept|proceed|yes/i.test(e.innerText||e.value||e.ariaLabel||''));"
        "b&&b.click();"
        "})()"
    )
    gui.hotkey("focus_address_bar")
    time.sleep(0.5)
    gui.write(js, interval=0.01)
    gui.press("enter")
    
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
