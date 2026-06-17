"""ELDIAL — реконструкция программы электродиализного обессоливания на Python.

Пакет содержит:
  * :mod:`eldial.params`   — параметры модели, чтение/запись формата ``Eldial.DAT``;
  * :mod:`eldial.model`    — расчётное ядро (маршевое интегрирование PDE по длине канала);
  * :mod:`eldial.services` — сервисные расчёты (пересчёт Y↔длина, производительность, предельный ток);
  * :mod:`eldial.report`   — форматирование таблиц и отчётов в стиле оригинала ELDIAL;
  * :mod:`eldial.cli`      — интерактивное консольное меню.

Физическая модель и обозначения описаны в «Базе знаний по ELDIAL» (разделы 3, 5, 10).
"""
from .params import Params, DEFAULT_PARAMS, read_dat, write_dat
from .model import Engine, velocity_profile

__all__ = [
    "Params",
    "DEFAULT_PARAMS",
    "read_dat",
    "write_dat",
    "Engine",
    "velocity_profile",
]

__version__ = "1.0.0"
