from __future__ import annotations

import unittest
from unittest.mock import patch

from publisher_login.router import login_by_url


class LoginRouterTests(unittest.TestCase):
    def test_wiley_domain_matches_suffix(self) -> None:
        with patch("publisher_login.router.wiley.login", return_value=True) as login_mock:
            ok = login_by_url("https://onlinelibrary.wiley.com/doi/abs/10.1002/9781118676684.ch8")
        self.assertTrue(ok)
        login_mock.assert_called_once()

    def test_unmatched_domain_skips(self) -> None:
        with self.assertLogs("publisher_login.router", level="INFO") as cm:
            ok = login_by_url("https://example.com/a")
        self.assertTrue(ok)
        self.assertIn("未匹配登录器", "\n".join(cm.output))
        self.assertIn("example.com", "\n".join(cm.output))

    def test_invalid_or_empty_url_skips(self) -> None:
        ok_1 = login_by_url("")
        ok_2 = login_by_url("not-a-url")
        self.assertTrue(ok_1)
        self.assertTrue(ok_2)

    def test_other_supported_domains_are_matched_as_skip_placeholders(self) -> None:
        with patch("publisher_login.router.acs.login", return_value=True) as login_mock:
            ok = login_by_url("https://pubs.acs.org/doi/10.1021/x")
        self.assertTrue(ok)
        login_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
