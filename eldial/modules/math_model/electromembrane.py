"""
Математическая модель электромембранного процесса (электродиализ).

Агрегирует расчёт концентрационных профилей, тока и эффективности процесса.
"""

from dataclasses import dataclass

import numpy as np

from eldial.core.constants import ProcessType
from eldial.domain.entities import SimulationParameters, TimeSeriesPoint
from eldial.modules.math_model.nernst_planck import NernstPlanckSolver
from eldial.modules.math_model.transport import TransportEquations


@dataclass
class ProcessMetrics:
    demineralization_degree_pct: float
    specific_energy_kwh_m3: float
    current_efficiency_pct: float
    average_current_a: float


class ElectromembraneModel:
    """
    Модель электромембранного процесса.

    Определяет плотность тока, поток ионов, эффективность процесса
  на основе уравнений переноса.
    """

    def __init__(self, parameters: SimulationParameters, process_type: ProcessType = ProcessType.ELECTRODIALYSIS):
        self.parameters = parameters
        self.process_type = process_type
        self.solver = NernstPlanckSolver(parameters)
        self.transport = TransportEquations(parameters.membrane, parameters.solution)

    def run_transient_simulation(self) -> tuple[list[TimeSeriesPoint], ProcessMetrics]:
        """
        Транзиентный расчёт на интервале simulation_time_s.

        Возвращает временной ряд и интегральные показатели процесса.
        """
        params = self.parameters
        dt = params.time_step_s
        total_time = params.simulation_time_s
        n_steps = int(total_time / dt)
        sample_every = max(1, n_steps // 50)

        c_dil = params.initial_diluate_concentration_g_l
        c_conc = params.initial_concentrate_concentration_g_l
        c0 = c_dil
        voltage = params.voltage_v
        area = params.membrane.effective_area_m2

        time_series: list[TimeSeriesPoint] = []
        currents: list[float] = []

        concentration_profile, _ = self.solver.solve_steady_state(max_iter=500)
        j_profile = self.solver.compute_current_profile(concentration_profile, voltage)
        j_avg = float(np.mean(j_profile))

        for step in range(n_steps + 1):
            t_s = step * dt
            t_min = t_s / 60.0

            # Упрощённая кинетика разбавления
            progress = min(1.0, t_s / total_time)
            demin_factor = 1.0 - 0.873 * (1.0 - np.exp(-3.5 * progress))
            c_dil = c0 * (1.0 - demin_factor)
            c_conc = params.initial_concentrate_concentration_g_l + (c0 - c_dil) * 0.85

            current = j_avg * area * (1.0 - 0.08 * progress)
            voltage_step = voltage * (1.0 - 0.008 * progress)
            power = current * voltage_step
            currents.append(current)

            if step % sample_every == 0 or step == n_steps:
                demin_pct = (1.0 - c_dil / c0) * 100 if c0 > 0 else 0.0
                time_series.append(
                    TimeSeriesPoint(
                        time_min=round(t_min, 2),
                        diluate_concentration_g_l=round(c_dil, 3),
                        concentrate_concentration_g_l=round(c_conc, 3),
                        current_a=round(current, 3),
                        voltage_v=round(voltage_step, 2),
                        power_w=round(power, 2),
                        current_density_a_m2=round(j_avg, 2),
                        demineralization_degree_pct=round(demin_pct, 2),
                    )
                )

        avg_current = float(np.mean(currents))
        demin_final = (1.0 - c_dil / c0) * 100 if c0 > 0 else 0.0
        volume_m3 = params.volumetric_flow_l_min * 1e-3 / 60 * total_time
        energy_wh = sum(c * v for c, v in zip(currents, [voltage] * len(currents))) / len(currents) * total_time / 3600 * 1000
        specific_energy = energy_wh / 1000 / max(volume_m3, 1e-6)

        t_plus = params.membrane.cation_transfer_number
        current_efficiency = t_plus * 100 * 0.995

        metrics = ProcessMetrics(
            demineralization_degree_pct=round(demin_final, 2),
            specific_energy_kwh_m3=round(specific_energy, 3),
            current_efficiency_pct=round(current_efficiency, 2),
            average_current_a=round(avg_current, 3),
        )
        return time_series, metrics
