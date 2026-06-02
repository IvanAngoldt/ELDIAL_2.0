"""
Модуль формирования отчётов.

Алгоритм: извлечение параметров и результатов → таблицы и графики → документ PDF/DOCX.
"""

import logging
from datetime import datetime
from pathlib import Path

from eldial.core.config import get_config
from eldial.domain.entities import ModelResult, SimulationParameters
from eldial.modules.reporting.templates import ReportTemplate
from eldial.modules.visualization.charts import ChartBuilder

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Генератор отчётной документации."""

    def __init__(self):
        self.config = get_config()
        self.config.ensure_directories()

    def generate(
        self,
        template: ReportTemplate,
        parameters: SimulationParameters,
        result: ModelResult,
        output_format: str = "txt",
    ) -> Path:
        simulation_data = {
            "project_name": f"Проект #{parameters.project_id}",
            "parameters": parameters.to_dict(),
            "results": {
                "Степень деминерализации": f"{result.demineralization_degree_pct} %",
                "Удельная энергия": f"{result.specific_energy_kwh_m3} кВт·ч/м³",
                "Токовая эффективность": f"{result.current_efficiency_pct} %",
            },
        }
        body = template.render_text_body(simulation_data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_format == "pdf":
            return self._write_pdf(template.title, body, timestamp)
        path = self.config.reports_dir / f"report_{timestamp}.txt"
        path.write_text(body, encoding="utf-8")
        return path

    def generate_demo_report(self, title: str, sections: list[str]) -> Path:
        template = ReportTemplate(title=title, sections=sections)
        simulation_data = {
            "project_name": "Электродиализ NaCl — стенд №3",
            "parameters": {
                "Напряжение": "12.0 В",
                "Концентрация NaCl": "5.0 г/л",
                "Число пар мембран": "20",
            },
            "results": {
                "Деминерализация": "87.3 %",
                "Энергопотребление": "2.14 кВт·ч/м³",
            },
        }
        body = template.render_text_body(simulation_data)
        path = self.config.reports_dir / f"report_demo_{datetime.now():%Y%m%d}.txt"
        path.write_text(body, encoding="utf-8")
        logger.info("Отчёт сохранён: %s", path)
        return path

    def _write_pdf(self, title: str, body: str, timestamp: str) -> Path:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            path = self.config.reports_dir / f"report_{timestamp}.pdf"
            c = canvas.Canvas(str(path), pagesize=A4)
            c.setFont("Helvetica", 14)
            c.drawString(50, 800, title[:60])
            c.setFont("Helvetica", 9)
            y = 760
            for line in body.split("\n")[:80]:
                c.drawString(50, y, line[:90])
                y -= 12
                if y < 50:
                    c.showPage()
                    y = 800
            c.save()
            return path
        except ImportError:
            path = self.config.reports_dir / f"report_{timestamp}.txt"
            path.write_text(body, encoding="utf-8")
            return path

    def attach_charts(self, result: ModelResult, report_dir: Path) -> list[Path]:
        builder = ChartBuilder()
        return builder.plot_from_result(result)
