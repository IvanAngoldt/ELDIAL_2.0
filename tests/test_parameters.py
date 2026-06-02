from eldial.modules.parameters.forms import ParameterFormData
from eldial.modules.parameters.service import ParameterInputService


def test_parse_form():
    service = ParameterInputService()
    form = ParameterFormData()
    params = service.parse_form(form, project_id=1)
    assert params.voltage_v == 12.0
    assert params.membrane.membrane_pairs == 20
