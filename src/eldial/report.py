"""Форматирование результатов ELDIAL: числа в стиле Fortran, таблицы, текстовый отчёт, CSV.

Вывод имитирует оригинальный формат программы ELDIAL (блоки «ИСХОДНЫЕ ДАННЫЕ»,
«ПРОФИЛЬ СКОРОСТЕЙ», «ИНФОРМАЦИЯ О ПАРАМЕТРАХ СЛОЯ»).
"""
from __future__ import annotations

import csv
import math
from typing import Callable, List

from .model import Engine, Layer
from .params import Params


# ------------------------------- форматирование чисел -------------------------------
def fF(x: float, dec: int = 4, width: int = 7) -> str:
    """Десятичный формат с фиксированным числом знаков и ведущим нулём (0.4000, -0.4000)."""
    return f"{x:.{dec}f}".rjust(width)


def fG(x: float, width: int = 10) -> str:
    """Десятичный формат с ~4 значащими цифрами (без экспоненты, с ведущим нулём: 0.06111)."""
    if x == 0:
        return "0.0000".rjust(width)
    a = abs(x)
    intdig = int(math.floor(math.log10(a))) + 1
    dec = max(0, 4 - intdig)
    return f"{x:.{dec}f}".rjust(width)


Writer = Callable[[str], None]


def _xtable(out: Writer, label: str, X: List[float], vals: List[float]) -> None:
    """Таблица 11 точек X=0…1, разбитая на две строки (как в оригинале ELDIAL)."""
    half = 6
    out("      x  | " + " | ".join(fF(t, 4, 6) for t in X[:half]))
    out("      " + "-" * 58)
    out(f"      {label}  | " + " | ".join(fF(t, 4, 6) for t in vals[:half]))
    out("")
    out("      x  | " + " | ".join(fF(t, 4, 6) for t in X[half:]))
    out("      " + "-" * 51)
    out(f"      {label}  | " + " | ".join(fF(t, 4, 6) for t in vals[half:]))


def banner(out: Writer) -> None:
    out("")
    out("    " + "=" * 60)
    out("    " + "Р Е Ж И М   Р А Б О Т Ы:".center(60))
    out("    " + "ЭЛЕКТРОДИАЛИЗНОЕ ОБЕССОЛИВАНИЕ".center(60))
    out("    " + "=" * 60)
    out("")


def print_inputs(out: Writer, p: Params) -> None:
    """Блок «ИСХОДНЫЕ ДАННЫЕ»."""
    out("    И С Х О Д Н Ы Е   Д А Н Н Ы Е")
    out("")
    rows = [
        ("tp", p.tp), ("tn", p.tn), ("tpefc", p.Tpc), ("tnefa", p.Tna),
        ("zp", p.zp), ("zn", p.zn), ("cb", p.cb), ("cd0", p.cd0),
        ("rac", p.rac), ("g", p.g), ("parys", p.parys), ("dpsi", p.dpsi),
        ("ymin", p.ymin), ("ymax", p.ymax),
    ]
    for name, v in rows:
        out(f"       {name:<7}= {fF(v, 4, 9)}")
    out(f"       {'tau':<7}= {fF(p.tau, 6, 11)}")
    out(f"       {'epsac':<7}= {fF(p.epsac, 6, 11)}")
    out("")


def _layer_block(out: Writer, eng: Engine, p: Params, L: Layer) -> None:
    out("     " + "=" * 60)
    out("       И Н Ф О Р М А Ц И Я   О   П А Р А М Е Т Р А Х   С Л О Я")
    out("      " + "*" * 56)
    out("")
    out(f"       длина аппарата  y = {fF(L.Y, 6, 10)}")
    out("")
    out("       распределение концентрации по ширине канала")
    out("")
    step = eng.N // 10
    _xtable(out, "c", eng.X[::step], L.C11)
    out("")
    out(f"       delta= {fG(L.delta)}   deltk= {fG(L.deltk)}   dela= {fG(L.dela)}   delk= {fG(L.delk)}")
    out(f"       i    = {fG(L.i)}   iint = {fG(L.iint)}   iav = {fG(L.iav)}   cdav = {fG(L.cdav)}")
    out("")


def preamble(eng: Engine, p: Params) -> List[str]:
    """Заголовок отчёта: блоки исходных данных, начального распределения и профиля скоростей."""
    lines: List[str] = []
    out = lines.append
    step = eng.N // 10
    banner(out)
    print_inputs(out, p)
    out(f"     расчёт для dpsi = {fF(p.dpsi, 3, 8)}")
    out("")
    out("       начальное распределение концентрации (Y=0)")
    out("")
    _xtable(out, "c", eng.X[::step], [1.0] * 11)
    out("")
    out(f"       i = {fG(eng.initial_current(), 9)}")
    out("")
    out("       П Р О Ф И Л Ь   Р А С П Р Е Д Е Л Е Н И Я   С К О Р О С Т Е Й")
    out("      " + "*" * 56)
    out("")
    _xtable(out, "v", eng.X[::step], [eng.V[i] for i in range(0, eng.N + 1, step)])
    out("")
    return lines


def layer_block_lines(eng: Engine, p: Params, L: Layer) -> List[str]:
    """Текст одного блока «ИНФОРМАЦИЯ О ПАРАМЕТРАХ СЛОЯ» в виде списка строк."""
    lines: List[str] = []
    _layer_block(lines.append, eng, p, L)
    return lines


def selected_layers(eng: Engine, p: Params, layers: List[Layer]) -> List[Layer]:
    """Слои, отбираемые на печать по правилам ymin и np (кратность печати)."""
    npr = max(1, int(p.np))
    return [L for L in layers if L.Y >= p.ymin - 1e-12 and L.step % npr == 0]


def footer_line(layers: List[Layer]) -> str:
    if not layers:
        return ""
    return f"      достигнута заданная длина аппарата,  т.е. y = {fF(layers[-1].Y, 4, 8)}"


def full_report(p: Params, out: Writer, N: int = 200) -> List[Layer]:
    """Полный отчёт в стиле ELDIAL (печать всех отобранных слоёв). Возвращает все слои."""
    eng = Engine(p, N=N)
    for s in preamble(eng, p):
        out(s)
    layers = eng.run()
    for L in selected_layers(eng, p, layers):
        for s in layer_block_lines(eng, p, L):
            out(s)
    foot = footer_line(layers)
    if foot:
        out(foot)
    return layers


# --------------------------------- сводная таблица ---------------------------------
def summary_table(layers: List[Layer], every: int = 1) -> str:
    """Компактная сводка по слоям (Y, cdav, i, iav, толщины ДПС)."""
    head = f"{'Y':>9} {'cdav':>9} {'C(0)':>8} {'C(1)':>8} {'i':>9} {'iav':>9} {'deltk':>8} {'delk':>8}"
    lines = [head, "-" * len(head)]
    for k, L in enumerate(layers):
        if k % every != 0 and L is not layers[-1]:
            continue
        lines.append(
            f"{L.Y:9.4f} {L.cdav:9.4f} {L.C11[0]:8.4f} {L.C11[-1]:8.4f} "
            f"{L.i:9.3f} {L.iav:9.3f} {L.deltk:8.4f} {L.delk:8.4f}"
        )
    return "\n".join(lines)


def export_csv(layers: List[Layer], path: str) -> None:
    """Экспорт результатов по слоям в CSV (для построения графиков во внешних программах)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Y", "cdav", "C_X0", "C_X1", "i", "iint", "iav",
                    "delta", "deltk", "dela", "delk"])
        for L in layers:
            w.writerow([f"{L.Y:.6f}", f"{L.cdav:.6f}", f"{L.C11[0]:.6f}",
                        f"{L.C11[-1]:.6f}", f"{L.i:.6f}", f"{L.iint:.6f}",
                        f"{L.iav:.6f}", f"{L.delta:.6f}", f"{L.deltk:.6f}",
                        f"{L.dela:.6f}", f"{L.delk:.6f}"])


def export_profile_csv(eng: Engine, layers: List[Layer], targets: List[float], path: str) -> None:
    """Экспорт профилей C(X) при заданных значениях Y (аналог файла ELDIAL.GRX)."""
    chosen = []
    for yt in targets:
        L = min(layers, key=lambda L: abs(L.Y - yt))
        chosen.append(L)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["X"] + [f"C(Y={L.Y:.4f})" for L in chosen])
        for i in range(eng.N + 1):
            w.writerow([f"{eng.X[i]:.4f}"] + [f"{L.C[i]:.6f}" for L in chosen])
