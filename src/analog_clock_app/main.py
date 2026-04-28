from __future__ import annotations

import threading
import webbrowser

from analog_clock_app.ui.app import run


def main() -> None:
    threading.Timer(1.0, lambda: webbrowser.open_new_tab("http://localhost:8080/")).start()
    run()


if __name__ == "__main__":
    main()

