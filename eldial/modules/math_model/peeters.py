"""
Упрощённая модель Peeters для электродиализа.

Альтернативная математическая модель (см. отчёт ЛР4).
"""

from dataclasses import dataclass

import numpy as np

from eldial.domain.entities import SimulationParameters


@dataclass
class PeetersResult:
    outlet_concentration: float
    current_utilization: float
    specific_power: float


class PeetersModel:
    """Упрощённая стационарная модель без полного решения NP."""

    def __init__(self, parameters: SimulationParameters):
        self.params = parameters

    def compute(self) -> PeetersResult:
        c0 = self.params.solution.nacl_concentration_g_l
        u = self.params.voltage_v
        n = self.params.membrane.membrane_pairs
        # Эмпирическая оценка для демонстрации
        removal = 1.0 - np.exp(-0.02 * u * n / 100)
        c_out = c0 * (1.0 - removal)
        return PeetersResult(
            outlet_concentration=float(c_out),
            current_utilization=float(self.params.membrane.cation_transfer_number * 100),
            specific_power=float(u * 0.3),
        )
