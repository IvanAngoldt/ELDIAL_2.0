"""Экран формирования отчёта."""

import tkinter as tk
from tkinter import messagebox, ttk

from eldial.modules.reporting.generator import ReportGenerator
from eldial.modules.reporting.templates import ReportTemplate


class ReportWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Формирование отчёта")
        self.geometry("700x500")
        self._build()

    def _build(self) -> None:
        frame = ttk.LabelFrame(self, text="Параметры отчёта", padding=12)
        frame.pack(fill="x", padx=16, pady=16)

        ttk.Label(frame, text="Название:").grid(row=0, column=0, sticky="w")
        self.title_entry = ttk.Entry(frame, width=50)
        self.title_entry.insert(0, "Отчёт по моделированию ED — стенд №3")
        self.title_entry.grid(row=0, column=1, pady=4)

        self.sections = {}
        sections_frame = ttk.LabelFrame(self, text="Разделы", padding=8)
        sections_frame.pack(fill="both", expand=True, padx=16, pady=8)
        for name in ReportTemplate.default_sections():
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(sections_frame, text=name, variable=var).pack(anchor="w")
            self.sections[name] = var

        ttk.Button(self, text="Сформировать отчёт", command=self._generate).pack(pady=12)

    def _generate(self) -> None:
        selected = [n for n, v in self.sections.items() if v.get()]
        gen = ReportGenerator()
        path = gen.generate_demo_report(
            title=self.title_entry.get(),
            sections=selected,
        )
        messagebox.showinfo("Отчёт", f"Отчёт сформирован:\n{path}")
