"""Экран отображения результатов моделирования."""

import tkinter as tk
from tkinter import ttk

from eldial.modules.visualization.charts import ChartBuilder
from eldial.modules.visualization.tables import ResultsTableBuilder


class ResultsWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Результаты моделирования")
        self.geometry("800x600")
        self._build()

    def _build(self) -> None:
        metrics = ttk.LabelFrame(self, text="Сводные показатели", padding=12)
        metrics.pack(fill="x", padx=12, pady=12)
        for label, val in [
            ("Степень деминерализации", "87.3 %"),
            ("Удельное энергопотребление", "2.14 кВт·ч/м³"),
            ("Токовая эффективность", "91.6 %"),
        ]:
            row = ttk.Frame(metrics)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=35).pack(side="left")
            ttk.Label(row, text=val, font=("", 11, "bold")).pack(side="left")

        table_frame = ttk.LabelFrame(self, text="Таблица результатов", padding=8)
        table_frame.pack(fill="both", expand=True, padx=12, pady=8)

        builder = ResultsTableBuilder()
        df = builder.build_demo_table()
        cols = list(df.columns)
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=8)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=90)
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
        tree.pack(fill="both", expand=True)

        ttk.Button(self, text="Построить графики", command=self._show_charts).pack(pady=8)

    def _show_charts(self) -> None:
        builder = ChartBuilder()
        path = builder.plot_concentration_demo()
        tk.messagebox.showinfo("График", f"Сохранён: {path}")
