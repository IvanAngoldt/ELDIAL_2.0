"""Формирование таблиц результатов."""

import pandas as pd

from eldial.domain.entities import ModelResult, TimeSeriesPoint


class ResultsTableBuilder:
    """Построение табличного представления результатов."""

    def from_time_series(self, points: list[TimeSeriesPoint]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "t, мин": p.time_min,
                    "C_разб., г/л": p.diluate_concentration_g_l,
                    "C_конц., г/л": p.concentrate_concentration_g_l,
                    "I, А": p.current_a,
                    "U, В": p.voltage_v,
                    "P, Вт": p.power_w,
                }
                for p in points
            ]
        )

    def from_model_result(self, result: ModelResult) -> pd.DataFrame:
        if result.time_series:
            return self.from_time_series(result.time_series)
        return self.build_demo_table()

    def build_demo_table(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "t, мин": [0, 30, 60, 90, 120],
                "C_разб., г/л": [5.00, 3.42, 2.15, 1.28, 0.64],
                "C_конц., г/л": [0.50, 1.28, 2.05, 2.78, 3.42],
                "I, А": [3.85, 3.65, 3.48, 3.35, 3.22],
                "U, В": [12.0, 11.8, 11.5, 11.2, 11.0],
                "P, Вт": [46.2, 43.1, 40.0, 37.5, 35.4],
            }
        )

    def summary_metrics(self, result: ModelResult) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"Показатель": "Степень деминерализации", "Значение": f"{result.demineralization_degree_pct} %"},
                {"Показатель": "Удельное энергопотребление", "Значение": f"{result.specific_energy_kwh_m3} кВт·ч/м³"},
                {"Показатель": "Токовая эффективность", "Значение": f"{result.current_efficiency_pct} %"},
                {"Показатель": "Средний ток", "Значение": f"{result.average_current_a} А"},
            ]
        )
