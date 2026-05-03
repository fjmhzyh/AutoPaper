from __future__ import annotations

import csv
import logging
from datetime import datetime
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


def _resolve_unsupported_sites_path(project_root: str | Path | None) -> Path:
    if project_root is not None:
        root = Path(project_root).resolve()
    else:
        root = Path(__file__).resolve().parents[1]
    return root / "unsupported_sites.csv"


def _record_unsupported_site(
    *,
    project_root: str | Path | None,
    task_name: str,
    doi: str,
    host: str,
    resolved_url: str,
) -> None:
    csv_path = _resolve_unsupported_sites_path(project_root)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    host_text = str(host or "").strip() or "unknown"
    row = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "taskName": Path(str(task_name or "").strip()).stem,
        "doi": str(doi or "").strip(),
        "host": host_text,
        "url": str(resolved_url or "").strip(),
    }
    fieldnames = ["time", "taskName", "doi", "host", "url"]
    rows: list[dict[str, str]] = []
    if csv_path.exists():
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file_obj:
                reader = csv.DictReader(file_obj)
                for raw in reader:
                    rows.append(
                        {
                            "time": str(raw.get("time", "") or "").strip(),
                            "taskName": str(raw.get("taskName", "") or "").strip(),
                            "doi": str(raw.get("doi", "") or "").strip(),
                            "host": str(raw.get("host", "") or "").strip(),
                            "url": str(raw.get("url", "") or "").strip(),
                        }
                    )
        except Exception:
            rows = []

    replaced = False
    for idx, old in enumerate(rows):
        if str(old.get("host", "") or "").strip().lower() == host_text.lower():
            rows[idx] = row
            replaced = True
            break
    if not replaced:
        rows.append(row)

    rows.sort(key=lambda item: str(item.get("host", "") or "").lower())
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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

    logger.info(f"[论文下载] 未匹配下载器，标记失败，域名: {host or 'unknown'}")
    try:
        _record_unsupported_site(
            project_root=project_root,
            task_name=task_name,
            doi=doi,
            host=host,
            resolved_url=resolved_url,
        )
    except Exception as exc:
        logger.warning(f"[论文下载] 记录 unsupported site 失败: {exc}")
    return {
        "paper_ok": False,
        "si_ok": False,
        "paper_download_url": "",
        "paper_file": "",
        "si_file": "",
        "failed_reason": "unsupported site",
    }
