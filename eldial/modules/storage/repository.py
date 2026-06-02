"""Репозитории доступа к данным."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from eldial.core.constants import SimulationStatus
from eldial.core.exceptions import StorageError
from eldial.domain.entities import ModelResult, Project, SimulationRun, User
from eldial.modules.storage.models import ModelResultORM, ProjectORM, SimulationORM, UserORM


class UserRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, user: User) -> User:
        orm = UserORM(
            login=user.login,
            password_hash=user.password_hash,
            full_name=user.full_name,
            organization=user.organization,
        )
        self._session.add(orm)
        self._session.flush()
        user.id = orm.id
        return user

    def get_by_login(self, login: str) -> User | None:
        stmt = select(UserORM).where(UserORM.login == login)
        row = self._session.scalar(stmt)
        if not row:
            return None
        return User(
            id=row.id,
            login=row.login,
            password_hash=row.password_hash,
            full_name=row.full_name or "",
            organization=row.organization or "",
            created_at=row.created_at,
        )


class ProjectRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, project: Project) -> Project:
        orm = ProjectORM(
            user_id=project.user_id,
            name=project.name,
            description=project.description,
            process_type=project.process_type.value,
            transport_model=project.transport_model.value,
        )
        self._session.add(orm)
        self._session.flush()
        project.id = orm.id
        return project

    def list_by_user(self, user_id: int) -> list[Project]:
        stmt = select(ProjectORM).where(ProjectORM.user_id == user_id)
        rows = self._session.scalars(stmt).all()
        return [
            Project(
                id=r.id,
                user_id=r.user_id,
                name=r.name,
                description=r.description or "",
                created_at=r.created_at,
            )
            for r in rows
        ]

    def get_by_id(self, project_id: int) -> Project | None:
        row = self._session.get(ProjectORM, project_id)
        if not row:
            return None
        return Project(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            description=row.description or "",
        )


class SimulationRepository:
    def __init__(self, session: Session):
        self._session = session

    def create(self, run: SimulationRun) -> SimulationRun:
        orm = SimulationORM(
            project_id=run.project_id,
            status=run.status.value,
        )
        self._session.add(orm)
        self._session.flush()
        run.id = orm.id
        return run

    def update_status(
        self,
        simulation_id: int,
        status: SimulationStatus,
        error_message: str | None = None,
    ) -> None:
        orm = self._session.get(SimulationORM, simulation_id)
        if not orm:
            raise StorageError(f"Симуляция {simulation_id} не найдена", operation="update")
        orm.status = status.value
        if status == SimulationStatus.RUNNING:
            orm.started_at = datetime.utcnow()
        if status in (SimulationStatus.COMPLETED, SimulationStatus.FAILED):
            orm.finished_at = datetime.utcnow()
        if error_message:
            orm.error_message = error_message


class ResultRepository:
    def __init__(self, session: Session):
        self._session = session

    def save(self, result: ModelResult) -> ModelResult:
        orm = ModelResultORM(
            simulation_id=result.simulation_id,
            demineralization_degree_pct=result.demineralization_degree_pct,
            specific_energy_kwh_m3=result.specific_energy_kwh_m3,
            current_efficiency_pct=result.current_efficiency_pct,
            average_current_a=result.average_current_a,
            result_json={
                "time_series": [
                    {
                        "time_min": p.time_min,
                        "c_dil": p.diluate_concentration_g_l,
                        "c_conc": p.concentrate_concentration_g_l,
                        "current": p.current_a,
                        "voltage": p.voltage_v,
                        "power": p.power_w,
                    }
                    for p in result.time_series
                ]
            },
        )
        self._session.add(orm)
        self._session.flush()
        result.id = orm.id
        return result

    def get_by_simulation(self, simulation_id: int) -> ModelResult | None:
        stmt = select(ModelResultORM).where(ModelResultORM.simulation_id == simulation_id)
        row = self._session.scalar(stmt)
        if not row:
            return None
        return ModelResult(
            id=row.id,
            simulation_id=row.simulation_id,
            demineralization_degree_pct=row.demineralization_degree_pct or 0.0,
            specific_energy_kwh_m3=row.specific_energy_kwh_m3 or 0.0,
            current_efficiency_pct=row.current_efficiency_pct or 0.0,
            average_current_a=row.average_current_a or 0.0,
            created_at=row.created_at,
        )
