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
    if not host.endswith("cell.com"):
        return True

    logger.info("[网站登陆] 执行 cell 登录流程")
    time.sleep(2)
    zhejiang_university, download_pdf = utils.check_keywords_exist(
        [
            "zhejiang university",
            "download pdf",
        ]
    )
    logger.info(f"zhejiang_university:{zhejiang_university}, download_pdf:{download_pdf}")
    if zhejiang_university:
        logger.info("[网站登陆] cell已登陆，无需再次登陆")
        return True
    if download_pdf:
        logger.info("[网站登陆] cell当前文章无需登陆")
        return True

    return _login_use_hotkey()


def _login_use_hotkey() -> bool:

    utils.search_keyword_and_foucus('log in')
    gui.press("enter")
    time.sleep(30)
    handle_elsevier_page()


def handle_elsevier_page ():
    current_url = utils.get_current_url()
    if not is_elsevier_authorization_url(current_url):
        return True
    organization, = utils.check_keywords_exist(['sign in via your organization'])
    if organization:
        utils.search_keyword_and_foucus('sign in via your organization')
        gui.press('enter')
        time.sleep(3)
        gui.write('zhejiang university library')
        time.sleep(3)
        gui.press('tab')
        time.sleep(1)
        gui.press('enter')
        # 等待页面跳转
        time.sleep(15)
        enter_email, = utils.check_keywords_exist(['enter your email to sign in'])
        logger.info(f"enter_email:{enter_email}")
        if is_elsevier_authorization_url(utils.get_current_url()) and enter_email:
            utils.search_keyword_and_foucus('sign in or register')
            gui.press('tab')
            gui.press('enter')
            time.sleep(20)
            if is_elsevier_authorization_url(utils.get_current_url()):
                return False
            return True
        else:
            return True



def is_elsevier_authorization_url(url: str) -> bool:
    parsed = urlparse(str(url or ""))
    host = (parsed.hostname or "").lower().strip()
    path = (parsed.path or "").lower().strip()
    return host == ELSEVIER_AUTH_HOST and path == ELSEVIER_AUTH_PATH