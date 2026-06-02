"""Экран ввода параметров моделирования."""

import tkinter as tk
from tkinter import messagebox, ttk

from eldial.modules.computation.engine import ComputationEngine
from eldial.modules.parameters.forms import ParameterFormData
from eldial.modules.parameters.service import ParameterInputService
from eldial.domain.entities import SimulationRun
from eldial.core.constants import SimulationStatus


class ParametersWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Ввод параметров моделирования")
        self.geometry("750x550")
        self._service = ParameterInputService()
        self._build()

    def _build(self) -> None:
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=12)

        self.form = ParameterFormData()
        tab1 = ttk.Frame(nb, padding=8)
        nb.add(tab1, text="Мембрана")
        self._add_field(tab1, "Число пар мембран", "membrane_pairs")
        self._add_field(tab1, "Площадь элемента, м²", "effective_area")
        self._add_field(tab1, "Напряжение, В", "voltage")

        tab2 = ttk.Frame(nb, padding=8)
        nb.add(tab2, text="Раствор")
        self._add_field(tab2, "NaCl, г/л", "nacl_concentration")
        self._add_field(tab2, "Температура, °C", "temperature")

        ttk.Button(self, text="Запустить моделирование", command=self._run).pack(pady=8)

    def _add_field(self, parent: ttk.Frame, label: str, attr: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=28).pack(side="left")
        e = ttk.Entry(row, width=20)
        e.insert(0, getattr(self.form, attr))
        e.pack(side="left")
        setattr(self, f"_entry_{attr}", e)

    def _run(self) -> None:
        for attr in self.form.__dataclass_fields__:
            entry = getattr(self, f"_entry_{attr}", None)
            if entry:
                setattr(self.form, attr, entry.get())
        try:
            params = self._service.parse_form(self.form, project_id=1)
            run = SimulationRun(id=1, project_id=1, parameters=params, status=SimulationStatus.QUEUED)
            engine = ComputationEngine()
            result = engine.run_simulation(run, params)
            messagebox.showinfo(
                "Готово",
                f"Деминерализация: {result.demineralization_degree_pct}%\n"
                f"Токовая эффективность: {result.current_efficiency_pct}%",
            )
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
