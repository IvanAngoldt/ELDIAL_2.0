"""Конфигурация приложения."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Настройки программной системы ElDial."""

    model_config = SettingsConfigDict(
        env_prefix="ELDIAL_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "ElDial"
    app_version: str = "1.0.0"
    debug: bool = False

    # База данных
    database_url: str = Field(
        default="postgresql://eldial:eldial@localhost:5432/eldial_db",
        description="URL подключения PostgreSQL",
    )
    database_echo: bool = False
    use_sqlite_fallback: bool = True
    sqlite_path: str = "data/eldial.sqlite3"

    # Вычисления
    max_iterations: int = 5000
    convergence_tolerance: float = 1e-6
    default_grid_nodes: int = 100

    # Пути
    base_dir: Path = Path(__file__).resolve().parents[2]
    reports_dir: Path = Field(default_factory=lambda: Path("reports/output"))
    exports_dir: Path = Field(default_factory=lambda: Path("data/exports"))
    logs_dir: Path = Field(default_factory=lambda: Path("logs"))

    def ensure_directories(self) -> None:
        """Создать рабочие каталоги при отсутствии."""
        for path in (self.reports_dir, self.exports_dir, self.logs_dir, Path("data")):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()
