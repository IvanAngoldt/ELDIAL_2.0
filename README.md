# ElDial (ELDIAL_2.0)

**Программная система для моделирования электромембранных процессов**

ФГБОУ ВО «Кубанский государственный университет», ФКТиПМ.  
Автор: **Ангольдт И.А.**, группа ПМ-51.

---

## Описание

ElDial — настольная программная система для численного моделирования электромембранных процессов (электродиализ, диффузионный диализ и др.). Система позволяет:

- создавать проекты моделирования;
- вводить и валидировать параметры мембран, растворов и режимов;
- выполнять расчёт на основе уравнений Нернста-Планка;
- сохранять результаты в СУБД PostgreSQL (или SQLite);
- визуализировать графики и таблицы;
- формировать отчётную документацию.

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.10+ |
| GUI | Tkinter |
| Вычисления | NumPy |
| Таблицы | Pandas |
| Графики | Matplotlib |
| СУБД | PostgreSQL / SQLite |
| ORM | SQLAlchemy |
| Отчёты | ReportLab, python-docx |

## Архитектура (модули)

```
eldial/
├── modules/
│   ├── ui/                 # Пользовательский интерфейс
│   ├── parameters/         # Ввод параметров моделирования
│   ├── math_model/         # Математическая модель процесса
│   ├── computation/        # Выполнение вычислений
│   ├── storage/            # Хранение данных и результатов
│   ├── visualization/      # Визуализация результатов
│   └── reporting/          # Формирование отчётов
├── domain/                 # Доменные сущности
├── core/                   # Конфигурация, константы
database/schema.sql         # Схема PostgreSQL
mock/                       # Веб-макеты экранов для отчёта
```

## Установка

```bash
git clone https://github.com/<username>/eldial.git
cd eldial
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 scripts/init_db.py
```

## Запуск

```bash
# Графический интерфейс (Tkinter)
python3 -m eldial.app

# или
python3 main.py

# Веб-макеты для скриншотов отчёта
python3 main.py --web

# Консольный демо-расчёт
python3 -m eldial.app --demo

# Инициализация БД
python3 -m eldial.app --init-db
```

## Модель данных

Основные сущности (PostgreSQL):

- `users` — пользователи системы
- `projects` — проекты моделирования
- `simulations` — вычислительные эксперименты
- `model_results` — результаты расчёта
- `membranes`, `parameters` — характеристики процесса

Схема: [`database/schema.sql`](database/schema.sql)

## Тестирование

```bash
pytest tests/ -v
```

## Документация

- [`docs/architecture.md`](docs/architecture.md) — структура ПО
- [`docs/algorithms.md`](docs/algorithms.md) — описание алгоритмов

## Лицензия

Учебный проект. © 2026 Ангольдт И.А.
