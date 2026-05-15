from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from core.browser_controller import BrowserController
from core.downloader import move_latest_download_to_task, print_download, snapshot_download_names
from publisher_download.common import normalize_doi


logger = logging.getLogger(__name__)

AUTO_DOWNLOAD_HOSTS = {
    "mdpi.com",
    "journals.plos.org",
    "frontiersin.org",
}

PRINT_DOWNLOAD_HOSTS = {
    "thno.org",
    "beilstein-journals.org",
    "dovepress.com",
}

SUPPORTED_HOSTS = AUTO_DOWNLOAD_HOSTS | PRINT_DOWNLOAD_HOSTS | {"biorxiv.org"}


def supports(resolved_url: str) -> bool:
    return _is_supported_host(_normalize_host(resolved_url))


def download(
    resolved_url: str,
    html_content: str,
    doi: str,
    *,
    task_name: str = "",
    item_index: int = 1,
    project_root: str | Path | None = None,
) -> dict[str, str | bool]:
    host = _normalize_host(resolved_url)
    if not _is_supported_host(host):
        return _failed("", f"通用下载器未支持域名: {host or 'unknown'}")

    paper_url = _extract_paper_url(resolved_url, html_content)
    if not paper_url:
        logger.info(f"[论文下载] 通用下载器未找到PDF地址，域名: {host or 'unknown'}")
        return _failed("", "通用下载器未找到PDF地址")

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    normalized_doi = normalize_doi(doi)
    logger.info(f"[论文下载] 通用下载器找到PDF地址 - {paper_url}")

    if _is_print_host(host):
        BrowserController().open_tab(paper_url)
        paper_file = print_download(
            project_root=root,
            task_name=task_name,
            subfolder="paper",
            doi=normalized_doi,
            item_index=item_index,
            prefix="paper",
        )
    else:
        paper_url = _with_download_flag(paper_url) if _host_matches(host, "biorxiv.org") else paper_url
        before_names = snapshot_download_names()
        BrowserController().open_tab(paper_url)
        paper_file = move_latest_download_to_task(
            project_root=root,
            task_name=task_name,
            subfolder="paper",
            doi=normalized_doi,
            item_index=item_index,
            prefix="paper",
            before_names=before_names,
        )

    paper_ok = bool(paper_file)
    if paper_ok:
        logger.info(f"[论文下载] 论文下载成功 - {paper_file}")
    else:
        logger.warning("[论文下载] 通用下载失败 - 未生成文件")

    return {
        "paper_ok": paper_ok,
        "si_ok": False,
        "paper_download_url": paper_url,
        "paper_file": str(paper_file or ""),
        "si_file": "",
        "failed_reason": "" if paper_ok else "通用下载失败",
    }


def _extract_paper_url(article_url: str, html_content: str) -> str:
    meta_url = _extract_meta_content(html_content, "citation_pdf_url")
    if meta_url:
        return urljoin(article_url, meta_url)

    for name in ("dc.identifier", "DC.Identifier", "eprints.document_url"):
        value = _extract_meta_content(html_content, name)
        if ".pdf" in value.lower():
            return urljoin(article_url, value)

    link = _extract_pdf_link(article_url, html_content)
    if link:
        return link

    return _site_fallback_url(article_url)


def _extract_meta_content(html_content: str, name: str) -> str:
    text = str(html_content or "")
    if not text:
        return ""

    pattern = re.compile(r"<meta\b[^>]*>", flags=re.IGNORECASE)
    for match in pattern.finditer(text):
        tag = match.group(0)
        tag_name = _extract_attr(tag, "name") or _extract_attr(tag, "property")
        if tag_name.lower() != name.lower():
            continue
        return _extract_attr(tag, "content")
    return ""


def _extract_attr(tag: str, attr: str) -> str:
    match = re.search(
        rf"""\b{re.escape(attr)}\s*=\s*(['"])(.*?)\1""",
        tag,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return str(match.group(2) or "").strip() if match else ""


def _extract_pdf_link(article_url: str, html_content: str) -> str:
    text = str(html_content or "")
    for match in re.finditer(r"""<a\b[^>]*href\s*=\s*(['"])(.*?)\1[^>]*>(.*?)</a>""", text, flags=re.IGNORECASE | re.DOTALL):
        href = str(match.group(2) or "").strip()
        label = re.sub(r"<[^>]+>", " ", str(match.group(3) or "")).lower()
        lower_href = href.lower()
        if ".pdf" in lower_href or "download pdf" in label or label.strip() == "pdf":
            return urljoin(article_url, href)
    return ""


def _site_fallback_url(article_url: str) -> str:
    host = _normalize_host(article_url)
    if _host_matches(host, "mdpi.com"):
        return article_url.rstrip("/") + "/pdf"
    if _host_matches(host, "journals.plos.org"):
        parsed = urlparse(article_url)
        query = parse_qs(parsed.query)
        article_id = query.get("id", [""])[0]
        if article_id:
            path = parsed.path.rstrip("/") + "/file"
            return urlunparse(parsed._replace(path=path, query=f"id={article_id}&type=printable"))
    if _host_matches(host, "frontiersin.org"):
        return article_url.rstrip("/").removesuffix("/full") + "/pdf"
    if _host_matches(host, "thno.org"):
        return re.sub(r"\.html?$", ".pdf", article_url, flags=re.IGNORECASE)
    return ""


def _with_download_flag(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["download"] = ["true"]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def _normalize_host(url: str) -> str:
    host = (urlparse(str(url or "")).hostname or "").lower().strip()
    return host[4:] if host.startswith("www.") else host


def _is_supported_host(host: str) -> bool:
    return any(_host_matches(host, item) for item in SUPPORTED_HOSTS)


def _is_print_host(host: str) -> bool:
    return any(_host_matches(host, item) for item in PRINT_DOWNLOAD_HOSTS)


def _host_matches(host: str, suffix: str) -> bool:
    return host == suffix or host.endswith(f".{suffix}")


def _failed(paper_url: str, reason: str) -> dict[str, str | bool]:
    return {
        "paper_ok": False,
        "si_ok": False,
        "paper_download_url": paper_url,
        "paper_file": "",
        "si_file": "",
        "failed_reason": reason,
    }
