"""
Фасад приложения — единая точка доступа к модулям системы.

Используется для координации сценариев: создание проекта → параметры → расчёт → отчёт.
"""

from eldial.core.constants import SimulationStatus
from eldial.domain.entities import ModelResult, Project, SimulationParameters, SimulationRun
from eldial.modules.computation.engine import ComputationEngine
from eldial.modules.parameters.forms import ParameterFormData
from eldial.modules.parameters.service import ParameterInputService
from eldial.modules.reporting.generator import ReportGenerator
from eldial.modules.reporting.templates import ReportTemplate
from eldial.modules.storage.database import get_session
from eldial.modules.storage.repository import ProjectRepository, ResultRepository, SimulationRepository
from eldial.modules.visualization.charts import ChartBuilder


class EldialFacade:
    """Высокоуровневый API программной системы."""

    def __init__(self):
        self.parameter_service = ParameterInputService()
        self.computation_engine = ComputationEngine()
        self.report_generator = ReportGenerator()
        self.chart_builder = ChartBuilder()

    def list_projects(self, user_id: int) -> list[Project]:
        with get_session() as session:
            return ProjectRepository(session).list_by_user(user_id)

    def run_full_pipeline(
        self,
        project_id: int,
        form: ParameterFormData | None = None,
    ) -> tuple[ModelResult, list]:
        """Полный цикл: параметры → расчёт → графики → отчёт."""
        form = form or ParameterFormData()
        params = self.parameter_service.parse_form(form, project_id)

        with get_session() as session:
            run = SimulationRun(
                id=None,
                project_id=project_id,
                parameters=params,
                status=SimulationStatus.QUEUED,
            )
            run = SimulationRepository(session).create(run)

        result = self.computation_engine.run_simulation(run, params)
        charts = self.chart_builder.plot_from_result(result)

        template = ReportTemplate(
            title=f"Отчёт по проекту #{project_id}",
            sections=ReportTemplate.default_sections(),
        )
        report_path = self.report_generator.generate(template, params, result)

        return result, charts + [report_path]

    def get_last_result(self, simulation_id: int) -> ModelResult | None:
        with get_session() as session:
            return ResultRepository(session).get_by_simulation(simulation_id)
