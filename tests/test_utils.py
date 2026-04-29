from __future__ import annotations

import unittest
from unittest.mock import patch

from core.utils import is_mac


class UtilsTests(unittest.TestCase):
    def test_is_mac_true_on_darwin(self) -> None:
        with patch("core.utils.sys.platform", "darwin"):
            self.assertTrue(is_mac())

    def test_is_mac_false_on_non_darwin(self) -> None:
        with patch("core.utils.sys.platform", "win32"):
            self.assertFalse(is_mac())


if __name__ == "__main__":
    unittest.main()
