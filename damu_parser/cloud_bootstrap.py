"""Автозагрузка данных для облачного деплоя (Streamlit Cloud)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from damu_parser.fetch import download_file, fetch_report_links, select_download_links
from damu_parser.parse import parse_excel_file

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PARQUET_PATH = PROCESSED_DIR / "damu_projects.parquet"
CSV_PATH = PROCESSED_DIR / "damu_projects.csv"

DEDUPE_COLS = [
    "company_name",
    "project_name",
    "credit_amount",
    "guarantee_amount",
    "program",
    "year",
    "support_type",
    "bank",
]


def bootstrap_data_from_damu(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    report_types: list[str] | None = None,
) -> Path:
    """Скачивает отчёты с damu.kz, парсит и сохраняет parquet."""
    types = report_types or ["subsidization", "guarantee"]
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    links = select_download_links(fetch_report_links(), types)
    if not links:
        raise RuntimeError("Не найдены отчёты на damu.kz")

    frames: list[pd.DataFrame] = []
    for link in links:
        dest = raw_dir / link.filename
        if not dest.exists():
            download_file(link.url, dest)
        df = parse_excel_file(dest)
        if not df.empty:
            frames.append(df)

    if not frames:
        raise RuntimeError("Не удалось распарсить отчёты ДАМУ")

    result = pd.concat(frames, ignore_index=True)
    dedupe_cols = [c for c in DEDUPE_COLS if c in result.columns]
    result = result.drop_duplicates(subset=dedupe_cols, keep="first")

    for col in ["credit_amount", "guarantee_amount"]:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")
    if "year" in result.columns:
        result["year"] = pd.to_numeric(result["year"], errors="coerce").astype("Int64")

    result.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    result.to_parquet(PARQUET_PATH, index=False)
    return PARQUET_PATH
