from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from core import gui
from core import utils
from core.app_config import get_config



logger = logging.getLogger(__name__)


def login(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not host.endswith("acs.org"):
        return True
    

    config = get_config()
    page_load_sec = config.get_float("download.page_load_sec", default=12.0)

    logger.info("[网站登陆] 执行 ACS 登录流程")
    access_through, zhejiang_university, open_pdf,access_through_institution= utils.check_keywords_exist(
        ["access through", "zhejiang university", "open pdf", 'access through your institution']
    )
    logger.info(f"关键字结果:accses_throug:{access_through},zhejiang:{zhejiang_university}")
    # 半登陆状态
    if access_through and zhejiang_university:
        utils.search_keyword_and_foucus('zhejiang university')
        gui.press('enter',2,0.2)
        time.sleep(20)
        gui.press("enter")
        time.sleep(10)
        return True

    # 未登陆状态
    if access_through_institution and not zhejiang_university:
        utils.search_keyword_and_foucus('access through your institution')
        gui.press('enter',2,0.2)
        time.sleep(30)
        utils.search_keyword("Search By University")
        gui.press("tab")
        gui.hotkey("shift_tab")
        gui.write("Zhejiang University", interval=0.1)
        time.sleep(3)
        gui.press("down", 1, 0.2)
        gui.press("enter", 1, 0.2)
        logger.info("[网站登陆] 等待跳转到浙大登陆页")
        time.sleep(15)
        gui.press("enter")
        time.sleep(20)
        return True

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
        gui.press("esc", 1, 1)
        gui.press("enter", 2, 1)
        return True

    gui.click(button_pos)
    return True

