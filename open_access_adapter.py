import re
import os
import hashlib
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from curl_cffi import requests


class OpenAccessAdapter:
    def __init__(self, output_dir="downloads", timeout=30):
        self.output_dir = output_dir
        self.timeout = timeout
        os.makedirs(output_dir, exist_ok=True)

        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def download(self, article_url: str) -> dict:
        html = self.fetch_html(article_url)
        pdf_url = self.extract_pdf_url(article_url, html)

        if not pdf_url:
            return {
                "success": False,
                "article_url": article_url,
                "pdf_url": "",
                "filename": "",
                "error": "未找到 PDF 地址",
            }

        filename = self.build_filename(article_url, pdf_url)
        filepath = os.path.join(self.output_dir, filename)

        ok = self.download_pdf(pdf_url, filepath)

        return {
            "success": ok,
            "article_url": article_url,
            "pdf_url": pdf_url,
            "filename": filepath if ok else "",
            "error": "" if ok else "下载失败或文件不是 PDF",
        }

    def fetch_html(self, url: str) -> str:
        resp = requests.get(
            url,
            headers=self.headers,
            timeout=self.timeout,
            impersonate="chrome120",
        )
        resp.raise_for_status()
        return resp.text

    def extract_pdf_url(self, article_url: str, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # 1. 最通用：citation_pdf_url
        pdf_url = self.get_meta(soup, "citation_pdf_url")
        if pdf_url:
            return urljoin(article_url, pdf_url)

        # 2. 常见 meta
        for name in [
            "dc.identifier",
            "DC.Identifier",
            "eprints.document_url",
        ]:
            value = self.get_meta(soup, name)
            if value and ".pdf" in value.lower():
                return urljoin(article_url, value)

        # 3. 页面 a 标签里找 PDF
        pdf_url = self.find_pdf_link(article_url, soup)
        if pdf_url:
            return pdf_url

        # 4. 站点规则补丁
        return self.site_specific_pdf_url(article_url)

    def get_meta(self, soup: BeautifulSoup, name: str) -> str:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()

        tag = soup.find("meta", attrs={"property": name})
        if tag and tag.get("content"):
            return tag["content"].strip()

        return ""

    def find_pdf_link(self, article_url: str, soup: BeautifulSoup) -> str:
        candidates = []

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(" ", strip=True).lower()
            href_lower = href.lower()

            if (
                ".pdf" in href_lower
                or "download pdf" in text
                or text == "pdf"
                or "pdf" in text
            ):
                candidates.append(urljoin(article_url, href))

        # 优先真正 .pdf
        for url in candidates:
            if ".pdf" in url.lower():
                return url

        return candidates[0] if candidates else ""

    def site_specific_pdf_url(self, article_url: str) -> str:
        domain = self.normalize_domain(article_url)

        # MDPI:
        # https://www.mdpi.com/2077-0375/16/3/89
        # https://www.mdpi.com/2077-0375/16/3/89/pdf
        if domain.endswith("mdpi.com"):
            return article_url.rstrip("/") + "/pdf"

        # PLOS:
        # https://journals.plos.org/plosntds/article?id=10.1371/journal.pntd.0012999
        # PDF 一般可以通过 type=printable 或页面 meta 找到，兜底如下
        if "journals.plos.org" in domain:
            if "?" in article_url:
                return article_url + "&type=printable"
            return article_url + "?type=printable"

        # bioRxiv:
        # https://www.biorxiv.org/lookup/doi/10.xxxx
        # 常见 PDF:
        # /content/10.xxxx.full.pdf
        if domain.endswith("biorxiv.org"):
            if "/lookup/doi/" in article_url:
                doi = article_url.split("/lookup/doi/", 1)[1]
                return f"https://www.biorxiv.org/content/{doi}.full.pdf"

        # Theranostics:
        # https://www.thno.org/v15p9643.htm
        # https://www.thno.org/v15p9643.pdf
        if domain.endswith("thno.org"):
            return re.sub(r"\.htm[l]?$", ".pdf", article_url)

        # Beilstein 通常 meta 里有，这里兜底找 /download/pdf/
        if domain.endswith("beilstein-journals.org"):
            return ""

        # Frontiers / DovePress / BMC 通常 meta 或 a 标签能拿到
        return ""

    def download_pdf(self, pdf_url: str, filepath: str) -> bool:
        try:
            resp = requests.get(
                pdf_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/pdf,*/*",
                },
                timeout=self.timeout,
                impersonate="chrome120",
            )

            if resp.status_code >= 400:
                return False

            content = resp.content

            # 判断是不是 PDF
            if not content.startswith(b"%PDF"):
                return False

            with open(filepath, "wb") as f:
                f.write(content)

            return True

        except Exception:
            return False

    def build_filename(self, article_url: str, pdf_url: str) -> str:
        parsed = urlparse(article_url)
        raw = parsed.path.strip("/") or article_url
        raw = re.sub(r"[^a-zA-Z0-9._-]+", "_", raw)

        if len(raw) > 120:
            raw = raw[:120]

        digest = hashlib.md5(article_url.encode("utf-8")).hexdigest()[:8]

        return f"{raw}_{digest}.pdf"

    def normalize_domain(self, url: str) -> str:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain


if __name__ == "__main__":
    urls = [
        "https://www.mdpi.com/2077-0375/16/3/89",
        "https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2025.1669104/full",
        "https://journals.plos.org/plosntds/article?id=10.1371/journal.pntd.0012999",
        "https://www.biorxiv.org/lookup/doi/10.64898/2026.03.02.708638",
        "https://www.thno.org/v15p9643.htm",
        "https://www.beilstein-journals.org/bjnano/articles/16/57",
        "https://genomebiology.biomedcentral.com/articles/10.1186/gb-2011-12-1-r8",
    ]

    adapter = OpenAccessAdapter(output_dir="downloads")

    for url in urls:
        result = adapter.download(url)
        print(result)