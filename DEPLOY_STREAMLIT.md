# Деплой на Streamlit Community Cloud

Публичная ссылка на дашборд — коллега открывает в браузере, **без Python и командной строки**.

## Шаг 1. Убедиться, что код на GitHub

Репозиторий: https://github.com/TemeshevProject/DAMU_Projects

Ветка **`main`** должна содержать:
- `streamlit_app.py`
- `requirements.txt`
- `data/processed/damu_projects.parquet` (~7 МБ)

## Шаг 2. Зарегистрироваться на Streamlit Cloud

1. Открой https://share.streamlit.io
2. Войди через **GitHub**
3. Разреши доступ к репозиторию `TemeshevProject/DAMU_Projects`

## Шаг 3. Создать приложение

1. **New app**
2. **Repository:** `TemeshevProject/DAMU_Projects`
3. **Branch:** `main`
4. **Main file path:** `streamlit_app.py`
5. **App URL** (опционально): например `damu-projects` → ссылка будет `https://damu-projects.streamlit.app`
6. **Deploy!**

Через 2–5 минут приложение будет доступно по ссылке.

## Шаг 4. Отправить ссылку

Пример: `https://damu-projects.streamlit.app`

Любой человек открывает в Chrome / Edge / Safari — дашборд работает.

## Обновление данных

1. Локально: `python3 -m damu_parser.cli --download --parse`
2. Закоммить обновлённый `data/processed/damu_projects.parquet`
3. Push в `main` — Streamlit Cloud пересоберёт приложение автоматически

Если parquet не в репозитории, при первом открытии приложение само скачает отчёты с damu.kz (~1–2 мин).

## Лимиты бесплатного тарифа

- Публичный репозиторий на GitHub
- Приложение «спит» при неактивности — первое открытие после сна ~30 сек
- Для закрытых репозиториев нужен Streamlit Teams

## Локальный запуск (для себя)

```bat
setup_and_run.bat
```

→ http://localhost:8501
