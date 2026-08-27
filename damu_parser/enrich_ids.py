"""Обогащение проектов ДАМУ полями БИН / ИИН."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from damu_parser.name_utils import clean_bin_iin, extract_person_key, is_valid_bin_iin, normalize_name
from damu_parser.registry import GBD_INDEX_PATH, build_name_index, download_registry

IP_FORMS = {"ИП", "ип"}


def _load_index(index_path: Path = GBD_INDEX_PATH) -> pd.DataFrame:
    if not index_path.exists():
        raise FileNotFoundError(
            f"Нет индекса реестра {index_path}. Запустите: python3 -m damu_parser.registry"
        )
    return pd.read_parquet(index_path)


def enrich_with_bin_iin(
    projects: pd.DataFrame,
    index_path: Path = GBD_INDEX_PATH,
) -> pd.DataFrame:
    index = _load_index(index_path)
    bin_by_name = dict(zip(index["name_norm"], index["bin"], strict=False))

    out = projects.copy()
    out["bin"] = None
    out["iin"] = None

    for idx, row in out.iterrows():
        company = row.get("company_name")
        legal = str(row.get("legal_form") or "").strip()
        norm = normalize_name(company)

        if legal.upper() in {x.upper() for x in IP_FORMS} or legal == "ИП":
            # ИИН в открытом реестре ЮЛ не публикуется — только если совпало имя с ЮЛ
            person = extract_person_key(company)
            if norm and norm in bin_by_name:
                out.at[idx, "bin"] = bin_by_name[norm]
            continue

        if norm and norm in bin_by_name:
            out.at[idx, "bin"] = bin_by_name[norm]
        else:
            # Частичное совпадение: имя DAMU содержится в названии реестра
            for name_norm, bin_val in bin_by_name.items():
                if len(norm) >= 4 and (norm in name_norm or name_norm in norm):
                    out.at[idx, "bin"] = bin_val
                    break

    # Для ИП: если БИН не найден, поле iin остаётся пустым (нужен реестр КГД)
    ip_mask = out["legal_form"].fillna("").str.upper().eq("ИП")
    out.loc[ip_mask & out["bin"].notna(), "iin"] = out.loc[ip_mask & out["bin"].notna(), "bin"]
    out.loc[ip_mask & out["bin"].notna(), "bin"] = None

    return out


def ensure_registry_index(max_chunks: int | None = None) -> Path:
    if GBD_INDEX_PATH.exists() and max_chunks is None:
        return GBD_INDEX_PATH
    if GBD_INDEX_PATH.exists() and max_chunks is not None:
        # Пересборка с расширенным реестром
        pass
    elif GBD_INDEX_PATH.exists():
        return GBD_INDEX_PATH
    raw = download_registry(max_chunks=max_chunks)
    return build_name_index(raw)


def build_enriched_parquet(
    projects_path: Path = Path("data/processed/damu_projects.parquet"),
    output_path: Path | None = None,
    max_registry_chunks: int | None = None,
) -> Path:
    ensure_registry_index(max_chunks=max_registry_chunks)
    df = pd.read_parquet(projects_path)
    enriched = enrich_with_bin_iin(df)
    out = output_path or projects_path
    enriched.to_parquet(out, index=False)
    csv_path = projects_path.with_suffix(".csv")
    enriched.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return out


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--max-chunks", type=int, default=200, help="Chunks of 100 records from gbd_ul")
    args = p.parse_args()
    path = build_enriched_parquet(max_registry_chunks=args.max_chunks)
    df = pd.read_parquet(path)
    print(f"Enriched {len(df)} rows, BIN filled: {df['bin'].notna().sum()}, IIN filled: {df['iin'].notna().sum()}")
