"""Подготовка данных для дашборда."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from damu_parser.cloud_bootstrap import bootstrap_data_from_damu, PARQUET_PATH as CLOUD_PARQUET

DEFAULT_DATA_DIR = Path("data/processed")
CSV_PATH = DEFAULT_DATA_DIR / "damu_projects.csv"
PARQUET_PATH = DEFAULT_DATA_DIR / "damu_projects.parquet"

DISPLAY_COLUMNS = [
    "company_name",
    "legal_form",
    "project_name",
    "project_type",
    "oked_code",
    "oked_division",
    "oked_subclass",
    "region",
    "district",
    "bank",
    "business_size",
    "credit_amount",
    "guarantee_amount",
    "program",
    "year",
    "month",
    "support_type",
    "source_file",
]

# Ключевые колонки для мобильного / краткого вида таблицы
MOBILE_DISPLAY_COLUMNS = [
    "company_name",
    "project_name",
    "oked_code",
    "region",
    "credit_amount",
    "program",
    "support_type",
]

COLUMN_LABELS = {
    "company_name": "Компания",
    "legal_form": "ОПФ",
    "project_name": "Проект",
    "project_type": "Цель кредита",
    "oked_code": "Код ОКЭД",
    "oked_division": "Раздел ОКЭД",
    "oked_subclass": "Подкласс ОКЭД",
    "region": "Регион",
    "district": "Район",
    "bank": "Банк",
    "business_size": "Размер бизнеса",
    "credit_amount": "Сумма кредита, ₸",
    "guarantee_amount": "Сумма гарантии, ₸",
    "program": "Программа",
    "year": "Год",
    "month": "Месяц",
    "support_type": "Тип поддержки",
    "source_file": "Источник",
}


def ensure_parquet(csv_path: Path = CSV_PATH, parquet_path: Path = PARQUET_PATH) -> Path:
    if parquet_path.exists() and csv_path.exists() and parquet_path.stat().st_mtime >= csv_path.stat().st_mtime:
        return parquet_path

    if not csv_path.exists():
        raise FileNotFoundError(f"Нет файла {csv_path}")

    df = pd.read_csv(csv_path, low_memory=False)
    numeric_cols = ["credit_amount", "guarantee_amount"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, index=False)
    return parquet_path


def load_projects(data_dir: Path = DEFAULT_DATA_DIR) -> pd.DataFrame:
    parquet_path = data_dir / "damu_projects.parquet"
    csv_path = data_dir / "damu_projects.csv"

    if parquet_path.exists():
        return pd.read_parquet(parquet_path)

    if csv_path.exists():
        ensure_parquet(csv_path, parquet_path)
        return pd.read_parquet(parquet_path)

    # Облако: скачать с damu.kz при первом запуске
    bootstrap_data_from_damu()
    return pd.read_parquet(CLOUD_PARQUET)


def format_amount(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.0f}".replace(",", " ")


def format_amount_compact(value: float | int | None) -> tuple[str, str]:
    """Короткий формат для метрик + полная сумма для подсказки."""
    if value is None or pd.isna(value):
        return "—", "—"

    v = float(value)
    full = f"{format_amount(v)} ₸"

    if abs(v) >= 1e12:
        short = f"{v / 1e12:.2f} трлн ₸".replace(".", ",")
    elif abs(v) >= 1e9:
        short = f"{v / 1e9:.2f} млрд ₸".replace(".", ",")
    elif abs(v) >= 1e6:
        short = f"{v / 1e6:.2f} млн ₸".replace(".", ",")
    else:
        short = full

    return short, full
