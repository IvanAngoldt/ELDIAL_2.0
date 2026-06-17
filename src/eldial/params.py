"""Параметры модели ELDIAL и ввод/вывод файла данных ``Eldial.DAT``.

Формат файла (свободный, Fortran list-directed): в каждой значащей строке первое
поле — числовое значение, остальное — имя параметра/комментарий. Порядок строго
фиксирован (см. «База знаний», раздел 6).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields, asdict
from typing import List


# Порядок параметров в файле Eldial.DAT (раздел 6 базы знаний).
PARAM_ORDER: List[str] = [
    "tp", "tn", "Tpc", "Tna", "zp", "zn", "cb", "cd0", "rac", "g", "parys",
    "dpsi", "ymin", "ymax", "tau", "epsac", "l", "np", "lkr", "kprint", "nprint",
]

# Параметры, которые хранятся как целые числа.
INT_PARAMS = {"l", "np", "lkr", "kprint", "nprint"}


def fnum(x: float) -> str:
    """Число в обычном десятичном виде: без экспоненты (e-…), без лишних нулей.

    Примеры: 0.0001 вместо 1e-04, 60 вместо 60.0, 3.66 как есть.
    """
    if x == int(x):
        return str(int(x))
    return f"{x:.10f}".rstrip("0").rstrip(".")

# Человеко-читаемые описания (используются в меню и при печати исходных данных).
DESCRIPTIONS = {
    "tp":     "число переноса катиона в растворе",
    "tn":     "число переноса аниона в растворе",
    "Tpc":    "эфф. число переноса катиона в КОМ",
    "Tna":    "эфф. число переноса аниона в АОМ",
    "zp":     "зарядовое число катиона",
    "zn":     "зарядовое число аниона",
    "cb":     "концентрация в камере концентрирования",
    "cd0":    "начальная концентрация в камере обессоливания (= c0)",
    "rac":    "отношение сопротивлений мембран/раствора",
    "g":      "пористость сепаратора",
    "parys":  "наполнение профиля скорости (0 — парабола, >40 — ступенчатый)",
    "dpsi":   "скачок потенциала на парной камере (управляющий)",
    "ymin":   "начало печати по Y",
    "ymax":   "конец расчёта по Y",
    "tau":    "шаг по длине (рекоменд. 1e-6 … 0.01)",
    "epsac":  "точность по плотности тока",
    "l":      "число доп. значений длины (udop)",
    "np":     "кратность печати слоёв",
    "lkr":    "режим шага: 0 — постоянный, 1 — адаптивный",
    "kprint": "режим печати: 1 — по слоям, 2 — по udop, 3 — всё",
    "nprint": "графические данные: 0 — нет, 1 — GRY, 2 — GRX, 3 — оба",
}


@dataclass
class Params:
    """Полный набор входных параметров расчёта ELDIAL."""

    # --- раствор и мембраны ---
    tp: float = 0.4
    tn: float = 0.6
    Tpc: float = 0.98
    Tna: float = 0.98
    zp: float = 1.0
    zn: float = -1.0
    cb: float = 1.0
    cd0: float = 1.0
    rac: float = 3.66
    # --- сепаратор ---
    g: float = 1.0
    parys: float = 0.0
    # --- канал ---
    dpsi: float = 60.0
    ymin: float = 0.0
    ymax: float = 0.15
    # --- численная схема ---
    tau: float = 1e-4
    epsac: float = 1e-4
    # --- управление выводом ---
    l: int = 1
    np: int = 1
    lkr: int = 0
    kprint: int = 3
    nprint: int = 3
    # --- доп. значения длины для вывода профилей C(x) ---
    udop: List[float] = field(default_factory=lambda: [0.04])

    def copy(self) -> "Params":
        d = asdict(self)
        d["udop"] = list(self.udop)
        return Params(**d)

    def set(self, name: str, raw: str) -> None:
        """Присвоить параметру значение из строки (с приведением типа)."""
        if name == "udop":
            self.udop = [float(t) for t in raw.replace(",", " ").split()]
        elif name in INT_PARAMS:
            setattr(self, name, int(round(float(raw))))
        else:
            setattr(self, name, float(raw))

    def validate(self) -> List[str]:
        """Вернуть список предупреждений о некорректных данных (пустой — всё ок)."""
        w: List[str] = []
        if not (0.0 < self.tp < 1.0) or abs(self.tp + self.tn - 1.0) > 1e-6:
            w.append("числа переноса tp, tn должны быть в (0,1) и давать tp+tn=1")
        if not (0.0 < self.Tpc <= 1.0) or not (0.0 < self.Tna <= 1.0):
            w.append("эфф. числа переноса Tpc, Tna должны быть в (0,1]")
        if self.cd0 <= 0 or self.cb <= 0:
            w.append("концентрации cd0 и cb должны быть положительны")
        if self.rac < 0:
            w.append("сопротивление rac не может быть отрицательным")
        if self.dpsi <= 0:
            w.append("скачок потенциала dpsi должен быть положителен")
        if self.ymax <= 0 or self.ymin < 0 or self.ymin >= self.ymax:
            w.append("длины Y должны удовлетворять 0 <= ymin < ymax")
        if not (1e-7 <= self.tau <= 0.05):
            w.append("шаг tau вне рекомендованного диапазона 1e-6 … 0.01")
        if self.epsac <= 0:
            w.append("точность epsac должна быть положительна")
        return w


# Параметры по умолчанию (эталонные значения из Eldial.DAT, раздел 6).
DEFAULT_PARAMS = Params()


def read_dat(path: str) -> Params:
    """Прочитать файл ``Eldial.DAT`` и вернуть :class:`Params`.

    Из каждой непустой строки берётся первый числовой токен; значения
    раскладываются по :data:`PARAM_ORDER`, остаток считается массивом ``udop``.
    """
    vals: List[float] = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tok = line.split()[0].replace("D", "E").replace("d", "e")
            try:
                vals.append(float(tok))
            except ValueError:
                continue

    p = Params()
    for i, name in enumerate(PARAM_ORDER):
        if i < len(vals):
            v = vals[i]
            setattr(p, name, int(round(v)) if name in INT_PARAMS else v)
    rest = vals[len(PARAM_ORDER):]
    p.udop = rest if rest else [0.04]
    return p


def write_dat(p: Params, path: str) -> None:
    """Сохранить параметры в формате ``Eldial.DAT`` (значение + имя + комментарий)."""
    lines = []
    for name in PARAM_ORDER:
        v = getattr(p, name)
        sval = f"{int(v)}" if name in INT_PARAMS else fnum(v)
        lines.append(f"  {sval:<12}{name:<8}{DESCRIPTIONS.get(name, '')}")
    for k, u in enumerate(p.udop, start=1):
        lines.append(f"  {fnum(u):<12}{f'udop({k})':<8}доп. значение длины")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def field_names() -> List[str]:
    """Список имён скалярных параметров (без ``udop``)."""
    return [f.name for f in fields(Params) if f.name != "udop"]
