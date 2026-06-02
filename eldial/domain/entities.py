"""
Доменные сущности программной системы.

Соответствуют логической модели данных (users, projects, simulations, model_results).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from eldial.core.constants import ProcessType, SimulationStatus, TransportModel


@dataclass
class User:
    id: int | None
    login: str
    password_hash: str
    full_name: str = ""
    organization: str = ""
    created_at: datetime | None = None


@dataclass
class Project:
    id: int | None
    user_id: int
    name: str
    description: str = ""
    process_type: ProcessType = ProcessType.ELECTRODIALYSIS
    transport_model: TransportModel = TransportModel.NERNST_PLANCK
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class MembraneProperties:
    """Характеристики мембранного стека."""

    membrane_pairs: int = 20
    effective_area_m2: float = 0.32
    channel_thickness_mm: float = 0.75
    channel_length_m: float = 0.48
    cation_transfer_number: float = 0.92
    anion_transfer_number: float = 0.04
    membrane_resistivity_ohm_m: float = 3.5
    diffusion_coefficient_m2_s: float = 1.2e-9


@dataclass
class SolutionProperties:
    """Свойства раствора."""

    nacl_concentration_g_l: float = 5.0
    ca_concentration_g_l: float = 0.12
    mg_concentration_g_l: float = 0.08
    ph: float = 7.2
    temperature_c: float = 25.0
    density_kg_m3: float = 1020.0
    viscosity_mpa_s: float = 1.02
    ionic_strength_mol_l: float = 0.085


@dataclass
class SimulationParameters:
    """Полный набор параметров вычислительного эксперимента."""

    project_id: int
    membrane: MembraneProperties = field(default_factory=MembraneProperties)
    solution: SolutionProperties = field(default_factory=SolutionProperties)
    voltage_v: float = 12.0
    volumetric_flow_l_min: float = 2.5
    simulation_time_s: float = 7200.0
    time_step_s: float = 0.5
    grid_nodes: int = 100
    integration_method: str = "crank_nicolson"
    convergence_tolerance: float = 1e-6
    max_iterations: int = 5000
    boundary_condition: str = "constant_voltage"
    initial_diluate_concentration_g_l: float = 5.0
    initial_concentrate_concentration_g_l: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "voltage_v": self.voltage_v,
            "temperature_c": self.solution.temperature_c,
            "concentration_g_l": self.solution.nacl_concentration_g_l,
            "membrane_pairs": self.membrane.membrane_pairs,
            "simulation_time_s": self.simulation_time_s,
            "time_step_s": self.time_step_s,
        }


@dataclass
class SimulationRun:
    id: int | None
    project_id: int
    parameters: SimulationParameters
    status: SimulationStatus = SimulationStatus.DRAFT
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


@dataclass
class TimeSeriesPoint:
    time_min: float
    diluate_concentration_g_l: float
    concentrate_concentration_g_l: float
    current_a: float
    voltage_v: float
    power_w: float
    current_density_a_m2: float = 0.0
    demineralization_degree_pct: float = 0.0


@dataclass
class ModelResult:
    """Результаты моделирования (таблица model_results)."""

    id: int | None
    simulation_id: int
    demineralization_degree_pct: float
    specific_energy_kwh_m3: float
    current_efficiency_pct: float
    average_current_a: float
    time_series: list[TimeSeriesPoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
