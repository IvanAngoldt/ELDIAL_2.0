"""
Точка сборки приложения ElDial.

Инициализация конфигурации, БД, логирования, запуск GUI.
"""

import argparse

from eldial.core.config import get_config
from eldial.modules.storage.database import get_database_manager
from eldial.utils.logging_setup import setup_logging


def bootstrap() -> None:
    config = get_config()
    config.ensure_directories()
    setup_logging()
    db = get_database_manager()
    db.create_tables()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="ElDial — моделирование электромембранных процессов",
    )
    parser.add_argument("--init-db", action="store_true", help="Создать таблицы БД")
    parser.add_argument("--demo", action="store_true", help="Запустить демо-расчёт в консоли")
    parser.add_argument("--web", action="store_true", help="Открыть веб-mock интерфейс")
    args = parser.parse_args(argv)

    bootstrap()

    if args.init_db:
        print("База данных инициализирована.")
        return

    if args.demo:
        _run_demo()
        return

    if args.web:
        import subprocess
        import sys
        from pathlib import Path
        mock_main = Path(__file__).parents[1] / "main.py"
        subprocess.run([sys.executable, str(mock_main)], check=False)
        return

    from eldial.modules.ui.application import EldialApplication
    EldialApplication().run()


def _run_demo() -> None:
    from eldial.core.constants import SimulationStatus
    from eldial.domain.entities import SimulationParameters, SimulationRun
    from eldial.modules.computation.engine import ComputationEngine
    from eldial.modules.parameters.forms import ParameterFormData
    from eldial.modules.parameters.service import ParameterInputService
    from eldial.modules.storage.database import get_session
    from eldial.modules.storage.repository import (
        ProjectRepository,
        SimulationRepository,
        UserRepository,
    )

    import subprocess
    import sys
    from pathlib import Path

    init_script = Path(__file__).resolve().parents[1] / "scripts" / "init_db.py"
    subprocess.run([sys.executable, str(init_script)], check=False)

    service = ParameterInputService()

    with get_session() as session:
        user = UserRepository(session).get_by_login("demo")
        if not user:
            print("Ошибка: выполните python3 scripts/init_db.py")
            return
        projects = ProjectRepository(session).list_by_user(user.id)
        project_id = projects[0].id if projects else 1
        params = service.parse_form(ParameterFormData(), project_id=project_id)
        run = SimulationRun(
            id=None,
            project_id=project_id,
            parameters=params,
            status=SimulationStatus.QUEUED,
        )
        run = SimulationRepository(session).create(run)

    result = ComputationEngine().run_simulation(run, params)
    print("=== Результаты моделирования ===")
    print(f"Деминерализация: {result.demineralization_degree_pct} %")
    print(f"Токовая эффективность: {result.current_efficiency_pct} %")
    print(f"Удельная энергия: {result.specific_energy_kwh_m3} кВт·ч/м³")
    print(f"Точек временного ряда: {len(result.time_series)}")


if __name__ == "__main__":
    main()
