"""
Сервис ввода и сохранения параметров моделирования.

Реализует алгоритм: ввод → валидация → сохранение в БД → передача вычислительному модулю.
"""

import json
from pathlib import Path

from eldial.domain.entities import (
    MembraneProperties,
    SimulationParameters,
    SolutionProperties,
)
from eldial.modules.parameters.forms import ParameterFormData
from eldial.modules.parameters.validator import ParameterValidator


class ParameterInputService:
    """Управление параметрами моделирования."""

    def __init__(self):
        self.validator = ParameterValidator()

    def parse_form(self, form: ParameterFormData, project_id: int) -> SimulationParameters:
        """Преобразование данных формы в доменную модель."""
        membrane = MembraneProperties(
            membrane_pairs=int(form.membrane_pairs),
            effective_area_m2=float(form.effective_area),
            channel_thickness_mm=float(form.channel_thickness),
            channel_length_m=float(form.channel_length),
            cation_transfer_number=float(form.cation_transfer),
            anion_transfer_number=float(form.anion_transfer),
            membrane_resistivity_ohm_m=float(form.membrane_resistivity),
            diffusion_coefficient_m2_s=float(form.diffusion_coeff),
        )
        solution = SolutionProperties(
            nacl_concentration_g_l=float(form.nacl_concentration),
            ca_concentration_g_l=float(form.ca_concentration),
            mg_concentration_g_l=float(form.mg_concentration),
            ph=float(form.ph),
            temperature_c=float(form.temperature),
            density_kg_m3=float(form.density),
            viscosity_mpa_s=float(form.viscosity),
            ionic_strength_mol_l=float(form.ionic_strength),
        )
        params = SimulationParameters(
            project_id=project_id,
            membrane=membrane,
            solution=solution,
            voltage_v=float(form.voltage),
            volumetric_flow_l_min=float(form.volumetric_flow),
            simulation_time_s=float(form.simulation_time_min) * 60,
            time_step_s=float(form.time_step),
            grid_nodes=int(form.grid_nodes),
            integration_method=form.integration_method,
            boundary_condition=form.boundary_condition,
            initial_diluate_concentration_g_l=float(form.initial_diluate),
            initial_concentrate_concentration_g_l=float(form.initial_concentrate),
        )
        self.validator.validate_or_raise(params)
        return params

    def save_to_file(self, params: SimulationParameters, path: Path) -> None:
        """Сохранение параметров в JSON (резервный режим без БД)."""
        data = {
            "project_id": params.project_id,
            "membrane": params.membrane.__dict__,
            "solution": params.solution.__dict__,
            "voltage_v": params.voltage_v,
            "simulation_time_s": params.simulation_time_s,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_from_file(self, path: Path, project_id: int) -> SimulationParameters:
        data = json.loads(path.read_text(encoding="utf-8"))
        form = ParameterFormData(
            membrane_pairs=str(data["membrane"]["membrane_pairs"]),
            effective_area=str(data["membrane"]["effective_area_m2"]),
            nacl_concentration=str(data["solution"]["nacl_concentration_g_l"]),
            voltage=str(data["voltage_v"]),
            simulation_time_min=str(data["simulation_time_s"] / 60),
        )
        return self.parse_form(form, project_id)
