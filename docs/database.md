# Модель данных ElDial

## СУБД

Основная: **PostgreSQL**. Резервный режим: **SQLite** (`data/eldial.sqlite3`).

## Таблицы

| Таблица | Описание |
|---------|----------|
| `users` | Учётные записи |
| `projects` | Проекты моделирования |
| `membranes` | Параметры мембранного стека |
| `parameters` | Параметры раствора и режима |
| `simulations` | Запуски расчёта |
| `model_results` | Интегральные результаты |
| `time_series_data` | Временные ряды |
| `reports` | Сформированные отчёты |

## Инициализация

```bash
python3 scripts/init_db.py
```

SQL-схема: `database/schema.sql`
