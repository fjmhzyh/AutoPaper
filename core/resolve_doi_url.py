from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    from core.app_config import get_config
    from core.browser_controller import BrowserController
    from core.logger import configure_logging
except ModuleNotFoundError:
    # Support direct script execution: `python3 core/resolve_doi_url.py ...`
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core.app_config import get_config
    from core.browser_controller import BrowserController
    from core.logger import configure_logging


logger = logging.getLogger(__name__)

DEFAULT_PAGE_LOAD_SEC = 60.0
CHECK_STABLE_INTERVAL_SEC = 0.3
DOI_ORG_HOSTS = {"doi.org", "dx.doi.org", "www.doi.org"}


def resolve_doi_url(doi: str) -> str | None:
    configure_logging()

    normalized_doi = _normalize_doi(doi)
    if not normalized_doi:
        logger.warning("resolve_doi_url skipped: empty DOI after normalization", extra={"doi": doi})
        return None

    target_url = f"https://doi.org/{normalized_doi}"
    controller = BrowserController()
    page_load_sec = max(
        0.0,
        get_config().get_float("download.page_load_sec", default=DEFAULT_PAGE_LOAD_SEC),
    )

    logger.info(
        "resolve_doi_url started",
        extra={"doi": normalized_doi, "target_url": target_url, "page_load_sec": page_load_sec},
    )

    try:
        controller.ensure_ready()
        controller.new_tab(target_url)
        time.sleep(page_load_sec)

        loaded, resolved_url = check_page_loaded(controller)
        if loaded and resolved_url:
            logger.info("resolve_doi_url success at first check", extra={"doi": normalized_doi, "url": resolved_url})
            return resolved_url

        logger.info("resolve_doi_url first check failed, refreshing", extra={"doi": normalized_doi})
        controller.refresh_page()
        time.sleep(page_load_sec)

        loaded, resolved_url = check_page_loaded(controller)
        if loaded and resolved_url:
            logger.info("resolve_doi_url success after refresh", extra={"doi": normalized_doi, "url": resolved_url})
            return resolved_url

        logger.warning("resolve_doi_url failed after retry", extra={"doi": normalized_doi})
        return None
    except Exception as exc:
        logger.exception("resolve_doi_url failed with exception", extra={"doi": normalized_doi, "error": str(exc)})
        return None


def check_page_loaded(browser: BrowserController) -> tuple[bool, str | None]:
    first_url = browser.copy_current_tab_url().strip()
    if not first_url:
        return False, None

    time.sleep(CHECK_STABLE_INTERVAL_SEC)

    second_url = browser.copy_current_tab_url().strip()
    if not second_url:
        return False, None
    if first_url != second_url:
        return False, None
    if _is_doi_redirect_host(second_url):
        return False, None
    return True, second_url


def _normalize_doi(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _is_doi_redirect_host(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().strip()
    if ":" in host:
        host = host.split(":", 1)[0]
    return host in DOI_ORG_HOSTS


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve DOI URL via browser automation.")
    parser.add_argument("doi", help="DOI text, e.g. 10.1000/xyz123")
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    url = resolve_doi_url(args.doi)
    if url:
        print(url)
    else:
        print("None")
