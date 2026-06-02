"""Структуры данных форм ввода параметров."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParameterFormData:
    """Данные формы ввода (соответствие экрану параметров)."""

    # Мембрана
    membrane_pairs: str = "20"
    effective_area: str = "0.32"
    channel_thickness: str = "0.75"
    channel_length: str = "0.48"
    cation_transfer: str = "0.92"
    anion_transfer: str = "0.04"
    membrane_resistivity: str = "3.5"
    diffusion_coeff: str = "1.2e-9"

    # Раствор
    nacl_concentration: str = "5.0"
    ca_concentration: str = "0.12"
    mg_concentration: str = "0.08"
    ph: str = "7.2"
    temperature: str = "25"
    density: str = "1020"
    viscosity: str = "1.02"
    ionic_strength: str = "0.085"

    # Процесс
    voltage: str = "12.0"
    volumetric_flow: str = "2.5"
    simulation_time_min: str = "120"
    time_step: str = "0.5"
    grid_nodes: str = "100"
    integration_method: str = "crank_nicolson"
    boundary_condition: str = "constant_voltage"
    initial_diluate: str = "5.0"
    initial_concentrate: str = "0.5"

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParameterFormData":
        return cls(**{k: str(v) for k, v in data.items() if k in cls.__dataclass_fields__})
