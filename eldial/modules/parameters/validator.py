"""
Модуль валидации параметров моделирования.

Алгоритм ввода параметров: проверка диапазонов, целостности, подготовка данных для вычислительного модуля.
"""

from eldial.core.constants import (
    MAX_CONCENTRATION,
    MAX_MEMBRANE_PAIRS,
    MAX_TEMPERATURE,
    MAX_VOLTAGE,
    MIN_CONCENTRATION,
    MIN_MEMBRANE_PAIRS,
    MIN_TEMPERATURE,
    MIN_VOLTAGE,
)
from eldial.core.exceptions import ValidationError
from eldial.domain.entities import MembraneProperties, SimulationParameters, SolutionProperties


class ParameterValidator:
    """Валидатор входных параметров моделирования."""

    def validate_membrane(self, membrane: MembraneProperties) -> list[str]:
        errors: list[str] = []
        if not MIN_MEMBRANE_PAIRS <= membrane.membrane_pairs <= MAX_MEMBRANE_PAIRS:
            errors.append(f"Число пар мембран: допустимо {MIN_MEMBRANE_PAIRS}–{MAX_MEMBRANE_PAIRS}")
        if membrane.effective_area_m2 <= 0:
            errors.append("Площадь элемента должна быть положительной")
        if membrane.cation_transfer_number + membrane.anion_transfer_number > 1.05:
            errors.append("Сумма чисел переноса не может превышать 1")
        return errors

    def validate_solution(self, solution: SolutionProperties) -> list[str]:
        errors: list[str] = []
        if not MIN_CONCENTRATION <= solution.nacl_concentration_g_l <= MAX_CONCENTRATION:
            errors.append(f"Концентрация NaCl: допустимо {MIN_CONCENTRATION}–{MAX_CONCENTRATION} г/л")
        if not MIN_TEMPERATURE <= solution.temperature_c <= MAX_TEMPERATURE:
            errors.append(f"Температура: допустимо {MIN_TEMPERATURE}–{MAX_TEMPERATURE} °C")
        if not 0 <= solution.ph <= 14:
            errors.append("pH должен быть в диапазоне 0–14")
        return errors

    def validate_simulation(self, params: SimulationParameters) -> list[str]:
        errors: list[str] = []
        errors.extend(self.validate_membrane(params.membrane))
        errors.extend(self.validate_solution(params.solution))
        if not MIN_VOLTAGE <= params.voltage_v <= MAX_VOLTAGE:
            errors.append(f"Напряжение: допустимо {MIN_VOLTAGE}–{MAX_VOLTAGE} В")
        if params.time_step_s <= 0:
            errors.append("Шаг по времени должен быть положительным")
        if params.simulation_time_s <= params.time_step_s:
            errors.append("Время моделирования должно превышать шаг по времени")
        if params.grid_nodes < 10:
            errors.append("Число узлов сетки: минимум 10")
        return errors

    def validate_or_raise(self, params: SimulationParameters) -> None:
        errors = self.validate_simulation(params)
        if errors:
            raise ValidationError("; ".join(errors))
