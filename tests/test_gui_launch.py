from __future__ import annotations

import unittest
from unittest.mock import patch

from gui import launch_app


class GuiLaunchTests(unittest.TestCase):
    def test_launch_app_enters_main_window_after_onboarding_completed(self) -> None:
        wizard = None
        app = None
        with (
            patch("gui.OnboardingWizard") as wizard_cls,
            patch("gui.MainWindow") as app_cls,
        ):
            wizard = wizard_cls.return_value
            wizard.run.return_value = True
            app = app_cls.return_value
            launch_app()

        wizard_cls.assert_called_once()
        wizard.run.assert_called_once()
        app_cls.assert_called_once()
        app.mainloop.assert_called_once()

    def test_launch_app_stops_when_onboarding_not_completed(self) -> None:
        with (
            patch("gui.OnboardingWizard") as wizard_cls,
            patch("gui.MainWindow") as app_cls,
        ):
            wizard = wizard_cls.return_value
            wizard.run.return_value = False
            launch_app()

        wizard_cls.assert_called_once()
        wizard.run.assert_called_once()
        app_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
