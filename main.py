#!/usr/bin/env python3
"""
ElDial — точка входа.

  python3 main.py          — GUI (Tkinter) или веб-mock
  python3 main.py --web    — только веб-интерфейс для скриншотов
  python3 main.py --demo   — консольный демо-расчёт
  python3 -m eldial.app    — альтернативный запуск
"""

import sys


def run_web_mock() -> None:
    import http.server
    import socketserver
    import webbrowser
    from pathlib import Path

    port = 8765
    mock_dir = Path(__file__).parent / "mock"
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(mock_dir), **kwargs
    )
    url = f"http://localhost:{port}/index.html"
    print(f"ElDial mock UI: {url}")
    webbrowser.open(url)
    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nОстановлено.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--web":
        run_web_mock()
    else:
        from eldial.app import main
        main()
