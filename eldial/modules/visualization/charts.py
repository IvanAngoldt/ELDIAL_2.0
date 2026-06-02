"""
Модуль визуализации результатов моделирования.

Построение графиков концентрации, плотности тока, энергопотребления.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from eldial.core.config import get_config
from eldial.domain.entities import ModelResult, TimeSeriesPoint


class ChartBuilder:
    """Построение графиков результатов."""

    def __init__(self):
        self.config = get_config()
        self.config.ensure_directories()

    def plot_concentration(self, time_series: list[TimeSeriesPoint], output_path: Path | None = None) -> Path:
        times = [p.time_min for p in time_series]
        c_dil = [p.diluate_concentration_g_l for p in time_series]
        c_conc = [p.concentrate_concentration_g_l for p in time_series]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(times, c_dil, "o-", color="#2e7d9a", linewidth=2, label="Разбавительная камера")
        ax.plot(times, c_conc, "s--", color="#d97706", linewidth=2, label="Концентратная камера")
        ax.set_xlabel("Время, мин")
        ax.set_ylabel("Концентрация NaCl, г/л")
        ax.set_title("Изменение концентрации в ходе электродиализа")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        path = output_path or self.config.exports_dir / "concentration_profile.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    def plot_current_density(self, time_series: list[TimeSeriesPoint], output_path: Path | None = None) -> Path:
        times = [p.time_min for p in time_series]
        j = [p.current_density_a_m2 for p in time_series]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(times, j, color="#2e7d9a", linewidth=2)
        ax.fill_between(times, j, alpha=0.2, color="#2e7d9a")
        ax.set_xlabel("Время, мин")
        ax.set_ylabel("Плотность тока, А/м²")
        ax.set_title("Плотность тока вдоль процесса")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        path = output_path or self.config.exports_dir / "current_density.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)
        plt.close(fig)
        return path

    def plot_from_result(self, result: ModelResult) -> list[Path]:
        paths = []
        if result.time_series:
            paths.append(self.plot_concentration(result.time_series))
            paths.append(self.plot_current_density(result.time_series))
        return paths

    def plot_concentration_demo(self) -> Path:
        """Демонстрационный график для UI."""
        t = np.linspace(0, 120, 50)
        c = 5.0 * np.exp(-0.03 * t)
        series = [
            TimeSeriesPoint(
                time_min=float(tm),
                diluate_concentration_g_l=float(cv),
                concentrate_concentration_g_l=float(5 - cv + 0.5),
                current_a=3.5,
                voltage_v=12.0,
                power_w=42.0,
            )
            for tm, cv in zip(t[::5], c[::5])
        ]
        return self.plot_concentration(series)
