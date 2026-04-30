from __future__ import annotations

import logging
from pathlib import Path

from publisher_download.common import download_by_template_map


logger = logging.getLogger(__name__)

HOST_TO_PAPER_URLS = {
    "stemcellres.biomedcentral.com": "https://stemcellres.biomedcentral.com/counter/pdf/{doi}.pdf",
    "arthritis-research.biomedcentral.com": "https://arthritis-research.biomedcentral.com/counter/pdf/{doi}.pdf",
    "bmcmusculoskeletdisord.biomedcentral.com": "https://bmcmusculoskeletdisord.biomedcentral.com/counter/pdf/{doi}.pdf",
    "trialsjournal.biomedcentral.com": "https://trialsjournal.biomedcentral.com/counter/pdf/{doi}.pdf",
}


def download(resolved_url: str, html_content: str, doi: str, *, task_name: str = "", item_index: int = 1, project_root: str | Path | None = None) -> dict[str, str | bool]:
    return download_by_template_map(resolved_url, html_content, doi, task_name=task_name, item_index=item_index, project_root=project_root, host_to_template=HOST_TO_PAPER_URLS, logger=logger, site_name="biomedcentral")
