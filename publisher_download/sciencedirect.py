from __future__ import annotations

import logging
import time
from pathlib import Path
from urllib.parse import urlparse

from core import gui, utils
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
    if host != "www.sciencedirect.com":
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": f"sciencedirect域名未支持: {host or 'unknown'}",
        }

    paper_url = _open_paper_pdf_from_rendered_dom()
    if not paper_url:
        logger.warning("[论文下载] sciencedirect未找到论文下载链接")
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": "sciencedirect未找到论文下载链接",
        }

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    normalized_doi = normalize_doi(doi)

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
        "paper_download_url": paper_url,
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
    links = extract_all_links(html_content)
    si_url = ""
    for keyword in ["supplement", "appendix", "figures", "table"]:
        si_url = find_link_by_keyword(links, keyword, resolved_url)
        if si_url:
            break
    if not si_url:
        logger.info("[资料下载] sciencedirect未找到si下载链接")
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
        logger.warning("[资料下载] sciencedirect si下载失败 - 打印保存未生成文件")
        return False, ""
    logger.info(f"[资料下载] si下载成功 - {si_file}")
    return True, si_file


def _open_paper_pdf_from_rendered_dom() -> bool:
    time.sleep(5)
    utils.search_keyword_and_foucus("download full issue")
    time.sleep(0.5)
    gui.hotkey("shift_tab")
    time.sleep(0.5)
    gui.press("enter")

    # js = (
    #     "javascript:(()=>{"
    #     "const a=document.querySelector('a[href*=\"/pdfft\"]');"
    #     "if(a&&a.href){window.location.href=a.href;}"
    #     "})()"
    # )
    # gui.hotkey("focus_address_bar")
    # time.sleep(0.5)
    # gui.write(js, interval=0.01)
    # time.sleep(3)
    # gui.press("enter")
    time.sleep(10)
    current = utils.get_current_url().strip()
    if "pdf.sciencedirectassets.com" not in current.lower():
        return False
    return True
