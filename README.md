# DAMU Projects Parser

Парсер открытых отчётов Фонда развития предпринимательства **ДАМУ** (Казахстан).

## Источник данных

Основной источник — раздел отчётов на [damu.kz/ru/reports/](https://damu.kz/ru/reports/). Фонд регулярно публикует Excel-файлы с проектами по:

| Тип | Что внутри | Пример файла |
|-----|------------|--------------|
| **Субсидирование** | ~120k проектов с 2010 года | `Отчет по проектам субсидирования на 01.08.2026г.xlsx` |
| **Гарантирование** | Проекты Гарантийного фонда | `Отчет по лимитам и поддержке СЧП по ГФ на 01.08.26г.xlsx` |
| **Өрлеу**, **МТИ**, **зелёные проекты** | Отдельные программы | см. `--list` |

### Поля в нормализованной таблице

- `company_name` — название компании / ИП
- `legal_form` — ТОО, ИП и т.д.
- `project_name` — описание проекта
- `project_type` — Инвестиции / пополнение оборотных средств
- `oked_section`, `oked_division`, `oked_subclass`, `oked_code` — ОКЭД
- `region`, `district` — регион и район
- `bank` — банк-партнёр
- `business_size` — микро / малый / средний
- `credit_amount`, `guarantee_amount` — суммы
- `program`, `year`, `month` — программа и период
- `support_type` — subsidization / guarantee

## Дашборд

Интерактивный дашборд на **Streamlit** (не статическая HTML — ~125k записей слишком тяжёлы для одной HTML-страницы в браузере).

```bash
pip install -r requirements.txt
python3 -m damu_parser.cli --download --parse   # если данных ещё нет
streamlit run dashboard/app.py
```

Откроется в браузере (`http://localhost:8501`):
- фильтры: регион, ОКЭД, банк, программа, год, сумма
- графики: регионы, ОКЭД, динамика по годам
- детальная таблица с экспортом CSV

## Установка

```bash
pip install -r requirements.txt
```

## Использование

Список всех Excel-отчётов на сайте:

```bash
python -m damu_parser.cli --list
```

Скачать и распарсить основные отчёты:

```bash
python -m damu_parser.cli --download --parse
```

Результат: `data/processed/damu_projects.csv`, `damu_projects.json`, `summary.json`.

### Фильтрация

```bash
# Поиск по компании или проекту
python -m damu_parser.cli --parse --search "ForteBank" --limit 10

# По коду ОКЭД (префикс)
python -m damu_parser.cli --parse --oked "47"

# По региону
python -m damu_parser.cli --parse --region "Алмат"
```

### Парсинг локального файла

```bash
python -m damu_parser.cli --parse --files data/raw/Отчет\ по\ проектам\ субсидирования\ на\ 01.08.2026г.xlsx
```

## Ограничения

- Публичного API ДАМУ нет — только Excel/PDF на сайте.
- Не все Excel-файлы имеют единую структуру; парсер покрывает основные листы субсидирования и гарантирования.
- На [data.egov.kz](https://data.egov.kz) есть агрегированные данные по кредитам МСБ, но без названий компаний.
- Данные обновляются вручную на сайте ДАМУ (обычно раз в месяц).

## Ссылки

- [Отчёты ДАМУ](https://damu.kz/ru/reports/)
- [Аналитика ДАМУ](https://damu.kz/ru/poleznaya-informatsiya/damu_analytics/charts/)
