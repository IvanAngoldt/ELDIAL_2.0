"""Экспорт графиков и таблиц."""

from pathlib import Path

import pandas as pd

from eldial.core.config import get_config


class ChartExporter:
    def export_csv(self, df: pd.DataFrame, filename: str) -> Path:
        config = get_config()
        path = config.exports_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path
