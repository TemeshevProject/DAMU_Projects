"""Загрузка реестра ЮЛ (БИН) с data.egov.kz."""

from __future__ import annotations

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from damu_parser.name_utils import clean_bin_iin, normalize_name

REGISTRY_DIR = Path("data/registry")
GBD_RAW_PATH = REGISTRY_DIR / "gbd_ul_chunks.parquet"
GBD_INDEX_PATH = REGISTRY_DIR / "gbd_ul_index.parquet"

INDEX = "gbd_ul"
VERSION = "v1"
CHUNK_SIZE = 100
TOTAL_ESTIMATE = 991_168


def _fetch_chunk_curl(start: int) -> list[dict]:
    url = (
        f"https://data.egov.kz/datasets/exportjson?index={INDEX}&version={VERSION}"
        f"&from={start}&count={CHUNK_SIZE}"
    )
    for attempt in range(3):
        try:
            out = subprocess.check_output(
                ["curl", "-sL", "--max-time", "90", url],
                stderr=subprocess.DEVNULL,
            )
            data = json.loads(out)
            if isinstance(data, list):
                return data
        except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
            time.sleep(1 + attempt)
    return []


def download_registry(
    output: Path = GBD_RAW_PATH,
    max_chunks: int | None = None,
    workers: int = 12,
) -> Path:
    """Скачивает реестр gbd_ul пакетами и сохраняет parquet."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    total_chunks = (TOTAL_ESTIMATE + CHUNK_SIZE - 1) // CHUNK_SIZE
    if max_chunks:
        total_chunks = min(total_chunks, max_chunks)

    starts = [i * CHUNK_SIZE for i in range(total_chunks)]
    rows: list[dict] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_fetch_chunk_curl, start): start for start in starts}
        for fut in as_completed(futures):
            chunk = fut.result()
            for rec in chunk:
                bin_val = clean_bin_iin(rec.get("bin"))
                if not bin_val:
                    continue
                rows.append(
                    {
                        "bin": bin_val,
                        "nameru": rec.get("nameru"),
                        "name_norm": normalize_name(rec.get("nameru")),
                        "director": rec.get("director"),
                        "statusru": rec.get("statusru"),
                    }
                )

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("Реестр gbd_ul не загружен (0 записей). Проверьте доступ к data.egov.kz")
    df = df.drop_duplicates(subset=["bin"], keep="first")
    df.to_parquet(output, index=False)
    return output


def build_name_index(raw_path: Path = GBD_RAW_PATH, output: Path = GBD_INDEX_PATH) -> Path:
    df = pd.read_parquet(raw_path)
    if "name_norm" not in df.columns:
        df["name_norm"] = df["nameru"].map(normalize_name)
    df = df[df["name_norm"].astype(str).str.len() > 0]
    index = df.drop_duplicates(subset=["name_norm"], keep="first")[
        ["name_norm", "bin", "nameru", "director"]
    ]
    index.to_parquet(output, index=False)
    return output


def lookup_bin_by_code(code: str) -> dict | None:
    """Поиск по БИН через export (первые записи с совпадением)."""
    clean = clean_bin_iin(code)
    if not clean:
        return None
    # getdata через curl
    url = (
        "https://data.egov.kz/datasets/getdata?index=gbd_ul&version=v1"
        f"&page=1&count=5&text={clean}"
    )
    try:
        out = subprocess.check_output(
            [
                "curl", "-sL",
                "-H", "Referer: https://data.egov.kz/datasets/view?index=gbd_ul",
                url,
            ],
            stderr=subprocess.DEVNULL,
        )
        data = json.loads(out)
        for el in data.get("elements", []):
            if clean_bin_iin(el.get("bin")) == clean:
                return el
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None
    return None


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Download GBD UL registry from data.egov.kz")
    p.add_argument("--max-chunks", type=int, default=None, help="Limit chunks for testing")
    p.add_argument("--workers", type=int, default=16)
    args = p.parse_args()
    path = download_registry(max_chunks=args.max_chunks, workers=args.workers)
    idx = build_name_index(path)
    print(f"Saved {path}, index {idx}, rows {len(pd.read_parquet(idx))}")
