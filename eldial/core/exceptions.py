"""Исключения программной системы ElDial."""


class EldialError(Exception):
    """Базовое исключение системы."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code or "ELDIAL_ERROR"
        super().__init__(message)


class ValidationError(EldialError):
    """Ошибка валидации входных параметров."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR")


class StorageError(EldialError):
    """Ошибка работы с хранилищем данных."""

    def __init__(self, message: str, operation: str | None = None):
        self.operation = operation
        super().__init__(message, code="STORAGE_ERROR")


class ComputationError(EldialError):
    """Ошибка численного расчёта."""

    def __init__(self, message: str, iteration: int | None = None):
        self.iteration = iteration
        super().__init__(message, code="COMPUTATION_ERROR")


class ModelError(EldialError):
    """Ошибка математической модели."""

    def __init__(self, message: str):
        super().__init__(message, code="MODEL_ERROR")


class ReportGenerationError(EldialError):
    """Ошибка формирования отчёта."""

    def __init__(self, message: str):
        super().__init__(message, code="REPORT_ERROR")
