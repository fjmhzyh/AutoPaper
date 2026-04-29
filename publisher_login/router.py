from __future__ import annotations

import logging
from urllib.parse import urlparse

from publisher_login import acs, rsc, sciencedirect, springer, tandfonline, wiley


logger = logging.getLogger(__name__)


def login_by_url(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if host.endswith("wiley.com"):
        return bool(wiley.login(resolved_url))
    if host.endswith("springer.com"):
        return bool(springer.login(resolved_url))
    if host.endswith("sciencedirect.com"):
        return bool(sciencedirect.login(resolved_url))
    if host.endswith("acs.org"):
        return bool(acs.login(resolved_url))
    if host.endswith("rsc.org"):
        return bool(rsc.login(resolved_url))
    if host.endswith("tandfonline.com"):
        return bool(tandfonline.login(resolved_url))

    logger.info(f"[网站登陆] 未匹配登录器，跳过，域名: {host or 'unknown'}")
    return True
