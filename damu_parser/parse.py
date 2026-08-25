"""Парсинг Excel-отчётов ДАМУ в единую таблицу."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from damu_parser.config import SHEET_PARSERS


def _normalize_columns(df: pd.DataFrame, column_map: dict[str, str]) -> pd.DataFrame:
    rename = {src: dst for src, dst in column_map.items() if src in df.columns}
    out = df.rename(columns=rename)
    for col in column_map.values():
        if col not in out.columns:
            out[col] = None
    return out[list(column_map.values())]


def _extract_oked_code(value: object) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if "-" in text:
        return text.split("-", 1)[0].strip()
    return text.split(" ", 1)[0].strip() if text else None


def parse_known_sheets(path: Path) -> list[pd.DataFrame]:
    xl = pd.ExcelFile(path)
    frames: list[pd.DataFrame] = []

    for parser_key, cfg in SHEET_PARSERS.items():
        for sheet_name in cfg["sheet_names"]:
            if sheet_name not in xl.sheet_names:
                continue

            df = pd.read_excel(
                xl,
                sheet_name=sheet_name,
                header=cfg["header_row"],
                dtype=str,
            )
            normalized = _normalize_columns(df, cfg["column_map"])
            normalized["support_type"] = cfg["support_type"]
            normalized["source_parser"] = parser_key
            normalized["source_file"] = path.name

            if "oked_division" in normalized.columns:
                normalized["oked_code"] = normalized["oked_division"].map(_extract_oked_code)
            elif "oked_subclass" in normalized.columns:
                normalized["oked_code"] = normalized["oked_subclass"].map(_extract_oked_code)
            else:
                normalized["oked_code"] = None

            normalized = normalized.dropna(how="all", subset=["company_name", "project_name"])
            frames.append(normalized)

    return frames


def parse_excel_file(path: Path) -> pd.DataFrame:
    frames = parse_known_sheets(path)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
