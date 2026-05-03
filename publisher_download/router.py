from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from publisher_download import (
    acs,
    biomedcentral,
    cdnsciencepub,
    hindawi,
    ieee,
    iopscience,
    jospt,
    literatum,
    pnas,
    rsc,
    sage,
    science,
    sciencedirect,
    springer,
    tandfonline,
    thieme,
    wiley,
)


logger = logging.getLogger(__name__)

DOWNLOADERS = {
    "pubs.acs.org": acs.download,
    "www.tandfonline.com": tandfonline.download,
    "link.springer.com": springer.download,
    "iopscience.iop.org": iopscience.download,
    "ieeexplore.ieee.org": ieee.download,
    "stemcellres.biomedcentral.com": biomedcentral.download,
    "arthritis-research.biomedcentral.com": biomedcentral.download,
    "bmcmusculoskeletdisord.biomedcentral.com": biomedcentral.download,
    "trialsjournal.biomedcentral.com": biomedcentral.download,
    "pubs.rsc.org": rsc.download,
    "journals.sagepub.com": sage.download,
    "www.hindawi.com": hindawi.download,
    "www.science.org": science.download,
    "www.sciencedirect.com": sciencedirect.download,
    "www.jospt.org": jospt.download,
    "www.thieme-connect.de": thieme.download,
    "cdnsciencepub.com": cdnsciencepub.download,
    "www.pnas.org": pnas.download,
    "dom-pubs.pericles-prod.literatumonline.com": literatum.download,
}


def download_by_url(
    resolved_url: str,
    html_content: str,
    doi: str,
    *,
    task_name: str = "",
    item_index: int = 1,
    project_root: str | Path | None = None,
) -> dict[str, str | bool]:
    host = (urlparse(str(resolved_url or "")).hostname or "").lower().strip()

    if host == "onlinelibrary.wiley.com" or host.endswith(".onlinelibrary.wiley.com"):
        return wiley.download(
            resolved_url,
            html_content,
            doi,
            task_name=task_name,
            item_index=item_index,
            project_root=project_root,
        )

    downloader = DOWNLOADERS.get(host)
    if downloader:
        return downloader(
            resolved_url,
            html_content,
            doi,
            task_name=task_name,
            item_index=item_index,
            project_root=project_root,
        )

    logger.info(f"[论文下载] 未匹配下载器，跳过，域名: {host or 'unknown'}")
    return {
        "paper_ok": True,
        "si_ok": True,
        "paper_download_url": "",
        "paper_file": "",
        "si_file": "",
        "failed_reason": "",
    }
