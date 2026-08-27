"""Нормализация названий для сопоставления с реестром."""

from __future__ import annotations

import re

LEGAL_PREFIXES = (
    "товарищество с ограниченной ответственностью",
    "товарищество с дополнительной ответственностью",
    "акционерное общество",
    "крестьянское хозяйство",
    "фермерское хозяйство",
    "индивидуальный предприниматель",
    "частное предприятие",
    "производственный кооператив",
    "товарищество собственников жилья",
    "товарищество собственников недвижимости",
    "товарищество собственников поквартирного дома",
    "товарищество собственников имущества",
    "товарищество собственников",
    "жек",
    "жк",
    "тоо",
    "ао",
    "ип",
    "кх",
    "фх",
    "жшс",
    "пт",
    "кт",
    "спк",
    "пк",
)


def _strip_legal_forms(text: str) -> str:
    t = text.lower().strip()
    for prefix in LEGAL_PREFIXES:
        if t.startswith(prefix):
            t = t[len(prefix):].strip(" \"'«»")
    return t


def normalize_name(name: str | None) -> str:
    if not name or not str(name).strip():
        return ""
    text = str(name).strip()
    text = text.replace("«", '"').replace("»", '"')
    # Короткое имя в кавычках: ТОО "Снэк KZ"
    quoted = re.findall(r'"([^"]+)"', text)
    if quoted:
        text = quoted[0]
    else:
        text = _strip_legal_forms(text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\-&.]", "", text, flags=re.UNICODE)
    return text.strip().lower()


def extract_person_key(name: str | None) -> str:
    """Ключ для ИП: фамилия из 'Аскарова М.М.' или текста до 'в лице'."""
    if not name:
        return ""
    text = str(name).split("в лице")[0].strip()
    text = re.sub(r'^["\'\s]+|["\'\s]+$', "", text)
    parts = re.split(r"\s+", text)
    if not parts:
        return ""
    return parts[0].lower().replace(".", "")


def is_valid_bin_iin(value: str | None) -> bool:
    if not value:
        return False
    digits = re.sub(r"\D", "", str(value))
    return len(digits) == 12


def clean_bin_iin(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits if len(digits) == 12 else None
