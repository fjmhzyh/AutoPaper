from __future__ import annotations

import logging
import time
from pathlib import Path
from urllib.parse import urlparse

from core.browser_controller import BrowserController
from core.downloader import print_download
from publisher_download.common import extract_all_links, find_link_by_keyword, normalize_doi


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
    if host != "www.cell.com":
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": f"cell域名未支持: {host or 'unknown'}",
        }

    links = extract_all_links(html_content)
    paper_url = find_link_by_keyword(links, "/action/showpdf", resolved_url)
    if not paper_url:
        logger.warning("[论文下载] cell未找到论文下载链接")
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": "cell未找到论文下载链接",
        }

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    normalized_doi = normalize_doi(doi)

    BrowserController().open_tab(paper_url)
    time.sleep(30)
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

    logger.info("[资料下载] cell未实现si下载")
    return {
        "paper_ok": paper_ok,
        "si_ok": False,
        "paper_download_url": paper_url,
        "paper_file": str(paper_file or ""),
        "si_file": "",
        "failed_reason": "" if paper_ok else "paper打印保存失败",
    }
