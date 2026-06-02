"""Константы и перечисления системы ElDial."""

from enum import Enum


class ProcessType(str, Enum):
    """Тип электромембранного процесса."""

    ELECTRODIALYSIS = "ED"
    ELECTRODIALYSIS_REVERSIBLE = "EDR"
    ELECTRO_ELECTRODIALYSIS = "EED"
    DIFFUSION_DIALYSIS = "DD"
    ELECTROCHEMICAL_RECOVERY = "ECR"


class TransportModel(str, Enum):
    """Математическая модель переноса."""

    NERNST_PLANCK = "nernst_planck"
    PEETERS = "peeters"
    MULTI_ION = "multi_ion"


class SimulationStatus(str, Enum):
    """Статус вычислительного эксперимента."""

    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFormat(str, Enum):
    """Формат экспорта отчёта."""

    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"


# Физические константы (СИ)
FARADAY_CONSTANT = 96485.33212  # Кл/моль
GAS_CONSTANT = 8.314462618  # Дж/(моль·К)
WATER_DENSITY = 1000.0  # кг/м³

# Пределы валидации параметров
MIN_VOLTAGE = 0.1
MAX_VOLTAGE = 48.0
MIN_TEMPERATURE = 5.0
MAX_TEMPERATURE = 80.0
MIN_CONCENTRATION = 0.01
MAX_CONCENTRATION = 200.0
MIN_MEMBRANE_PAIRS = 1
MAX_MEMBRANE_PAIRS = 500

DEFAULT_TIME_STEP = 0.5  # с
DEFAULT_SIMULATION_TIME = 7200.0  # с (120 мин)
