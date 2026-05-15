import csv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from curl_cffi import requests

INPUT_FILE = "doi1000.csv"

PUBLISHER_OUTPUT_FILE = "publisher_address.txt"
DETAIL_OUTPUT_FILE = "doi_resolve_result.csv"

MAX_WORKERS = 20
TIMEOUT = 20
SAVE_EVERY = 20


def normalize_doi(raw: str) -> str:
    if not raw:
        return ""

    doi = raw.strip()
    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("doi:", "")
    return doi.strip()


def normalize_domain(url: str) -> str:
    domain = urlparse(url).netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def read_dois_from_csv(file_path: str) -> list[str]:
    dois = []

    with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames or "DOI" not in reader.fieldnames:
            raise ValueError("CSV 文件中没有找到 DOI 列")

        for row in reader:
            doi = normalize_doi(row.get("DOI", ""))
            if doi:
                dois.append(doi)

    return dois


def is_resolved_url(url: str) -> bool:
    domain = normalize_domain(url)
    return domain not in ("doi.org", "dx.doi.org")


def resolve_doi(doi: str) -> dict:
    doi_url = f"https://doi.org/{doi}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    last_error = ""

    for attempt in range(3):
        try:
            resp = requests.get(
                doi_url,
                headers=headers,
                allow_redirects=True,
                timeout=TIMEOUT,
                impersonate="chrome120",
            )

            redirect_chain = [doi_url]

            for item in resp.history:
                redirect_chain.append(item.url)

            redirect_chain.append(resp.url)
            redirect_chain = list(dict.fromkeys(redirect_chain))

            final_url = resp.url
            domain = normalize_domain(final_url)

            return {
                "doi": doi,
                "status_code": resp.status_code,
                "final_url": final_url,
                "domain": domain,
                "resolved": is_resolved_url(final_url),
                "redirect_count": max(len(redirect_chain) - 1, 0),
                "redirect_chain": " -> ".join(redirect_chain),
                "error": "",
            }

        except Exception as e:
            last_error = str(e)
            time.sleep(1 + attempt)

    return {
        "doi": doi,
        "status_code": "",
        "final_url": "",
        "domain": "",
        "resolved": False,
        "redirect_count": 0,
        "redirect_chain": doi_url,
        "error": last_error,
    }


def save_publisher_addresses(unique_publishers: dict):
    with open(PUBLISHER_OUTPUT_FILE, "w", encoding="utf-8") as f:
        for url in unique_publishers.values():
            f.write(url + "\n")


def save_detail_results(results: list[dict]):
    fieldnames = [
        "doi",
        "status_code",
        "final_url",
        "domain",
        "resolved",
        "redirect_count",
        "redirect_chain",
        "error",
    ]

    with open(DETAIL_OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def save_progress(unique_publishers: dict, results: list[dict]):
    save_publisher_addresses(unique_publishers)
    save_detail_results(results)


def main():
    dois = read_dois_from_csv(INPUT_FILE)

    print(f"读取到 {len(dois)} 个 DOI")

    unique_publishers = {}
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(resolve_doi, doi): doi
            for doi in dois
        }

        for index, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            results.append(result)

            if result["resolved"]:
                domain = result["domain"]

                if domain not in unique_publishers:
                    unique_publishers[domain] = result["final_url"]
                    print(f"[新增网站] {domain} -> {result['final_url']}")

            print(
                f"[{index}/{len(dois)}] "
                f"{result['status_code']} "
                f"redirect={result['redirect_count']} "
                f"{result['final_url'] or result['error']}"
            )

            if index % SAVE_EVERY == 0:
                save_progress(unique_publishers, results)
                print(f"已保存进度：{index}/{len(dois)}")

    save_progress(unique_publishers, results)

    print("\n完成")
    print(f"共解析 DOI：{len(results)}")
    print(f"共发现网站：{len(unique_publishers)}")
    print(f"网站地址文件：{PUBLISHER_OUTPUT_FILE}")
    print(f"详细结果文件：{DETAIL_OUTPUT_FILE}")


if __name__ == "__main__":
    main()