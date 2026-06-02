"""Главное окно приложения ElDial (Tkinter)."""

import tkinter as tk
from tkinter import messagebox, ttk

from eldial import __version__


class MainWindow:
    """Главное окно — навигация по функциям системы."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ElDial — Моделирование электромембранных процессов")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        self._build_ui()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg="#1a3a5c", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="ElDial",
            font=("Helvetica", 22, "bold"),
            bg="#1a3a5c",
            fg="white",
        ).pack(pady=(12, 0))
        tk.Label(
            header,
            text="Программная система для моделирования электромембранных процессов",
            font=("Helvetica", 10),
            bg="#1a3a5c",
            fg="#94b8cc",
        ).pack()

        body = tk.Frame(self.root, padx=24, pady=24)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Выберите действие:", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 12))

        actions = [
            ("Создать проект моделирования", self._open_project_create),
            ("Ввод параметров моделирования", self._open_parameters),
            ("Результаты моделирования", self._open_results),
            ("Формирование отчёта", self._open_report),
        ]
        for text, cmd in actions:
            ttk.Button(body, text=text, command=cmd, width=45).pack(pady=6, anchor="w")

        status = tk.Label(
            body,
            text=f"Версия {__version__} | Python + Tkinter + NumPy + Matplotlib",
            font=("Helvetica", 9),
            fg="#64748b",
        )
        status.pack(side="bottom", anchor="w", pady=(24, 0))

    def _open_project_create(self) -> None:
        from eldial.modules.ui.windows.project_window import ProjectCreateWindow
        ProjectCreateWindow(self.root)

    def _open_parameters(self) -> None:
        from eldial.modules.ui.windows.parameters_window import ParametersWindow
        ParametersWindow(self.root)

    def _open_results(self) -> None:
        from eldial.modules.ui.windows.results_window import ResultsWindow
        ResultsWindow(self.root)

    def _open_report(self) -> None:
        from eldial.modules.ui.windows.report_window import ReportWindow
        ReportWindow(self.root)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)
