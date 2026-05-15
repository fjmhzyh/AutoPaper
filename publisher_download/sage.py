from __future__ import annotations

import logging
import time
from pathlib import Path
from urllib.parse import urlparse

from core import utils
from core.browser_controller import BrowserController
from core.downloader import move_latest_download_to_task, snapshot_download_names
from publisher_download.common import normalize_doi


logger = logging.getLogger(__name__)

PAPER_TEMPLATE = "https://journals.sagepub.com/doi/pdf/{doi}?download=true"


def download(resolved_url: str, html_content: str, doi: str, *, task_name: str = "", item_index: int = 1, project_root: str | Path | None = None) -> dict[str, str | bool]:
    _ = html_content
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()
    if host != "journals.sagepub.com":
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": "",
            "paper_file": "",
            "si_file": "",
            "failed_reason": f"sage域名未支持: {host or 'unknown'}",
        }

    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parents[1]
    normalized_doi = normalize_doi(doi)
    paper_download_url = PAPER_TEMPLATE.format(doi=normalized_doi)

    before_names = snapshot_download_names()
    BrowserController().open_tab(paper_download_url)
    time.sleep(5)

    current_url = utils.get_current_url().lower()
    if "/doi/abs/" in current_url:
        logger.warning("[论文下载] sage下载失败 - 收费文章")
        return {
            "paper_ok": False,
            "si_ok": False,
            "paper_download_url": paper_download_url,
            "paper_file": "",
            "si_file": "",
            "failed_reason": "收费文章",
        }

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
        logger.warning("[论文下载] sage下载失败 - 收费文章")

    return {
        "paper_ok": paper_ok,
        "si_ok": False,
        "paper_download_url": paper_download_url,
        "paper_file": str(paper_file or ""),
        "si_file": "",
        "failed_reason": "" if paper_ok else "收费文章",
    }
