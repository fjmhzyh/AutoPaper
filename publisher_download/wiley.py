from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from core.browser_controller import BrowserController
from core.downloader import move_latest_download_to_task, snapshot_download_names
from publisher_download.common import (
    download_paper_file,
    extract_first_si_url,
    normalize_doi,
)


logger = logging.getLogger(__name__)


def download(
    resolved_url: str,
    html_content: str,
    doi: str,
    *,
    task_name: str = "",
    item_index: int = 1,
    project_root: str | Path | None = None,
) -> dict[str, str | bool]:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if not _is_supported_host(host):
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": f"wiley域名未支持: {host or 'unknown'}",
        }

    normalized_doi = normalize_doi(doi)
    paper_download_url = f"https://{host}/doi/pdfdirect/{normalized_doi}?download=true"

    paper_ok, paper_file = download_paper_file(
        paper_download_url,
        normalized_doi,
        task_name=task_name,
        item_index=item_index,
        project_root=project_root,
        logger=logger,
    )
    si_ok, si_file = download_si(
        resolved_url,
        html_content,
        normalized_doi,
        task_name=task_name,
        item_index=item_index,
        project_root=project_root,
    )

    return {
        "paper_ok": paper_ok,
        "si_ok": si_ok,
        "paper_download_url": paper_download_url,
        "paper_file": paper_file,
        "si_file": si_file,
        "failed_reason": "" if paper_ok else "paper下载失败",
    }


def download_si(
    resolved_url: str,
    html_content: str,
    doi: str,
    *,
    task_name: str,
    item_index: int,
    project_root: str | Path | None,
) -> tuple[bool, str]:
    si_url = extract_first_si_url(html_content, resolved_url)
    if not si_url:
        logger.info("[资料下载] wiley未找到si下载链接")
        return False, ""

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    before_names = snapshot_download_names()
    BrowserController().open_tab(si_url)
    moved = move_latest_download_to_task(
        project_root=root,
        task_name=task_name,
        subfolder="si",
        doi=doi,
        item_index=item_index,
        prefix="si",
        before_names=before_names,
    )
    if not moved:
        logger.warning("[资料下载] wiley si下载失败")
        return False, ""
    logger.info(f"[资料下载] si下载成功 - {moved}")
    return True, moved


def _is_supported_host(host: str) -> bool:
    return host == "onlinelibrary.wiley.com" or host.endswith(".onlinelibrary.wiley.com")
