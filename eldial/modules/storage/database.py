"""Управление подключением к СУБД."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from eldial.core.config import get_config
from eldial.core.exceptions import StorageError
from eldial.modules.storage.models import Base


class DatabaseManager:
    """Менеджер подключения к PostgreSQL / SQLite (резервный режим)."""

    def __init__(self, database_url: str | None = None):
        config = get_config()
        self._url = database_url or config.database_url
        self._engine = None
        self._session_factory = None
        self._init_engine()

    def _init_engine(self) -> None:
        config = get_config()
        try:
            self._engine = create_engine(
                self._url,
                echo=config.database_echo,
                pool_pre_ping=True,
            )
            self._engine.connect().close()
        except Exception:
            if config.use_sqlite_fallback:
                sqlite_url = f"sqlite:///{config.sqlite_path}"
                self._engine = create_engine(sqlite_url, echo=config.database_echo)
            else:
                raise StorageError(
                    "Не удалось подключиться к PostgreSQL",
                    operation="connect",
                )
        self._session_factory = sessionmaker(bind=self._engine)

    def create_tables(self) -> None:
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        if not self._session_factory:
            raise StorageError("Сессия не инициализирована", operation="session")
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            raise StorageError(str(exc), operation="transaction") from exc
        finally:
            session.close()


_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with get_database_manager().session() as session:
        yield session
