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
from eldial.model import velocity_profile  # noqa: E402
from eldial import services  # noqa: E402


def golden_params():
    return Params(tp=0.4, tn=0.6, Tpc=0.98, Tna=0.98, cb=1.0, cd0=0.01,
                  rac=3.66, parys=0.0, dpsi=80.0, ymin=0.0, ymax=0.04, tau=0.0005)


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
