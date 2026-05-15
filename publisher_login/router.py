from __future__ import annotations

import logging
from urllib.parse import urlparse

from publisher_login import acs, cell, nature, rsc, sciencedirect, springer, tandfonline, wiley


logger = logging.getLogger(__name__)

LOGIN_SITES = [
    {
        "id": "wiley",
        "label": "wiley",
        "match_suffixes": ("wiley.com",),
        "open_url": "https://onlinelibrary.wiley.com",
        "module": wiley,
    },
    {
        "id": "springer",
        "label": "springer",
        "match_suffixes": ("springer.com",),
        "open_url": "https://link.springer.com",
        "module": springer,
    },
    {
        "id": "nature",
        "label": "nature",
        "match_suffixes": ("nature.com",),
        "open_url": "https://www.nature.com",
        "module": nature,
    },
    {
        "id": "sciencedirect",
        "label": "sciencedirect",
        "match_suffixes": ("sciencedirect.com",),
        "open_url": "https://www.sciencedirect.com",
        "module": sciencedirect,
    },
    {
        "id": "cell",
        "label": "cell",
        "match_suffixes": ("cell.com",),
        "open_url": "https://www.cell.com",
        "module": cell,
    },
    {
        "id": "acs",
        "label": "pub.acs.org",
        "match_suffixes": ("acs.org",),
        "open_url": "https://pubs.acs.org",
        "module": acs,
    },
    {
        "id": "rsc",
        "label": "pub.rsc.org",
        "match_suffixes": ("rsc.org",),
        "open_url": "https://pubs.rsc.org",
        "module": rsc,
    },
    {
        "id": "tandfonline",
        "label": "tandfonline",
        "match_suffixes": ("tandfonline.com",),
        "open_url": "https://www.tandfonline.com",
        "module": tandfonline,
    },
]


def get_supported_login_sites() -> list[dict[str, str]]:
    return [
        {
            "id": str(item.get("id", "")).strip(),
            "label": str(item.get("label", "")).strip(),
            "open_url": str(item.get("open_url", "")).strip(),
        }
        for item in LOGIN_SITES
    ]


def login_by_url(resolved_url: str) -> bool:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    for site in LOGIN_SITES:
        suffixes = tuple(site.get("match_suffixes", ()) or ())
        if host and any(host.endswith(str(suffix).lower()) for suffix in suffixes):
            module = site.get("module")
            if module is None or not hasattr(module, "login"):
                return True
            return bool(module.login(resolved_url))

    logger.info(f"[网站登陆] 未匹配登录器，跳过，域名: {host or 'unknown'}")
    return True
