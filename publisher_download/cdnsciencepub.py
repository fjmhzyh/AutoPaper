from __future__ import annotations

import logging
from pathlib import Path

from publisher_download.common import download_by_template_map


logger = logging.getLogger(__name__)

HOST_TO_PAPER_URLS = {
    "cdnsciencepub.com": "https://cdnsciencepub.com/doi/pdf/{doi}?download=true",
}


def download(resolved_url: str, html_content: str, doi: str, *, task_name: str = "", item_index: int = 1, project_root: str | Path | None = None) -> dict[str, str | bool]:
    return download_by_template_map(resolved_url, html_content, doi, task_name=task_name, item_index=item_index, project_root=project_root, host_to_template=HOST_TO_PAPER_URLS, logger=logger, site_name="cdnsciencepub")
