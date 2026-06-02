import pytest

from eldial.core.exceptions import ValidationError
from eldial.domain.entities import MembraneProperties, SimulationParameters, SolutionProperties
from eldial.modules.parameters.validator import ParameterValidator


def test_valid_parameters():
    v = ParameterValidator()
    params = SimulationParameters(project_id=1)
    assert v.validate_simulation(params) == []


def test_invalid_voltage():
    v = ParameterValidator()
    params = SimulationParameters(project_id=1, voltage_v=100.0)
    errors = v.validate_simulation(params)
    assert any("Напряжение" in e for e in errors)


def test_validate_or_raise():
    v = ParameterValidator()
    params = SimulationParameters(project_id=1, voltage_v=100.0)
    with pytest.raises(ValidationError):
        v.validate_or_raise(params)
