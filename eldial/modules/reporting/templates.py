"""Шаблоны отчётной документации."""

from dataclasses import dataclass, field


@dataclass
class ReportTemplate:
    """Шаблон оформления отчёта (ГОСТ 7.32-2017)."""

    title: str
    author: str = "Иванов И.И."
    organization: str = "КубГУ, ФКТиПМ"
    format: str = "pdf"
    sections: list[str] = field(default_factory=list)

    @staticmethod
    def default_sections() -> list[str]:
        return [
            "Титульный лист",
            "Описание проекта и исходных данных",
            "Параметры моделирования",
            "Методика расчёта",
            "Графики концентраций и тока",
            "Сводные таблицы результатов",
            "Анализ энергопотребления",
            "Сравнение с экспериментальными данными",
            "Выводы и рекомендации",
        ]

    def render_text_body(self, simulation_data: dict) -> str:
        lines = [
            "=" * 63,
            "ОТЧЁТ О МОДЕЛИРОВАНИИ",
            "Электромембранный процесс электродиализа NaCl",
            "=" * 63,
            "",
            f"Наименование: {simulation_data.get('project_name', '—')}",
            f"Автор: {self.author}",
            f"Организация: {self.organization}",
            "",
        ]
        if "Параметры моделирования" in self.sections:
            lines.extend(["1. ПАРАМЕТРЫ МОДЕЛИРОВАНИЯ", "-" * 40])
            for k, v in simulation_data.get("parameters", {}).items():
                lines.append(f"   {k}: {v}")
            lines.append("")
        if "Результаты" in self.sections or any("результат" in s.lower() for s in self.sections):
            lines.extend(["2. РЕЗУЛЬТАТЫ", "-" * 40])
            for k, v in simulation_data.get("results", {}).items():
                lines.append(f"   {k}: {v}")
        return "\n".join(lines)
