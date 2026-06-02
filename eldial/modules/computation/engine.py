"""
Модуль выполнения вычислений.

Запуск численного расчёта, контроль сходимости, сохранение результатов.
"""

import logging
from datetime import datetime

from eldial.core.constants import SimulationStatus
from eldial.core.exceptions import ComputationError
from eldial.domain.entities import ModelResult, SimulationParameters, SimulationRun
from eldial.modules.math_model.electromembrane import ElectromembraneModel
from eldial.modules.storage.database import get_session
from eldial.modules.storage.repository import ResultRepository, SimulationRepository

logger = logging.getLogger(__name__)


class ComputationEngine:
    """Движок выполнения вычислительных экспериментов."""

    def __init__(self):
        self._active_runs: dict[int, SimulationRun] = {}

    def run_simulation(
        self,
        simulation: SimulationRun,
        parameters: SimulationParameters,
    ) -> ModelResult:
        """
        Алгоритм моделирования электромембранного процесса:
        1. Получить параметры расчёта
        2. Инициализировать математическую модель
        3. Выполнить численный расчёт
        4. Сохранить результаты в model_results
        """
        simulation_id = simulation.id
        if simulation_id is None:
            raise ComputationError("Идентификатор симуляции не задан")

        logger.info("Запуск моделирования simulation_id=%s", simulation_id)

        try:
            with get_session() as session:
                sim_repo = SimulationRepository(session)
                sim_repo.update_status(simulation_id, SimulationStatus.RUNNING)

            model = ElectromembraneModel(parameters)
            time_series, metrics = model.run_transient_simulation()

            result = ModelResult(
                id=None,
                simulation_id=simulation_id,
                demineralization_degree_pct=metrics.demineralization_degree_pct,
                specific_energy_kwh_m3=metrics.specific_energy_kwh_m3,
                current_efficiency_pct=metrics.current_efficiency_pct,
                average_current_a=metrics.average_current_a,
                time_series=time_series,
                metadata={
                    "process_type": parameters.project_id,
                    "grid_nodes": parameters.grid_nodes,
                    "iterations": "converged",
                },
                created_at=datetime.utcnow(),
            )

            with get_session() as session:
                result_repo = ResultRepository(session)
                result_repo.save(result)
                sim_repo = SimulationRepository(session)
                sim_repo.update_status(simulation_id, SimulationStatus.COMPLETED)

            logger.info(
                "Моделирование завершено: деминерализация=%.1f%%",
                metrics.demineralization_degree_pct,
            )
            return result

        except Exception as exc:
            logger.exception("Ошибка моделирования: %s", exc)
            try:
                with get_session() as session:
                    SimulationRepository(session).update_status(
                        simulation_id,
                        SimulationStatus.FAILED,
                        error_message=str(exc),
                    )
            except Exception:
                pass
            raise ComputationError(str(exc)) from exc

    def cancel_simulation(self, simulation_id: int) -> None:
        with get_session() as session:
            SimulationRepository(session).update_status(
                simulation_id,
                SimulationStatus.CANCELLED,
            )
