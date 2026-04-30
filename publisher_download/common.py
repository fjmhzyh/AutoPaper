from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from core.browser_controller import BrowserController
from core.downloader import move_latest_download_to_task, snapshot_download_names


def download_by_template_map(
    resolved_url: str,
    html_content: str,
    doi: str,
    *,
    task_name: str,
    item_index: int,
    project_root: str | Path | None,
    host_to_template: dict[str, str],
    logger: logging.Logger,
    site_name: str,
) -> dict[str, str | bool]:
    _ = html_content
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    template = host_to_template.get(host)
    if not template:
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": f"{site_name}域名未支持: {host or 'unknown'}",
        }

    normalized_doi = normalize_doi(doi)
    paper_download_url = template.format(doi=normalized_doi) if "{doi}" in template else template
    paper_ok, paper_file = download_paper_file(
        paper_download_url,
        normalized_doi,
        task_name=task_name,
        item_index=item_index,
        project_root=project_root,
        logger=logger,
    )
    si_ok = False
    si_file = ""
    logger.info("[资料下载] 当前站点未实现通用si下载，请在站点模块内实现")
    return {
        "paper_ok": paper_ok,
        "si_ok": si_ok,
        "paper_download_url": paper_download_url,
        "paper_file": paper_file,
        "si_file": si_file,
        "failed_reason": "" if paper_ok else "paper下载失败",
    }


def download_paper_file(
    paper_download_url: str,
    doi: str,
    *,
    task_name: str,
    item_index: int,
    project_root: str | Path | None,
    logger: logging.Logger,
) -> tuple[bool, str]:
    root = _resolve_project_root(project_root)
    before_names = snapshot_download_names()
    BrowserController().open_tab(paper_download_url)
    moved = move_latest_download_to_task(
        project_root=root,
        task_name=task_name,
        subfolder="paper",
        doi=doi,
        item_index=item_index,
        prefix="paper",
        before_names=before_names,
    )
    if not moved:
        logger.warning("[论文下载] paper下载后未找到文件")
        return False, ""
    logger.info(f"[论文下载] 论文下载成功 - {moved}")
    return True, moved


def normalize_doi(doi: str) -> str:
    text = str(doi or "").strip()
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def extract_first_si_url(html_content: str, base_url: str) -> str:
    text = str(html_content or "")
    if not text.strip():
        return ""

    hrefs = re.findall(r"""href\s*=\s*[\"']([^\"']+)[\"']""", text, flags=re.IGNORECASE)
    if not hrefs:
        return ""

    keyword_pattern = re.compile(
        r"(supplement|supplementary|supporting[-_\s]?information|\bsi\b|suppl)",
        flags=re.IGNORECASE,
    )
    file_pattern = re.compile(r"\.(pdf|zip|docx?|xlsx?)($|[?#])", flags=re.IGNORECASE)
    for href in hrefs:
        link = str(href or "").strip()
        if not link:
            continue
        absolute = urljoin(base_url, link)
        if not keyword_pattern.search(absolute):
            continue
        if not file_pattern.search(absolute) and "download" not in absolute.lower():
            continue
        return absolute
    return ""


def _resolve_project_root(project_root: str | Path | None) -> Path:
    if project_root is not None:
        return Path(project_root).resolve()
    return Path(__file__).resolve().parents[1]
