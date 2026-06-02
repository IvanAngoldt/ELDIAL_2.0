from eldial.domain.entities import SimulationParameters
from eldial.modules.math_model.electromembrane import ElectromembraneModel
from eldial.modules.math_model.nernst_planck import NernstPlanckSolver


def test_nernst_planck_solver_convergence():
    params = SimulationParameters(project_id=1, max_iterations=200)
    solver = NernstPlanckSolver(params)
    profile, iterations = solver.solve_steady_state(max_iter=200)
    assert len(profile) == params.grid_nodes
    assert iterations > 0


def test_electromembrane_transient():
    params = SimulationParameters(project_id=1, simulation_time_s=600, time_step_s=10)
    model = ElectromembraneModel(params)
    series, metrics = model.run_transient_simulation()
    assert len(series) > 0
    assert 0 < metrics.demineralization_degree_pct <= 100
    assert metrics.current_efficiency_pct > 0
