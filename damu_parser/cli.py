"""CLI для загрузки и парсинга отчётов ДАМУ."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from damu_parser.fetch import download_file, fetch_report_links, select_download_links
from damu_parser.parse import parse_excel_file


def _print_links(links: list) -> None:
    by_type: dict[str, list] = {}
    for link in links:
        by_type.setdefault(link.report_type, []).append(link)

    for report_type, items in sorted(by_type.items()):
        print(f"\n=== {report_type} ({len(items)} файлов) ===")
        for item in items:
            size = f"{item.size_kb} Кб" if item.size_kb else "размер неизвестен"
            print(f"  - {item.filename} ({size})")
            print(f"    {item.url}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Загрузка и парсинг открытых отчётов Фонда ДАМУ (damu.kz)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Показать доступные Excel-отчёты на damu.kz",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Скачать отчёты (по умолчанию: subsidization и guarantee)",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=["subsidization", "guarantee"],
        help="Типы отчётов для загрузки: subsidization, guarantee, orleu, manufacturing, green, other",
    )
    parser.add_argument(
        "--parse",
        action="store_true",
        help="Парсить скачанные/указанные Excel-файлы",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw"),
        help="Папка для сырых Excel-файлов",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Папка для результатов (CSV/JSON)",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Конкретные Excel-файлы для парсинга (пути)",
    )
    parser.add_argument(
        "--search",
        help="Фильтр по названию компании или проекта (подстрока, без учёта регистра)",
    )
    parser.add_argument(
        "--oked",
        help="Фильтр по коду ОКЭД (начинается с указанного префикса)",
    )
    parser.add_argument(
        "--region",
        help="Фильтр по региону (подстрока)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Сколько строк показать в превью (0 = не показывать)",
    )

    args = parser.parse_args()

    if args.list:
        links = fetch_report_links()
        _print_links(links)
        return

    files_to_parse: list[Path] = []

    if args.download:
        links = fetch_report_links()
        selected = select_download_links(links, args.types)
        args.input_dir.mkdir(parents=True, exist_ok=True)

        print(f"Скачиваю {len(selected)} файлов в {args.input_dir}...")
        for link in selected:
            dest = args.input_dir / link.filename
            if dest.exists():
                print(f"  уже есть: {link.filename}")
            else:
                print(f"  загрузка: {link.filename}")
                download_file(link.url, dest)
            files_to_parse.append(dest)

    if args.files:
        files_to_parse.extend(Path(f) for f in args.files)

    if args.parse or args.files:
        if not files_to_parse:
            if args.input_dir.exists():
                files_to_parse = sorted(args.input_dir.glob("*.xlsx"))
            else:
                parser.error("Нет файлов для парсинга. Используйте --download или --files")

        all_frames: list[pd.DataFrame] = []
        for path in files_to_parse:
            if not path.exists():
                print(f"Пропуск (не найден): {path}")
                continue
            print(f"Парсинг: {path.name}")
            df = parse_excel_file(path)
            if df.empty:
                print(f"  нет распознанных листов в {path.name}")
            else:
                print(f"  строк: {len(df)}")
                all_frames.append(df)

        if not all_frames:
            print("Нет данных после парсинга.")
            return

        result = pd.concat(all_frames, ignore_index=True)

        dedupe_cols = [
            c for c in [
                "company_name",
                "project_name",
                "credit_amount",
                "guarantee_amount",
                "program",
                "year",
                "support_type",
                "bank",
            ]
            if c in result.columns
        ]
        before = len(result)
        result = result.drop_duplicates(subset=dedupe_cols, keep="first")
        if before != len(result):
            print(f"Удалено дублей: {before - len(result)}")

        if args.search:
            mask = (
                result["company_name"].fillna("").str.contains(args.search, case=False, na=False)
                | result["project_name"].fillna("").str.contains(args.search, case=False, na=False)
            )
            result = result[mask]

        if args.oked:
            result = result[result["oked_code"].fillna("").str.startswith(args.oked)]

        if args.region:
            result = result[
                result["region"].fillna("").str.contains(args.region, case=False, na=False)
            ]

        args.output_dir.mkdir(parents=True, exist_ok=True)
        csv_path = args.output_dir / "damu_projects.csv"
        json_path = args.output_dir / "damu_projects.json"

        result.to_csv(csv_path, index=False, encoding="utf-8-sig")
        result.to_json(json_path, orient="records", force_ascii=False, indent=2)

        print(f"\nИтого записей: {len(result)}")
        print(f"CSV: {csv_path}")
        print(f"JSON: {json_path}")

        if args.limit > 0 and len(result) > 0:
            preview_cols = [
                c for c in [
                    "company_name",
                    "project_name",
                    "oked_code",
                    "oked_division",
                    "region",
                    "credit_amount",
                    "support_type",
                    "program",
                ]
                if c in result.columns
            ]
            print("\nПревью:")
            print(result[preview_cols].head(args.limit).to_string(index=False))

        summary = {
            "total_records": len(result),
            "by_support_type": result["support_type"].value_counts().to_dict(),
            "by_program": result["program"].value_counts().head(10).to_dict(),
            "top_oked": result["oked_code"].value_counts().head(10).to_dict(),
        }
        summary_path = args.output_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Сводка: {summary_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
