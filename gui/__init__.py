from .main_window import MainWindow
from .onboarding import OnboardingWizard


def launch_app() -> None:
    wizard = OnboardingWizard()
    if not wizard.run():
        return
    app = MainWindow()
    app.mainloop()


__all__ = ["MainWindow", "launch_app"]
