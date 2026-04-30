from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from core.browser_controller import BrowserController
from core.downloader import print_download
from publisher_download.common import extract_first_si_url, normalize_doi


logger = logging.getLogger(__name__)

HOST_TO_PAPER_URLS = {
    "pubs.acs.org": "https://pubs.acs.org/doi/pdf/{doi}?ref=article_openPDF",
}


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
    template = HOST_TO_PAPER_URLS.get(host)
    if not template:
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": f"acs域名未支持: {host or 'unknown'}",
        }

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    normalized_doi = normalize_doi(doi)
    paper_download_url = template.format(doi=normalized_doi)

    BrowserController().open_tab(paper_download_url)
    paper_file = print_download(
        project_root=root,
        task_name=task_name,
        subfolder="paper",
        doi=normalized_doi,
        item_index=item_index,
        prefix="paper",
    )
    paper_ok = bool(paper_file)
    if paper_ok:
        logger.info(f"[论文下载] 论文下载成功 - {paper_file}")
    else:
        logger.warning("[论文下载] 论文下载失败 - 打印保存未生成文件")

    si_ok, si_file = download_si(
        resolved_url,
        html_content,
        normalized_doi,
        task_name=task_name,
        item_index=item_index,
        project_root=root,
    )
    return {
        "paper_ok": paper_ok,
        "si_ok": si_ok,
        "paper_download_url": paper_download_url,
        "paper_file": str(paper_file or ""),
        "si_file": si_file,
        "failed_reason": "" if paper_ok else "paper打印保存失败",
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
        logger.info("[资料下载] acs未找到si下载链接")
        return False, ""

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    BrowserController().open_tab(si_url)
    si_file = print_download(
        project_root=root,
        task_name=task_name,
        subfolder="si",
        doi=doi,
        item_index=item_index,
        prefix="si",
    )
    if not si_file:
        logger.warning("[资料下载] acs si下载失败 - 打印保存未生成文件")
        return False, ""
    logger.info(f"[资料下载] si下载成功 - {si_file}")
    return True, si_file
