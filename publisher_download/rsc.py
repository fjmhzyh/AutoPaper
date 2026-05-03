from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

from core.browser_controller import BrowserController
from core.downloader import print_download
from publisher_download.common import extract_all_links, normalize_doi,find_link_by_keyword


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
    if host != "pubs.rsc.org":
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": f"rsc域名未支持: {host or 'unknown'}",
        }

    links = extract_all_links(html_content)
    paper_url = find_link_by_keyword(links, "/en/content/articlepdf/", resolved_url)
    if not paper_url:
        logger.warning("[论文下载] rsc未找到论文下载链接")
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": "rsc未找到论文下载链接",
        }

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    normalized_doi = normalize_doi(doi)
    BrowserController().open_tab(paper_url)
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

    si_url = find_link_by_keyword(links, "suppdata", resolved_url)
    if not si_url:
        logger.info("[资料下载] rsc未找到si下载链接")
        si_ok = False
        si_file = ""
    else:
        BrowserController().open_tab(si_url)
        si_file = print_download(
            project_root=root,
            task_name=task_name,
            subfolder="si",
            doi=normalized_doi,
            item_index=item_index,
            prefix="si",
        )
        si_ok = bool(si_file)
        if si_ok:
            logger.info(f"[资料下载] si下载成功 - {si_file}")
        else:
            logger.warning("[资料下载] si下载失败 - 打印保存未生成文件")

    return {
        "paper_ok": paper_ok,
        "si_ok": si_ok,
        "paper_download_url": paper_url,
        "paper_file": str(paper_file or ""),
        "si_file": str(si_file or ""),
        "failed_reason": "" if paper_ok else "paper打印保存失败",
    }



