"""
Численное решение системы уравнений Нернста-Планка.

Метод: неявная схема Кранка-Николсона по пространственной координате.
"""

import numpy as np

from eldial.core.exceptions import ModelError
from eldial.domain.entities import SimulationParameters
from eldial.modules.math_model.transport import TransportEquations


class NernstPlanckSolver:
    """Решатель уравнений переноса для одномерной геометрии канала."""

    def __init__(self, parameters: SimulationParameters):
        self.params = parameters
        self.transport = TransportEquations(
            parameters.membrane,
            parameters.solution,
        )
        self.nx = parameters.grid_nodes
        self.dx = parameters.membrane.channel_length_m / (self.nx - 1)

    def build_initial_concentration(self) -> np.ndarray:
        """Начальное распределение концентрации в разбавительной камере."""
        molar_mass_nacl = 58.44  # г/моль
        c0 = self.params.initial_diluate_concentration_g_l / molar_mass_nacl
        return np.full(self.nx, c0)

    def build_electric_field(self, voltage: float) -> np.ndarray:
        """Равномерное электрическое поле вдоль канала."""
        length = self.params.membrane.channel_length_m
        return np.full(self.nx, voltage / length)

    def crank_nicolson_step(
        self,
        concentration: np.ndarray,
        dt: float,
        voltage: float,
    ) -> np.ndarray:
        """
        Один шаг интегрирования по времени (упрощённая CN-схема).
        """
        electric_field = self.build_electric_field(voltage)
        grad_c = np.gradient(concentration, self.dx)
        flux = self.transport.total_ion_flux(concentration, grad_c, electric_field)
        div_flux = np.gradient(flux, self.dx)
        c_new = concentration - dt * div_flux
        c_new = np.clip(c_new, 0.0, None)
        return c_new

    def solve_steady_state(
        self,
        max_iter: int | None = None,
        tolerance: float | None = None,
    ) -> tuple[np.ndarray, int]:
        """Итерационный поиск квазистационарного профиля концентрации."""
        max_iter = max_iter or self.params.max_iterations
        tolerance = tolerance or self.params.convergence_tolerance

        c = self.build_initial_concentration()
        voltage = self.params.voltage_v
        dt = self.params.time_step_s

        residual = float("inf")
        for iteration in range(max_iter):
            c_old = c.copy()
            c = self.crank_nicolson_step(c, dt, voltage)
            residual = np.linalg.norm(c - c_old) / (np.linalg.norm(c_old) + 1e-12)
            if residual < tolerance:
                return c, iteration + 1

        raise ModelError(
            f"Сходимость не достигнута за {max_iter} итераций: "
            f"остаток={residual:.2e}, допуск={tolerance:.2e}. "
            "Попробуйте уменьшить шаг по времени или увеличить max_iterations."
        )

    def compute_current_profile(self, concentration: np.ndarray, voltage: float) -> np.ndarray:
        """Профиль плотности тока вдоль канала."""
        electric_field = self.build_electric_field(voltage)
        grad_c = np.gradient(concentration, self.dx)
        flux = self.transport.total_ion_flux(concentration, grad_c, electric_field)
        return self.transport.current_density(flux)
