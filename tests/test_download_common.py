from __future__ import annotations

import unittest

from publisher_download.common import extract_first_si_url


class DownloadCommonTests(unittest.TestCase):
    def test_extract_first_si_url_returns_first_match(self) -> None:
        html = """
        <a href="/doi/suppl/10.1000/x/suppl_file/suppl.pdf">Supporting Information 1</a>
        <a href="/doi/suppl/10.1000/x/suppl_file/suppl2.pdf">Supporting Information 2</a>
        """
        url = extract_first_si_url(html, "https://onlinelibrary.wiley.com/doi/10.1000/x")
        self.assertEqual(url, "https://onlinelibrary.wiley.com/doi/suppl/10.1000/x/suppl_file/suppl.pdf")

    def test_extract_first_si_url_returns_empty_when_not_found(self) -> None:
        html = "<a href='/doi/full/10.1000/x'>Full Text</a>"
        url = extract_first_si_url(html, "https://onlinelibrary.wiley.com/doi/10.1000/x")
        self.assertEqual(url, "")


if __name__ == "__main__":
    unittest.main()
