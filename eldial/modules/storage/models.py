"""ORM-модели SQLAlchemy (физическая модель данных)."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(128))
    organization: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    projects: Mapped[list["ProjectORM"]] = relationship(back_populates="user")


class ProjectORM(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    process_type: Mapped[str] = mapped_column(String(16), default="ED")
    transport_model: Mapped[str] = mapped_column(String(32), default="nernst_planck")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["UserORM"] = relationship(back_populates="projects")
    simulations: Mapped[list["SimulationORM"]] = relationship(back_populates="project")


class SimulationORM(Base):
    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["ProjectORM"] = relationship(back_populates="simulations")
    results: Mapped[list["ModelResultORM"]] = relationship(back_populates="simulation")


class ModelResultORM(Base):
    __tablename__ = "model_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    simulation_id: Mapped[int] = mapped_column(ForeignKey("simulations.id"), nullable=False)
    demineralization_degree_pct: Mapped[float | None] = mapped_column(Float)
    specific_energy_kwh_m3: Mapped[float | None] = mapped_column(Float)
    current_efficiency_pct: Mapped[float | None] = mapped_column(Float)
    average_current_a: Mapped[float | None] = mapped_column(Float)
    result_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)

    simulation: Mapped["SimulationORM"] = relationship(back_populates="results")
