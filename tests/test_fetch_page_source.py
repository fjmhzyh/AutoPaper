from __future__ import annotations

import unittest
from unittest.mock import patch

from core.utils import get_html_content


class FetchPageSourceTests(unittest.TestCase):
    def test_get_html_content_uses_expected_hotkeys_and_clipboard(self) -> None:
        calls: list[str] = []
        with (
            patch("core.utils.gui.hotkey", side_effect=lambda action: calls.append(action)),
            patch("core.utils.time.sleep", return_value=None),
            patch("core.utils._read_clipboard", return_value="<html>demo</html>"),
        ):
            content = get_html_content(5)

        self.assertEqual(calls, ["view_source", "select_all", "copy"])
        self.assertEqual(content, "<html>demo</html>")


if __name__ == "__main__":
    unittest.main()
