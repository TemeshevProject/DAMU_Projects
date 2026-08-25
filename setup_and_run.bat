@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==> 1/4 Проверка Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите с https://www.python.org/downloads/
    echo При установке отметьте "Add Python to PATH".
    pause
    exit /b 1
)

echo ==> 2/4 Установка зависимостей...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

echo ==> 3/4 Проверка данных...
if not exist "data\processed\damu_projects.csv" (
    echo     Данных нет — скачиваю отчёты с damu.kz (1-3 минуты)...
    set PYTHONPATH=%CD%
    python -m damu_parser.cli --download --parse
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось загрузить данные.
        pause
        exit /b 1
    )
) else (
    echo     data\processed\damu_projects.csv найден — пропускаю загрузку
)

echo ==> 4/4 Запуск дашборда на http://localhost:8501
echo     Остановка: Ctrl+C
set PYTHONPATH=%CD%
python -m streamlit run dashboard/app.py --browser.gatherUsageStats false
pause
