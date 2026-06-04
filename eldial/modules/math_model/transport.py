"""
Уравнения переноса вещества и заряда в электромембранных системах.

Реализация упрощённой модели на основе уравнений Нернста-Планка.
"""

import numpy as np

from eldial.core.constants import FARADAY_CONSTANT, GAS_CONSTANT
from eldial.domain.entities import MembraneProperties, SolutionProperties


class TransportEquations:
    """Расчёт потоков ионов и плотности тока."""

    def __init__(
        self,
        membrane: MembraneProperties,
        solution: SolutionProperties,
    ):
        self.membrane = membrane
        self.solution = solution
        self.temperature_k = solution.temperature_c + 273.15

    def diffusion_flux(self, concentration_gradient: np.ndarray) -> np.ndarray:
        """Диффузионный поток: J_d = -D * grad(C)."""
        d = self.membrane.diffusion_coefficient_m2_s
        return -d * concentration_gradient

    def migration_flux(
        self,
        concentration: np.ndarray,
        electric_field: np.ndarray,
        charge_number: int = 1,
    ) -> np.ndarray:
        """Миграционный поток: J_m = -z * F * D * C * grad(phi) / (R * T)."""
        z = charge_number
        d = self.membrane.diffusion_coefficient_m2_s
        c = concentration
        rt = GAS_CONSTANT * self.temperature_k
        return -z * FARADAY_CONSTANT * d * c * electric_field / rt

    def total_ion_flux(
        self,
        concentration: np.ndarray,
        concentration_gradient: np.ndarray,
        electric_field: np.ndarray,
        charge_number: int = 1,
    ) -> np.ndarray:
        """Суммарный поток по уравнению Нернста-Планка."""
        j_diff = self.diffusion_flux(concentration_gradient)
        j_migr = self.migration_flux(concentration, electric_field, charge_number)
        return j_diff + j_migr

    def current_density(self, ion_flux: np.ndarray, charge_number: int = 1) -> np.ndarray:
        """Плотность тока j = z * F * J."""
        return charge_number * FARADAY_CONSTANT * ion_flux

    def membrane_resistance(self) -> float:
        """Удельное сопротивление мембранного стека (Ом).

        Формула: R = 2 * N * rho / S, где N — число пар мембран,
        rho — удельное сопротивление (Ом·м), S — эффективная площадь (м²).
        """
        n_pairs = self.membrane.membrane_pairs
        rho_m = self.membrane.membrane_resistivity_ohm_m
        area = self.membrane.effective_area_m2
        return 2 * n_pairs * rho_m / area

    def limiting_current_density(self, bulk_concentration_mol_m3: float) -> float:
        """Предельная плотность тока (А/м²), упрощённая оценка Лева.

        Формула: j_lim = z * F * D * C_bulk / delta,
        где delta — толщина диффузионного слоя (м).
        """
        d = self.membrane.diffusion_coefficient_m2_s
        delta = self.membrane.channel_thickness_mm * 1e-3
        z = 1
        return z * FARADAY_CONSTANT * d * bulk_concentration_mol_m3 / delta
