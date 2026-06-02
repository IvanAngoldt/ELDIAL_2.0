"""
Модуль пользовательского интерфейса.

Реализация на Tkinter (согласно отчёту ЛР4).
При отсутствии Tkinter — запуск веб-интерфейса mock/.
"""

import logging
import sys
import webbrowser
from pathlib import Path

from eldial.core.config import get_config

logger = logging.getLogger(__name__)


class EldialApplication:
    """Точка входа GUI-приложения."""

    def __init__(self):
        self.config = get_config()
        self.config.ensure_directories()

    def run(self) -> None:
        try:
            import tkinter as tk
            from eldial.modules.ui.main_window import MainWindow

            root = tk.Tk()
            app = MainWindow(root)
            root.mainloop()
        except ImportError:
            logger.warning("Tkinter недоступен, запуск веб-интерфейса")
            self._run_web_fallback()

    def _run_web_fallback(self) -> None:
        mock_dir = self.config.base_dir / "mock" / "index.html"
        if mock_dir.exists():
            webbrowser.open(mock_dir.as_uri())
            print(f"Открыт веб-интерфейс: {mock_dir}")
            print("Для полного UI установите Python с поддержкой Tk.")
        else:
            print("Интерфейс недоступен: нет Tkinter и каталога mock/", file=sys.stderr)
