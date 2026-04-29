from .main_window import MainWindow


def launch_app() -> None:
    app = MainWindow()
    app.mainloop()


__all__ = ["MainWindow", "launch_app"]
