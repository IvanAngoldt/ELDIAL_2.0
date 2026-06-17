"""Интерактивное консольное меню ELDIAL."""
from __future__ import annotations

import os
import sys
from typing import Optional

from . import params as P
from .model import Engine
from . import report, services
from .params import Params, DEFAULT_PARAMS, read_dat, write_dat, DESCRIPTIONS, PARAM_ORDER, fnum

LINE = "=" * 64
YES = ("д", "да", "y", "yes", "1")  # утвердительные ответы
# каталог приложения: рядом с .exe (в собранной версии) или текущая папка (запуск из исходников)
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.getcwd()
DATA_DIR = os.path.join(APP_DIR, "data")               # папка data рядом с программой
DAT_PATH = os.path.join(DATA_DIR, "Eldial.DAT")        # единственный файл исходных данных
RES_PATH = os.path.join(DATA_DIR, "ELDIAL.RES")        # текстовый отчёт расчёта
CSV_PATH = os.path.join(DATA_DIR, "eldial_layers.csv")  # экспорт результатов по слоям
N_MIN, N_MAX, N_DEFAULT = 20, 2000, 200                # границы числа узлов сетки по X


# ------------------------------- помощники ввода -------------------------------
def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default != "" else ""
    try:
        a = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        return default
    return a if a else default


def ask_float(prompt: str, default: float) -> float:
    while True:
        a = ask(prompt, fnum(default))
        try:
            return float(a.replace(",", "."))
        except ValueError:
            print("  ! введите число")


def pause() -> None:
    try:
        input("\n[Enter — продолжить] ")
    except EOFError:
        pass


def header(title: str) -> None:
    print("\n" + LINE)
    print(f"  {title}")
    print(LINE)


def progress(cur: float, total: float, width: int = 30, label: str = "расчёт") -> None:
    """Перерисовать строку прогресса: [#####-----]  42%  Y=0.063/0.150."""
    frac = 0.0 if total <= 0 else max(0.0, min(1.0, cur / total))
    filled = int(round(frac * width))
    bar = "#" * filled + "-" * (width - filled)
    print(f"\r  {label}: [{bar}] {frac * 100:5.1f}%  Y={cur:.4f}/{fnum(total)}",
          end="", flush=True)


def progress_clear() -> None:
    """Стереть строку прогресса (вернуть курсор в начало и затереть пробелами)."""
    print("\r" + " " * 70 + "\r", end="", flush=True)


# --------------------------------- состояние ---------------------------------
class App:
    def __init__(self) -> None:
        self.params: Params = DEFAULT_PARAMS.copy()
        self.source = "(значения по умолчанию)"
        self.N = N_DEFAULT
        # автозагрузка из data/Eldial.DAT, если файл есть
        if os.path.exists(DAT_PATH):
            try:
                self.params = read_dat(DAT_PATH)
                self.source = DAT_PATH
            except Exception:
                pass

    # ------------------------------- пункты меню -------------------------------
    def show_params(self) -> None:
        header("ТЕКУЩИЕ ПАРАМЕТРЫ")
        print(f"  источник данных: {self.source}")
        print(f"  узлов сетки по X (N): {self.N}\n")
        for name in PARAM_ORDER:
            v = getattr(self.params, name)
            sval = f"{int(v)}" if name in P.INT_PARAMS else fnum(v)
            print(f"  {name:<8}= {sval:<10} — {DESCRIPTIONS.get(name, '')}")
        print(f"  {'udop':<8}= {', '.join(fnum(u) for u in self.params.udop)}")
        warns = self.params.validate()
        if warns:
            print("\n  ВНИМАНИЕ:")
            for w in warns:
                print(f"   - {w}")
        pause()

    def edit_params(self) -> None:
        header("ИЗМЕНЕНИЕ ПАРАМЕТРОВ")
        print("  Enter — оставить текущее значение. Введите 'q' для выхода.\n")
        aborted = False
        for name in PARAM_ORDER:
            cur = getattr(self.params, name)
            sval = f"{int(cur)}" if name in P.INT_PARAMS else fnum(cur)
            a = ask(f"  {name} ({DESCRIPTIONS.get(name, '')})", sval)
            if a.lower() == "q":
                aborted = True
                break
            try:
                self.params.set(name, a)
            except ValueError:
                print("    ! некорректное значение, оставлено прежнее")
        if not aborted:
            a = ask("  udop (через пробел)", ", ".join(fnum(u) for u in self.params.udop))
            if a.lower() != "q":
                try:
                    self.params.set("udop", a)
                except ValueError:
                    pass
        try:
            os.makedirs(os.path.dirname(DAT_PATH), exist_ok=True)
            write_dat(self.params, DAT_PATH)
            self.source = DAT_PATH
            print(f"\n  изменения сохранены в {DAT_PATH}")
        except Exception as e:
            self.source = "(изменено вручную)"
            print(f"\n  ! не удалось сохранить в {DAT_PATH}: {e}")
        warns = self.params.validate()
        if warns:
            print("\n  ВНИМАНИЕ:")
            for w in warns:
                print(f"   - {w}")
        pause()

    def load_dat(self) -> None:
        header("ЗАГРУЗКА ДАННЫХ ИЗ ФАЙЛА")
        print(f"  файл исходных данных: {DAT_PATH}")
        print("  (редактируйте этот файл вручную, чтобы изменить параметры)")
        if not os.path.exists(DAT_PATH):
            print(f"  ! файл не найден: {DAT_PATH}")
            return pause()
        try:
            self.params = read_dat(DAT_PATH)
            self.source = DAT_PATH
            print(f"  данные загружены из {DAT_PATH}")
        except Exception as e:
            print(f"  ! ошибка чтения: {e}")
        pause()

    def run_calc(self) -> None:
        header("РАСЧЁТ (полный отчёт в стиле ELDIAL)")
        warns = self.params.validate()
        if warns:
            print("  ВНИМАНИЕ:")
            for w in warns:
                print(f"   - {w}")
            if ask("  продолжить расчёт? (д/н)", "д").lower() not in YES:
                return
        eng = Engine(self.params, N=self.N)
        npr = max(1, int(self.params.np))
        ymin, ymax = self.params.ymin, self.params.ymax

        print("\n  Режим вывода на экран:")
        print("    1 — по шагам (Enter — далее, p — назад, число — к Y, a — до конца (итог), q — стоп)")
        print("    2 — не выводить на экран (только сохранить в файл)")
        mode = ask("  выбор", "1")

        # шапка отчёта печатается всегда (кроме режима «только файл»)
        pre = report.preamble(eng, self.params)
        if mode != "2":
            print("\n".join(pre))

        # потоковый (ленивый) расчёт: считаем слой за слоем, все слои кешируем в памяти
        # (это позволяет в пошаговом режиме листать и назад, без временного файла)
        layers: list = []
        gen = eng.march()
        stopped = False
        completed = False

        def passes(L) -> bool:
            """Слой попадает в печать (фильтр по ymin и кратности np)."""
            return L.Y >= ymin - 1e-12 and L.step % npr == 0

        def compute_next():
            """Посчитать следующий слой из генератора и добавить в кеш. None — конец."""
            nonlocal completed
            try:
                L = next(gen)
            except StopIteration:
                completed = True
                return None
            layers.append(L)
            return L

        def ensure_to(target: float) -> None:
            """Досчитать молча до Y>=target (или до конца расчёта)."""
            goal = min(target, ymax)
            while not completed and (not layers or layers[-1].Y < target - 1e-12):
                L = compute_next()
                if L is not None and L.step % 100 == 0:
                    progress(L.Y, goal)
            progress_clear()

        if mode == "2":
            ensure_to(ymax + 1.0)                       # посчитать всё (только в файл)
            print(f"  расчёт завершён: {len(layers)} слоёв.")
        else:                                           # mode == "1" — навигация вперёд/назад
            def next_view(pos: int):
                """Индекс следующего отображаемого слоя после pos (дорасчёт при нужде)."""
                k = pos + 1
                while True:
                    while k < len(layers):
                        if passes(layers[k]):
                            return k
                        k += 1
                    if compute_next() is None:
                        return None

            def prev_view(pos: int):
                for k in range(pos - 1, -1, -1):
                    if passes(layers[k]):
                        return k
                return None

            pos = next_view(-1)
            summarized = False
            if pos is None:
                print("  нет слоёв для показа.")
            while pos is not None:
                print("\n".join(report.layer_block_lines(eng, self.params, layers[pos])))
                cmd = ask(f"  [Y={layers[pos].Y:.4f}] Enter — далее, p — назад, "
                          "число — к Y, a — до конца (итог), q — стоп").strip().lower()
                if cmd == "q":
                    stopped = True
                    break
                elif cmd == "a":
                    ensure_to(ymax + 1.0)               # досчитать всё с прогресс-баром
                    self._print_summary(layers)
                    summarized = True
                    break
                elif cmd == "p":
                    pr = prev_view(pos)
                    if pr is None:
                        print("  ! это первый показанный слой")
                    else:
                        pos = pr
                elif cmd:
                    try:
                        target = float(cmd.replace(",", "."))
                    except ValueError:
                        print("  ! не число")
                        continue
                    if target > ymax + 1e-9:
                        print(f"  ! Y={fnum(target)} больше ymax={fnum(ymax)}")
                        continue
                    ensure_to(target)
                    pos = min(range(len(layers)), key=lambda k: abs(layers[k].Y - target))
                else:
                    nxt = next_view(pos)
                    if nxt is None:
                        print("  (достигнут конец расчёта)")
                        break
                    pos = nxt
            if not stopped and not summarized and layers and layers[-1].Y >= ymax - 1e-12:
                print(report.footer_line(layers))

        # сохранение результатов в data/ (без запроса пути)
        print("\n" + LINE)
        os.makedirs(DATA_DIR, exist_ok=True)
        if not completed:
            if ask("  расчёт не завершён. дорассчитать до конца? (д/н)", "н").lower() in YES:
                for L in gen:                       # продолжаем тот же генератор без пересчёта
                    layers.append(L)
                    if L.step % 100 == 0:
                        progress(L.Y, ymax, label="дорасчёт")
                progress_clear()
                completed = True
        save_res = ask(f"  сохранить отчёт в файл {RES_PATH}? (д/н)", "н").lower() in YES
        save_csv = ask(f"  экспортировать результаты по слоям в CSV ({CSV_PATH})? (д/н)", "н").lower() in YES
        if save_res:
            shown = report.selected_layers(eng, self.params, layers)
            buf = list(pre)
            for L in shown:
                buf.extend(report.layer_block_lines(eng, self.params, L))
            if completed:
                buf.append(report.footer_line(layers))
            with open(RES_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(buf) + "\n")
            print(f"  отчёт сохранён в {RES_PATH}")
        if save_csv:
            report.export_csv(layers, CSV_PATH)
            print(f"  CSV сохранён в {CSV_PATH}")
        pause()

    def _print_summary(self, layers: list) -> None:
        """Итог расчёта: сводная таблица по слоям + достигнутая степень обессоливания."""
        if not layers:
            print("  нет данных для сводки.")
            return
        every = max(1, len(layers) // 25)
        print()
        print(report.summary_table(layers, every=every))
        last = layers[-1]
        alpha = services.desalination_degree(last.cdav)
        print(f"\n  на Y={last.Y:.4f}: cdav={last.cdav:.4f}, "
              f"степень обессоливания α={alpha*100:.1f}%")

    def quick_summary(self) -> None:
        header("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
        eng = Engine(self.params, N=self.N)
        ymax = self.params.ymax
        layers = []
        for L in eng.march():                       # потоковый расчёт с индикатором прогресса
            layers.append(L)
            if L.step % 50 == 0:
                progress(L.Y, ymax)
        progress(ymax, ymax)
        progress_clear()
        self._print_summary(layers)
        pause()

    def task_find_Y(self) -> None:
        header("ЗАДАЧА: подбор длины Y под заданную степень обессоливания")
        deg = ask_float("  степень обессоливания, % ", 60.0) / 100.0
        ymax = self.params.ymax

        def on_step(L):
            if L.step % 50 == 0:
                progress(L.Y, ymax, label="подбор Y")

        Yt, layers = services.find_Y_for_desalination(self.params, deg, N=self.N, on_step=on_step)
        progress_clear()
        if Yt is None:
            print(f"\n  целевая степень {deg*100:.0f}% не достигнута при ymax={fnum(self.params.ymax)}.")
            print("  увеличьте ymax или dpsi.")
            return pause()
        print(f"\n  степень {deg*100:.0f}% (cdav={1-deg:.4f}) достигается при Y = {Yt:.4f}")
        print("\n  пересчёт в физические величины (необязательно):")
        if ask("  выполнить пересчёт? (д/н)", "н").lower() in YES:
            h = ask_float("    межмембранное расстояние h, см", 0.05)
            v = ask_float("    средняя скорость v̄, см/с", 3.2)
            D = ask_float("    коэффициент диффузии D, см²/с", services.D_NACL)
            y = services.Y_to_length(Yt, v, h, D)
            print(f"    длина канала  y = {y:.2f} см")
            if ask("    рассчитать производительность? (д/н)", "н").lower() in YES:
                a = ask_float("      ширина мембраны a, см", 40.0)
                n = ask_float("      число парных камер", 100.0)
                W = services.production_lph(v, h, a, n)
                print(f"      производительность W = {W:.1f} л/ч")
        pause()

    def task_ilim(self) -> None:
        header("ЗАДАЧА: предельная плотность тока (Пирс / Левек)")
        D = ask_float("  коэффициент диффузии D, см²/с", services.D_NACL)
        c0 = ask_float("  концентрация c0, моль/см³ (напр. 1e-4)", 1e-4)
        delta = ask_float("  толщина ДПС δ, см", 0.02)
        T1 = ask_float("  эфф. число переноса в мембране T1", self.params.Tpc)
        t1 = ask_float("  число переноса в растворе t1", self.params.tp)
        ilim = services.peers_ilim(D, c0, delta, T1, t1)
        print(f"\n  предельная плотность тока (Пирс): i_lim = {ilim:.4f} А/см²")
        Y = ask_float("  безразмерная длина Y (для оценки Левека, Y<0.05)", 0.02)
        dTmax = max(self.params.Tna - self.params.tn, self.params.Tpc - self.params.tp)
        iav = services.leveque_ilim_av(dTmax, Y)
        print(f"  средняя предельная (Левек): I_AV,пред = {iav:.4f} (безразмерная)")
        pause()

    def set_grid(self) -> None:
        header("ТОЧНОСТЬ СЕТКИ")
        print("  N — число узлов сетки по ширине канала (целое, больше = точнее, но медленнее).")
        print(f"  допустимо: {N_MIN}…{N_MAX}, рекомендуется 100–400, по умолчанию {N_DEFAULT}.")
        val = int(round(ask_float("  число узлов по X (N)", self.N)))
        if val < N_MIN:
            print(f"  ! слишком мало; установлено минимальное N={N_MIN}")
            val = N_MIN
        elif val > N_MAX:
            print(f"  ! слишком много (будет очень медленно); установлено максимальное N={N_MAX}")
            val = N_MAX
        self.N = val
        print(f"  N = {self.N}")
        pause()

    def show_about(self) -> None:
        header("О ПРОГРАММЕ")
        print(__doc__ or "")
        print("  ELDIAL-PY — реконструкция программы электродиализного обессоливания.")
        print("  Модель: 2D конвективная электродиффузия в камере обессоливания.")
        pause()

    # --------------------------------- цикл меню ---------------------------------
    def menu(self) -> None:
        items = [
            ("1", "Показать текущие параметры", self.show_params),
            ("2", "Изменить параметры", self.edit_params),
            ("3", "Загрузить данные из файла (data/Eldial.DAT)", self.load_dat),
            ("4", "РАССЧИТАТЬ (полный отчёт)", self.run_calc),
            ("5", "Сводная таблица результатов (кратко)", self.quick_summary),
            ("6", "Задача: подбор длины Y под степень обессоливания", self.task_find_Y),
            ("7", "Задача: предельная плотность тока", self.task_ilim),
            ("8", "Точность сетки (N)", self.set_grid),
            ("0", "О программе", self.show_about),
            ("q", "Выход", None),
        ]
        while True:
            print("\n" + LINE)
            print("  ELDIAL — ЭЛЕКТРОДИАЛИЗНОЕ ОБЕССОЛИВАНИЕ")
            print(f"  данные: {self.source}   |   dpsi={fnum(self.params.dpsi)}, "
                  f"ymax={fnum(self.params.ymax)}, N={self.N}")
            print(LINE)
            for key, label, _ in items:
                print(f"   {key}.  {label}")
            choice = ask("\n  выберите пункт").lower()
            action = next((fn for k, _, fn in items if k == choice), False)
            if action is None:  # выход
                print("\n  Завершение работы. До свидания!")
                return
            if action is False:
                print("  ! нет такого пункта")
                continue
            try:
                action()
            except KeyboardInterrupt:
                print("\n  (прервано)")
            except Exception as e:
                print(f"\n  ! ошибка: {e}")
                pause()


def main(argv: Optional[list] = None) -> int:
    app = App()
    print("\n  Добро пожаловать в ELDIAL-PY!")
    try:
        app.menu()
    except KeyboardInterrupt:
        print("\n  Завершение работы.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
