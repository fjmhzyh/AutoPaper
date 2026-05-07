from __future__ import annotations

import argparse
import importlib
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from core import gui
    from core.browser_controller import BrowserController
    from core.csv_manager import CSVManager
    from core.logger import configure_logging
    from core.task_manager import DOI_PATTERN, STATISTIC_FIELDNAMES, TASK_FIELDNAMES
except ModuleNotFoundError:
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from core import gui
    from core.browser_controller import BrowserController
    from core.csv_manager import CSVManager
    from core.logger import configure_logging
    from core.task_manager import DOI_PATTERN, STATISTIC_FIELDNAMES, TASK_FIELDNAMES




logger = logging.getLogger(__name__)


def open_pubmed_and_get_rss_text(keyword: str) -> str:
    keyword_text = str(keyword or "").strip()
    if not keyword_text:
        raise ValueError("keyword不能为空")

    BrowserController().open_tab("https://pubmed.ncbi.nlm.nih.gov/")
    time.sleep(10)
    gui.write(keyword_text)
    gui.press("enter")
    time.sleep(10)
    gui.press("tab", presses=5, interval=0.3)
    gui.press("enter")
    gui.press("tab", presses=2, interval=0.3)
    gui.press("enter")
    time.sleep(2)
    gui.press("tab")
    gui.press("enter")
    time.sleep(2)
    rss_link = _clipboard_paste().strip()
    if not rss_link:
        raise ValueError("未获取到RSS订阅链接")

    logger.info(f"[任务获取] RSS链接获取成功: {rss_link}")
    rss_text = _fetch_rss_text_by_curl_cffi(rss_link)
    gui.hotkey("close_tab")
    if not rss_text:
        raise ValueError("RSS内容为空")
    return rss_text


def _fetch_rss_text_by_curl_cffi(url: str) -> str:
    try:
        curl_cffi = importlib.import_module("curl_cffi")
    except ModuleNotFoundError as exc:
        raise RuntimeError("未安装 curl-cffi，请先安装后再执行RSS抓取") from exc

    requests_module = getattr(curl_cffi, "requests", None)
    if requests_module is None:
        raise RuntimeError("curl_cffi.requests 不可用，请检查 curl-cffi 安装")

    response = requests_module.get(url, timeout=30)
    if int(getattr(response, "status_code", 500)) >= 400:
        raise ValueError(f"RSS内容获取失败: HTTP {response.status_code}")
    return str(getattr(response, "text", "") or "").strip()


def _clipboard_copy(text: str) -> None:
    module = _import_pyperclip()
    module.copy(text)


def _clipboard_paste() -> str:
    module = _import_pyperclip()
    return str(module.paste() or "")


def _import_pyperclip():
    try:
        return importlib.import_module("pyperclip")
    except ModuleNotFoundError as exc:
        raise RuntimeError("未安装 pyperclip，请先安装后再执行RSS抓取") from exc


def create_rss_task(keyword: str) -> dict[str, Any]:
    configure_logging()
    keyword_text = str(keyword or "").strip()
    if not keyword_text:
        raise ValueError("keyword不能为空")

    rss_text = open_pubmed_and_get_rss_text(keyword_text)
    content = str(rss_text or "").strip()
    if not content:
        raise ValueError("rss_text不能为空")

    project_root = Path(__file__).resolve().parents[1]
    tasks_dir = project_root / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    extracted = extract_strict_dois(content)
    total_extracted = len(extracted)
    if total_extracted == 0:
        raise ValueError("未提取到DOI")

    valid_dois: list[str] = []
    seen: set[str] = set()
    duplicate_count = 0
    invalid_count = 0
    for doi in extracted:
        if not _is_valid_doi(doi):
            invalid_count += 1
            continue
        key = doi.lower()
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        valid_dois.append(doi)

    if not valid_dois:
        raise ValueError("未提取到有效DOI")

    task_name = _generate_rss_task_name(tasks_dir, keyword_text)
    task_file = tasks_dir / f"{task_name}.csv"

    logger.info(f"[任务获取] 关键词-{keyword_text} 原始DOI-{total_extracted}条")
    _write_task_file(task_file, valid_dois)
    _upsert_statistic_row(project_root, task_name=task_name, total_count=len(valid_dois))
    logger.info(
        f"[执行结果] 任务-{task_name} 写入完成: 有效-{len(valid_dois)}条, 重复-{duplicate_count}条, 无效-{invalid_count}条"
    )

    return {
        "task_name": task_name,
        "task_file": str(task_file),
        "total_extracted": total_extracted,
        "valid_count": len(valid_dois),
        "duplicate_count": duplicate_count,
        "invalid_count": invalid_count,
    }


def extract_strict_dois(text: str) -> list[str]:
    strict_doi_pattern = r"\bdoi:\s*(10\.[0-9]{4,}(?:\.[0-9]+)*/[^\s<;,)]+)"
    matches = re.findall(strict_doi_pattern, str(text or ""), re.IGNORECASE)

    clean_dois: list[str] = []
    for doi in matches:
        clean_doi = re.sub(r"<[^>]+>", "", doi)
        clean_doi = re.sub(r"[^0-9a-zA-Z./-]+$", "", clean_doi)
        clean_doi = clean_doi.rstrip(".")
        clean_doi = clean_doi.strip().lower()
        if clean_doi:
            clean_dois.append(clean_doi)
    return clean_dois


def _is_valid_doi(doi: str) -> bool:
    text = str(doi or "").strip()
    if not text or " " in text:
        return False
    return DOI_PATTERN.match(text) is not None


def _generate_rss_task_name(tasks_dir: Path, keyword: str) -> str:
    safe_keyword = _normalize_keyword(keyword)
    base = f"rss-{safe_keyword}-{datetime.now().strftime('%m%d')}"
    candidate = base
    index = 2
    while (tasks_dir / f"{candidate}.csv").exists():
        candidate = f"{base}-{index:02d}"
        index += 1
    return candidate


def _normalize_keyword(keyword: str) -> str:
    text = str(keyword or "").strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^0-9a-z_-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-_")
    return text or "keyword"


def _write_task_file(task_file: Path, dois: list[str]) -> None:
    manager = CSVManager(task_file, fieldnames=TASK_FIELDNAMES)
    manager.load()
    for doi in dois:
        manager.add_row(
            {
                "DOI": doi,
                "DownloaStatus": "",
                "SIDownloadStatus": "",
                "failedReason": "",
                "PublisherUrl": "",
                "PaperFile": "",
                "SIFile": "",
                "HtmlFile": "",
                "PaperDownloadUrl": "",
            }
        )


def _resolve_statistic_path(project_root: Path) -> Path:
    preferred = [project_root / "statistic.csv", project_root / "statistic.csv "]
    for item in preferred:
        if item.exists():
            return item
    existing = sorted(project_root.glob("statistic.csv*"))
    if existing:
        return existing[0]
    return preferred[0]


def _upsert_statistic_row(project_root: Path, *, task_name: str, total_count: int) -> None:
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M")
    statistic_path = _resolve_statistic_path(project_root)
    manager = CSVManager(statistic_path, fieldnames=STATISTIC_FIELDNAMES)
    manager.upsert_by(
        "taskName",
        task_name,
        {
            "taskName": task_name,
            "status": "pending",
            "totalCount": str(total_count),
            "paperSuccessCount": "0",
            "paperFailedCount": "0",
            "siSuccessCount": "0",
            "createTime": now_text,
            "updateTime": now_text,
        },
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create RSS task by keyword.")
    parser.add_argument("keyword", nargs="?", help="search keyword")
    parser.add_argument("--keyword", dest="keyword_opt", help="search keyword")
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()
    keyword = str(args.keyword_opt or args.keyword or "").strip()
    if not keyword:
        raise ValueError("keyword不能为空，请使用位置参数 keyword 或 --keyword")
    result = create_rss_task(keyword)
    print(f"task_name={result['task_name']}, total={result['valid_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
