#!/usr/bin/env python3
"""Инициализация БД и демонстрационных данных."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eldial.core.config import get_config
from eldial.core.constants import ProcessType, TransportModel
from eldial.domain.entities import Project, User
from eldial.modules.storage.database import get_database_manager, get_session
from eldial.modules.storage.repository import ProjectRepository, UserRepository


def main() -> None:
    config = get_config()
    config.ensure_directories()
    db = get_database_manager()
    db.create_tables()

    with get_session() as session:
        user_repo = UserRepository(session)
        user = user_repo.get_by_login("demo")
        if not user:
            user = user_repo.create(
                User(id=None, login="demo", password_hash="hash", full_name="Иванов И.А.")
            )
        project_repo = ProjectRepository(session)
        projects = project_repo.list_by_user(user.id)
        if not projects:
            project_repo.create(
                Project(
                    id=None,
                    user_id=user.id,
                    name="Электродиализ NaCl — опытный стенд №3",
                    description="Демонстрационный проект",
                    process_type=ProcessType.ELECTRODIALYSIS,
                    transport_model=TransportModel.NERNST_PLANCK,
                )
            )
    print("БД инициализирована:", config.sqlite_path if config.use_sqlite_fallback else config.database_url)


if __name__ == "__main__":
    main()
