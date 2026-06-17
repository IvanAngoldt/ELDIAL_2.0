"""Приёмочные тесты: воспроизведение эталонного прогона ELDIAL (раздел 7 базы знаний).

Эталон: tp=0.4, tn=0.6, Tpc=Tna=0.98, cb=1, cd0=0.01, rac=3.66, parys=0,
        dpsi=80, ymax=0.04, tau=0.0005.
Контрольная величина — cdav (главный результат), допуск ~1.5 %.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from eldial import Engine, Params, read_dat  # noqa: E402
from eldial.model import velocity_profile, C_FLOOR  # noqa: E402
from eldial import services  # noqa: E402


def golden_params():
    return Params(tp=0.4, tn=0.6, Tpc=0.98, Tna=0.98, cb=1.0, cd0=0.01,
                  rac=3.66, parys=0.0, dpsi=80.0, ymin=0.0, ymax=0.04, tau=0.0005)


def task1_params(dpsi):
    """Параметры ЗАДАЧИ 1 (методичка): cb=cd0=1, rac=3.66, парабола."""
    return Params(tp=0.4, tn=0.6, Tpc=0.98, Tna=0.98, cb=1.0, cd0=1.0,
                  rac=3.66, parys=0.0, dpsi=dpsi, ymin=0.0, ymax=0.6, tau=2.5e-4)


def test_initial_current():
    """Входной ток (C≡1): I = dpsi/[2·tp·tn·(rac + 1 + 1/cb)] = 29.45."""
    eng = Engine(golden_params())
    assert eng.initial_current() == pytest.approx(29.45, abs=0.05)


@pytest.mark.parametrize("Y, cdav_ref", [
    (0.0005, 0.9870),
    (0.0400, 0.7316),
])
def test_cdav_golden(Y, cdav_ref):
    """cdav в контрольных точках должна совпадать с эталоном в пределах ~1.5 %."""
    layers = Engine(golden_params(), N=200).run()
    L = min(layers, key=lambda L: abs(L.Y - Y))
    assert L.cdav == pytest.approx(cdav_ref, rel=0.015)


def test_velocity_profile_parabolic():
    """parys=0 → параболический профиль 6X(1−X), среднее = 1."""
    X = [i / 100 for i in range(101)]
    V = velocity_profile(X, 0.0)
    assert V[0] == 0.0 and V[-1] == 0.0
    assert V[50] == pytest.approx(1.5)  # 6·0.5·0.5
    mean = sum((V[i] + V[i + 1]) * 0.5 * 0.01 for i in range(100))
    assert mean == pytest.approx(1.0, abs=1e-3)


def test_wall_depletion_asymmetry():
    """Сторона X=1 (КОМ) обедняется сильнее, чем X=0 (АОМ): T1k−t1 > T2a−t2."""
    layers = Engine(golden_params()).run()
    last = layers[-1]
    assert last.C11[-1] < last.C11[0]


def test_read_dat_roundtrip(tmp_path):
    """Чтение Eldial.DAT восстанавливает эталонные параметры."""
    dat = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Eldial_golden.DAT")
    p = read_dat(dat)
    assert p.dpsi == pytest.approx(80.0)
    assert p.cd0 == pytest.approx(0.01)
    assert p.tau == pytest.approx(0.0005)


def test_services_roundtrip():
    """Пересчёт Y↔длина обратим."""
    y = services.Y_to_length(0.15, v_mean=2.56, h=0.05)
    Y = services.length_to_Y(y, v_mean=2.56, h=0.05)
    assert Y == pytest.approx(0.15)


def test_find_Y_monotone():
    """Подбор Y под степень обессоливания возвращает значение внутри интервала."""
    p = golden_params()
    p.ymax = 0.04
    Yt, layers = services.find_Y_for_desalination(p, 0.20)
    assert Yt is not None and 0.0 < Yt <= p.ymax


# ----------------------- регрессия: корректность расчёта C(X) в сечениях -----------------------
def test_wall_never_negative_or_zero():
    """Пристеночная концентрация никогда не уходит в ноль/минус: пол = C_FLOOR.

    В предельном режиме модель ELDIAL ограничивает концентрацию снизу (≈0.0001),
    а не зануляет её — иначе нарушается электронейтральность раствора.
    """
    layers = Engine(task1_params(60.0), N=200).run()
    for L in layers:
        assert min(L.C) >= C_FLOOR - 1e-12
        assert L.C11[0] > 0.0 and L.C11[-1] > 0.0


def test_wall_concentration_monotone():
    """Пристеночные концентрации монотонно убывают вдоль канала (без скачков вверх).

    Прежняя реализация давала немонотонное поведение (резкое падение до 0, затем
    рост), что накапливало ошибку. После исправления C(0) и C(1) не возрастают.
    """
    layers = Engine(task1_params(60.0), N=200).run()
    tol = 1e-6
    for prev, cur in zip(layers, layers[1:]):
        assert cur.C11[0] <= prev.C11[0] + tol      # АОМ (X=0)
        assert cur.C11[-1] <= prev.C11[-1] + tol     # КОМ (X=1)


def test_current_monotone_no_collapse():
    """Плотность тока убывает плавно, без нефизичного обвала (≈вдвое за шаг)."""
    layers = Engine(task1_params(60.0), N=200).run()
    for prev, cur in zip(layers, layers[1:]):
        assert cur.i <= prev.i + 1e-6                # ток не возрастает (после входа)
        assert cur.i >= 0.45 * prev.i                # и не обрушивается скачком


@pytest.mark.parametrize("dpsi", [40.0, 60.0, 80.0, 100.0])
def test_task1_limiting_plateau(dpsi):
    """ЗАДАЧА 1: при dpsi≥40 безразмерная длина выходит на полку Y≈0.15."""
    Yt, _ = services.find_Y_for_desalination(task1_params(dpsi), 0.6, N=200)
    assert Yt == pytest.approx(0.15, abs=0.01)


def test_task1_ohmic_low_dpsi():
    """ЗАДАЧА 1, омический режим (dpsi=10, ниже предельного тока): Y≈0.25.

    Воспроизводится только с учётом ЭДС концентрационной поляризации (EMF_COEF).
    """
    Yt, _ = services.find_Y_for_desalination(task1_params(10.0), 0.6, N=200)
    assert Yt == pytest.approx(0.25, abs=0.012)


@pytest.mark.parametrize("dpsi, Yref", [(10.0, 0.41), (20.0, 0.30), (30.0, 0.29)])
def test_task3_cross_validation(dpsi, Yref):
    """ЗАДАЧА 3 (80%, cdav=0.2): независимая проверка калибровки ЭДС по dpsi=10/20/30."""
    p = task1_params(dpsi)
    Yt, _ = services.find_Y_for_desalination(p, 0.8, N=200)
    assert Yt == pytest.approx(Yref, abs=0.015)


def test_emf_zero_at_inlet():
    """ЭДС поляризации равна нулю на входе (C ≡ 1) — входной ток чисто омический."""
    eng = Engine(task1_params(60.0))
    assert eng.emf([1.0] * (eng.N + 1)) == pytest.approx(0.0, abs=1e-12)


def test_task2_reference():
    """ЗАДАЧА 2: cd0=0.01, dpsi=60, степень 50% → Y≈0.109 (методичка)."""
    p = Params(tp=0.4, tn=0.6, Tpc=0.98, Tna=0.98, cb=1.0, cd0=0.01,
               rac=3.66, parys=0.0, dpsi=60.0, ymin=0.0, ymax=0.15, tau=1e-4)
    Yt, _ = services.find_Y_for_desalination(p, 0.5, N=200)
    assert Yt == pytest.approx(0.109, abs=0.005)


def test_task6_profile():
    """ЗАДАЧА 6: профиль C(X) при dpsi=100, Tpc=Tna=0.95, Y≈0.08; пол у КОМ = 0.0001."""
    p = Params(tp=0.4, tn=0.6, Tpc=0.95, Tna=0.95, cb=1.0, cd0=1.0,
               rac=3.66, parys=0.0, dpsi=100.0, ymin=0.0, ymax=0.09, tau=1e-4)
    layers = Engine(p, N=200).run()
    L = min(layers, key=lambda L: abs(L.Y - 0.08))
    assert L.cdav == pytest.approx(0.5961, rel=0.02)
    assert L.C11[-1] == pytest.approx(C_FLOOR, abs=1e-9)   # КОМ на полу 0.0001
    ref = [0.342, 0.4675, 0.5839, 0.6766, 0.7292,
           0.7286, 0.6683, 0.5506, 0.3876, 0.1982, 0.0001]
    for got, exp in zip(L.C11, ref):
        assert got == pytest.approx(exp, abs=0.02)
