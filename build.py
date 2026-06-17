#!/usr/bin/env python3
"""Сборка распространяемой версии ELDIAL.

Результат — папка ``dist/Eldial_2.0`` со структурой:

    Eldial_2.0/
        Eldial(.exe)        — исполняемый файл
        core/               — служебные файлы рантайма PyInstaller
        data/Eldial.DAT     — входные данные (пользователь редактирует вручную)

Запуск:  python build.py

ВАЖНО: PyInstaller НЕ умеет кросс-компиляцию. На Windows получится ``Eldial.exe``,
на macOS/Linux — соответствующий бинарник. Чтобы собрать .exe для Windows,
запускайте этот скрипт на Windows.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "Eldial"          # имя исполняемого файла
DIST_NAME = "Eldial_2.0"     # имя итоговой папки-дистрибутива
DIST_DIR = os.path.join(ROOT, "dist")
BUILT_DIR = os.path.join(DIST_DIR, APP_NAME)
OUT_DIR = os.path.join(DIST_DIR, DIST_NAME)


def main() -> int:
    # 1) очистить прошлые сборки
    for d in (BUILT_DIR, OUT_DIR, os.path.join(ROOT, "build")):
        shutil.rmtree(d, ignore_errors=True)

    # 2) запустить PyInstaller (onedir, папка рантайма называется "core")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onedir",
        "--console",
        "--name", APP_NAME,
        "--contents-directory", "core",
        "--paths", os.path.join(ROOT, "src"),
        os.path.join(ROOT, "main.py"),
    ]
    print("Сборка:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)

    # 3) переименовать папку сборки dist/Eldial -> dist/Eldial_2.0
    os.rename(BUILT_DIR, OUT_DIR)

    # 4) положить рядом редактируемую папку data/ с входным файлом
    data_dst = os.path.join(OUT_DIR, "data")
    os.makedirs(data_dst, exist_ok=True)
    shutil.copy2(os.path.join(ROOT, "data", "Eldial.DAT"),
                 os.path.join(data_dst, "Eldial.DAT"))

    exe = APP_NAME + (".exe" if os.name == "nt" else "")
    print("\nГотово!")
    print(f"  дистрибутив: {OUT_DIR}")
    print(f"  запуск:      {os.path.join(OUT_DIR, exe)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
