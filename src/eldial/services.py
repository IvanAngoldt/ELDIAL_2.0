"""Сервисные расчёты для проектных задач ELDIAL (пересчёт безразмерных величин в физические).

Формулы — раздел 3.7–3.8 «Базы знаний». Коэффициент диффузии D по умолчанию
взят для NaCl (≈1.6·10⁻⁵ см²/с).
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from .model import Engine, Layer, F_FARADAY
from .params import Params

D_NACL = 1.6e-5  # см²/с — эффективный коэффициент диффузии NaCl


# ------------------------------- пересчёт Y ↔ длина -------------------------------
def Y_to_length(Y: float, v_mean: float, h: float, D: float = D_NACL) -> float:
    """Физическая длина канала y [см] из безразмерной Y:  y = Y·v̄·h²/D."""
    return Y * v_mean * h ** 2 / D


def length_to_Y(y: float, v_mean: float, h: float, D: float = D_NACL) -> float:
    """Безразмерная длина Y из физической длины y [см]."""
    return y * D / (v_mean * h ** 2)


def velocity_for_length(Y: float, y: float, h: float, D: float = D_NACL) -> float:
    """Средняя скорость v̄ [см/с], при которой на длине y достигается Y."""
    return D * y / (Y * h ** 2)


# ----------------------------- производительность аппарата -----------------------------
def production_lph(v_mean: float, h: float, width: float, n_pairs: float) -> float:
    """Производительность W [л/ч] = v̄·h·a·n_пар·3600/1000 (h, a в см; v̄ в см/с)."""
    return v_mean * h * width * n_pairs * 3.6


def n_pairs_for_production(W_lph: float, v_mean: float, h: float, width: float) -> float:
    """Число парных камер для заданной производительности W [л/ч]."""
    return W_lph / (v_mean * h * width * 3.6)


# --------------------------------- степень обессоливания ---------------------------------
def desalination_degree(cdav: float, cd0_norm: float = 1.0) -> float:
    """Степень обессоливания α = 1 − cdav/cd0 (cdav — нормированная концентрация)."""
    return 1.0 - cdav / cd0_norm


# --------------------------------- предельный ток ---------------------------------
def leveque_ilim_av(delta_T_max: float, Y: float) -> float:
    """Средняя предельная плотность тока по Левеку (ур. 5.49), применимо при Y<0.05."""
    return 1.43 / delta_T_max * Y ** (-1.0 / 3.0)


def peers_ilim(D: float, c0: float, delta: float, T1: float, t1: float) -> float:
    """Предельная плотность тока по Пирсу (ур. 7.43), А/см². c0 [моль/см³], delta [см]."""
    return F_FARADAY * D * c0 / (delta * (T1 - t1))


def current_to_physical(I: float, cd0: float, h: float, D: float = D_NACL) -> float:
    """Физическая плотность тока i [А/см²] из безразмерной I (ур. 5.38). cd0 [моль/см³]."""
    return I * F_FARADAY * D * cd0 / h


# --------------------------- автоподбор Y под целевую степень ---------------------------
def find_Y_for_desalination(
    params: Params,
    degree: float,
    N: int = 200,
    on_step: Optional[Callable[[Layer], None]] = None,
) -> Tuple[Optional[float], List[Layer]]:
    """Найти безразмерную длину Y, при которой достигается заданная степень обессоливания.

    ``degree`` — доля (0.6 = 60 %). Возвращает (Y или None, список слоёв).
    Расчёт потоковый: останавливается, как только цель достигнута. ``on_step`` (если
    задан) вызывается для каждого посчитанного слоя — удобно для индикатора прогресса.
    """
    target = 1.0 - degree
    layers: List[Layer] = []
    prev: Optional[Layer] = None
    for L in Engine(params, N=N).march():
        layers.append(L)
        if on_step is not None:
            on_step(L)
        if L.cdav <= target:                       # цель достигнута на этом слое
            if prev is None:
                return L.Y, layers
            # линейная интерполяция между предыдущим и текущим слоем
            Yt = prev.Y + (target - prev.cdav) * (L.Y - prev.Y) / (L.cdav - prev.cdav)
            return Yt, layers
        prev = L
    return None, layers                            # не достигнута на интервале [0, ymax]
