"""Расчётное ядро ELDIAL — маршевое интегрирование задачи конвективной электродиффузии.

Безразмерная модель (C=c/c0, X=x/h ∈ [0,1], Y=yD/(v̄h²)):

    V(X)·∂C/∂Y = ∂²C/∂X²
    ∂C/∂X|_{X=0} =  I·(Tna − tn)        (сторона анионообменной мембраны, АОМ)
    ∂C/∂X|_{X=1} = −I·(Tpc − tp)        (сторона катионообменной мембраны, КОМ)
    C(Y=0, X) = 1

Связь тока со скачком потенциала (омическая часть подтверждена входным током
i=29.45 в эталоне, см. «База знаний» §10.8):

    I = dpsi / [ 2·tp·tn·( rac + ∫₀¹ dX/C + 1/cb ) ]

Численно: неявный шаг по Y (backward Euler) + прогонка (метод Томаса) по X,
с итерационным согласованием тока I (точность epsac). Предельный режим
возникает естественно: при C→0 у стенки сопротивление →∞, ток выходит на «полку».
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator, List

from .params import Params

F_FARADAY = 96485.0  # Кл/моль — постоянная Фарадея (для пересчёта в физические величины)


def velocity_profile(X: List[float], parys: float) -> List[float]:
    """Безразмерный профиль скорости V(X), нормированный на среднее = 1.

    ``parys == 0``  → параболический (Пуазейль) ``6X(1−X)``;
    ``parys > 40``  → ступенчатый (плунжерный) профиль;
    ``0 < parys ≤ 40`` → «наполненный» профиль сепаратора.
    """
    if parys == 0.0:
        return [6.0 * x * (1.0 - x) for x in X]
    if parys > 40.0:
        v = [1.0] * len(X)
        v[0] = 0.0
        v[-1] = 0.0
        return v
    den = math.exp(2.0 * parys) * (parys - 1.0) + parys + 1.0
    return [
        parys * (1.0 - math.exp(2.0 * parys * x)) * (1.0 - math.exp(2.0 * parys * (1.0 - x))) / den
        for x in X
    ]


def thomas(a: List[float], b: List[float], c: List[float], d: List[float]) -> List[float]:
    """Решение трёхдиагональной СЛАУ методом прогонки (алгоритм Томаса)."""
    n = len(b)
    cp = [0.0] * n
    dp = [0.0] * n
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = [0.0] * n
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


@dataclass
class Layer:
    """Результаты расчёта на одном слое Y."""

    Y: float            # текущая безразмерная длина
    C: List[float]      # профиль концентрации по всей сетке X
    C11: List[float]    # концентрация в 11 опорных точках X = 0, 0.1, …, 1.0
    cdav: float         # среднерасходная концентрация (главный результат)
    i: float            # локальная плотность тока
    iint: float         # сила тока (интеграл I по Y)
    iav: float          # средняя по длине плотность тока
    delta: float        # мин. толщина ДПС у АОМ (X=0)
    deltk: float        # мин. толщина ДПС у КОМ (X=1)
    dela: float         # макс. толщина ДПС у АОМ
    delk: float         # макс. толщина ДПС у КОМ
    step: int           # номер шага марша


class Engine:
    """Решатель краевой задачи ELDIAL по параметрам :class:`Params`."""

    def __init__(self, params: Params, N: int = 200):
        self.P = params
        self.N = N
        self.dX = 1.0 / N
        self.X = [i / N for i in range(N + 1)]
        self.V = velocity_profile(self.X, params.parys)
        # индексы 11 опорных точек X = 0, 0.1, …, 1.0
        self._idx11 = [int(round(k / 10 * N)) for k in range(11)]

    # ------------------------- интегральные характеристики -------------------------
    def _trapz(self, y: List[float]) -> float:
        dX = self.dX
        return sum((y[i] + y[i + 1]) * 0.5 * dX for i in range(len(y) - 1))

    def cdav(self, C: List[float]) -> float:
        """Среднерасходная концентрация ∫₀¹ C·V dX."""
        return self._trapz([C[i] * self.V[i] for i in range(len(C))])

    def resistance(self, C: List[float]) -> float:
        """Безразмерное сопротивление цепи: 2·tp·tn·(rac + ∫dX/C + 1/cb)."""
        S = self._trapz([1.0 / max(c, 1e-9) for c in C])
        return 2.0 * self.P.tp * self.P.tn * (self.P.rac + S + 1.0 / self.P.cb)

    def current(self, C: List[float]) -> float:
        """Локальная безразмерная плотность тока I = dpsi / R(C)."""
        return max(self.P.dpsi / self.resistance(C), 0.0)

    def initial_current(self) -> float:
        """Ток на входе (C ≡ 1)."""
        return self.current([1.0] * (self.N + 1))

    def diffusion_layers(self, C: List[float]):
        """Оценка толщины ДПС у обеих мембран: вилка (мин/макс) по профилю C(X)."""
        dX = self.dX
        Cmax = max(C)
        s0 = (C[1] - C[0]) / dX          # наклон у X=0 (АОМ)
        s1 = (C[-1] - C[-2]) / dX        # наклон у X=1 (КОМ)
        # минимальная оценка — метод касательной (ур. 5.47)
        da_min = (Cmax - C[0]) / s0 if s0 > 1e-9 else 0.0
        dk_min = (Cmax - C[-1]) / (-s1) if -s1 > 1e-9 else 0.0

        # максимальная оценка — расстояние до выхода на объёмную концентрацию
        def reach(start: int, step: int) -> float:
            i, k = start, 0
            while 0 <= i <= self.N and C[i] < 0.99 * Cmax:
                i += step
                k += 1
                if not (0 <= i <= self.N):
                    break
            return k * dX

        return da_min, dk_min, reach(0, +1), reach(self.N, -1)

    # --------------------------- трёхдиагональный решатель ---------------------------
    def _prep_lhs(self, r: float):
        """Предвычислить коэффициенты прогонки для постоянной (вдоль канала) матрицы.

        Левая часть СЛАУ зависит только от профиля V и шага r=tau/dX², поэтому
        прямой ход прогонки (cp, знаменатели) считается один раз на значение tau.
        """
        N, V = self.N, self.V
        # диагонали: a — поддиагональ, b — главная, c — наддиагональ
        b = [0.0] * (N + 1)
        c = [0.0] * (N + 1)
        a = [0.0] * (N + 1)
        b[0], c[0] = 1.0, -1.0                   # ГУ Неймана при X=0
        for i in range(1, N):
            a[i], b[i], c[i] = -r, V[i] + 2.0 * r, -r
        a[N], b[N] = -1.0, 1.0                    # ГУ Неймана при X=1
        cp = [0.0] * (N + 1)
        denom = [0.0] * (N + 1)
        denom[0] = b[0]
        cp[0] = c[0] / b[0]
        for i in range(1, N + 1):
            denom[i] = b[i] - a[i] * cp[i - 1]
            cp[i] = c[i] / denom[i]
        return cp, denom, a

    def _solve(self, d: List[float], cp: List[float], denom: List[float], a: List[float]) -> List[float]:
        """Обратный ход прогонки для заданной правой части d (cp/denom предвычислены)."""
        N = self.N
        dp = [0.0] * (N + 1)
        dp[0] = d[0] / denom[0]
        for i in range(1, N + 1):
            dp[i] = (d[i] - a[i] * dp[i - 1]) / denom[i]
        x = [0.0] * (N + 1)
        x[N] = dp[N]
        for i in range(N - 1, -1, -1):
            x[i] = dp[i] - cp[i] * x[i + 1]
        return x

    # ------------------------------- маршевый расчёт -------------------------------
    def march(self) -> Iterator[Layer]:
        """Генератор слоёв расчёта от Y=0 до ymax с шагом tau (адаптивным при lkr=1)."""
        P, N, dX, V = self.P, self.N, self.dX, self.V
        C = [1.0] * (N + 1)
        kA = P.Tna - P.tn
        kK = P.Tpc - P.tp
        tau = P.tau
        I = self.current(C)
        Y = 0.0
        iint = 0.0
        step = 0
        c1_prev = C[-1]
        cp, denom, aL = self._prep_lhs(tau / dX ** 2)
        cur_r = tau / dX ** 2

        while Y < P.ymax - 1e-12:
            r = tau / dX ** 2
            if r != cur_r:                       # шаг изменился (адаптивный режим) — пересобрать СЛАУ
                cp, denom, aL = self._prep_lhs(r)
                cur_r = r
            Cn = list(C)
            # правая часть для внутренних узлов не зависит от тока — собираем один раз
            d = [0.0] * (N + 1)
            for i in range(1, N):
                d[i] = V[i] * Cn[i]
            # итерационное согласование тока I со скачком потенциала dpsi
            for _ in range(60):
                d[0] = -dX * I * kA              # меняются только граничные правые части
                d[N] = -dX * I * kK
                C = [v if v > 0.0 else 0.0 for v in self._solve(d, cp, denom, aL)]
                Inew = self.current(C)
                if abs(Inew - I) < P.epsac:
                    I = Inew
                    break
                I = 0.5 * (I + Inew)

            iint += I * tau
            Y += tau
            step += 1
            da, dk, dA, dK = self.diffusion_layers(C)
            yield Layer(
                Y=Y, C=list(C), C11=[C[j] for j in self._idx11], cdav=self.cdav(C),
                i=I, iint=iint, iav=iint / Y, delta=da, deltk=dk, dela=dA, delk=dK,
                step=step,
            )

            # адаптивный шаг (lkr=1): ×10 при медленном изменении концентрации (§4.2)
            if P.lkr == 1 and tau <= 0.005 and step % 10 == 0:
                rel = abs(c1_prev - C[-1]) / max(c1_prev, 1e-12)
                if rel <= 0.01:
                    tau *= 10.0
                c1_prev = C[-1]

    def run(self) -> List[Layer]:
        """Выполнить расчёт и вернуть список слоёв (удобно для анализа/экспорта)."""
        return list(self.march())
