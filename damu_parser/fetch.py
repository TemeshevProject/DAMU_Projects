"""Загрузка отчётов с сайта damu.kz."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup

from damu_parser.config import BASE_URL, DOWNLOAD_SKIP_SUBSTRINGS, REPORTS_PAGE, REPORT_TYPE_KEYWORDS


@dataclass
class ReportLink:
    url: str
    filename: str
    report_type: str
    size_kb: int | None = None


def classify_report(filename: str, url: str) -> str:
    text = f"{filename} {url}".lower()
    for report_type, keywords in REPORT_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return report_type
    return "other"


def fetch_report_links(page_url: str = REPORTS_PAGE) -> list[ReportLink]:
    response = requests.get(page_url, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links: list[ReportLink] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not href.lower().endswith(".xlsx"):
            continue

        full_url = urljoin(BASE_URL, href)
        if full_url in seen:
            continue
        seen.add(full_url)

        filename = unquote(Path(href).name)
        size_kb = None
        size_match = re.search(r"—\s*(\d+)\s*Кб", anchor.get_text(" ", strip=True))
        if size_match:
            size_kb = int(size_match.group(1))

        links.append(
            ReportLink(
                url=full_url,
                filename=filename,
                report_type=classify_report(filename, href),
                size_kb=size_kb,
            )
        )

    return links


def select_download_links(links: list[ReportLink], types: list[str]) -> list[ReportLink]:
    """Отбирает файлы для загрузки, исключая дубли однотипных отчётов."""
    selected: list[ReportLink] = []
    for report_type in types:
        type_links = [l for l in links if l.report_type == report_type and (l.size_kb or 0) > 0]
        if not type_links:
            continue

        skip_parts = DOWNLOAD_SKIP_SUBSTRINGS.get(report_type, [])
        filtered = [
            l for l in type_links
            if not any(part.lower() in l.filename.lower() for part in skip_parts)
        ]
        pool = filtered or type_links

        # Для субсидирования — самый большой файл (основной свод)
        if report_type == "subsidization":
            pool = sorted(pool, key=lambda l: l.size_kb or 0, reverse=True)[:1]
        else:
            pool = pool

        selected.extend(pool)
    return selected


def download_file(url: str, dest: Path, timeout: int = 120) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    dest.write_bytes(response.content)
    return dest
