"""Экран создания проекта моделирования."""

import tkinter as tk
from tkinter import messagebox, ttk

from eldial.core.constants import ProcessType, TransportModel
from eldial.domain.entities import Project


class ProjectCreateWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Создание проекта моделирования")
        self.geometry("700x500")
        self._build()

    def _build(self) -> None:
        frame = ttk.LabelFrame(self, text="Общие сведения", padding=12)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        fields = [
            ("Наименование:", "Электродиализ NaCl — опытный стенд №3"),
            ("Описание:", "Моделирование деминерализации рассола"),
            ("Автор:", "Иванов И.И."),
        ]
        self.entries = {}
        for i, (label, default) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=4)
            e = ttk.Entry(frame, width=50)
            e.insert(0, default)
            e.grid(row=i, column=1, pady=4, padx=8)
            self.entries[label] = e

        ttk.Label(frame, text="Тип процесса:").grid(row=3, column=0, sticky="w", pady=4)
        self.process_var = tk.StringVar(value=ProcessType.ELECTRODIALYSIS.value)
        ttk.Combobox(
            frame,
            textvariable=self.process_var,
            values=[p.value for p in ProcessType],
            state="readonly",
            width=47,
        ).grid(row=3, column=1, pady=4, padx=8)

        ttk.Button(self, text="Создать проект", command=self._create).pack(pady=12)

    def _create(self) -> None:
        name = self.entries["Наименование:"].get()
        project = Project(id=None, user_id=1, name=name, process_type=ProcessType.ELECTRODIALYSIS)
        messagebox.showinfo("Проект", f"Проект «{project.name}» создан (демо-режим).")
