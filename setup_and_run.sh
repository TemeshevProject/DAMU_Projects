#!/usr/bin/env bash
# Полная установка и запуск дашборда ДАМУ одной командой
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 1/4 Установка зависимостей..."
python3 -m pip install -q -r requirements.txt

echo "==> 2/4 Проверка данных..."
if [[ ! -f data/processed/damu_projects.csv ]]; then
  echo "    Данных нет — скачиваю отчёты с damu.kz (это займёт 1–3 минуты)..."
  export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
  python3 -m damu_parser.cli --download --parse
else
  echo "    data/processed/damu_projects.csv найден — пропускаю загрузку"
fi

echo "==> 3/4 Подготовка кэша..."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
python3 -c "from dashboard.data import ensure_parquet; ensure_parquet(); print('OK')"

echo "==> 4/4 Запуск дашборда на http://localhost:8501"
echo "    Остановка: Ctrl+C"
exec ./run_dashboard.sh
