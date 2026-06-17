#!/usr/bin/env python3
"""Запуск ELDIAL-PY без установки пакета:  python main.py"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from eldial.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
