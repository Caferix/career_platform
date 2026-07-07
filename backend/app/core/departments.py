from __future__ import annotations

from typing import Iterable


DEPARTMENT_LABELS: dict[str, str] = {
    "embedded": "Gömülü Sistemler",
    "backend": "Backend",
    "frontend": "Frontend",
    "security": "Siber Güvenlik",
    "infrastructure": "Sistem ve Altyapı",
    "product": "Ürün Yönetimi",
    "people_ops": "İnsan Kaynakları",
}

DEPARTMENT_ALIASES: dict[str, str] = {
    "embedded": "embedded",
    "gömülü sistemler": "embedded",
    "gomulu sistemler": "embedded",
    "backend": "backend",
    "backend developer": "backend",
    "frontend": "frontend",
    "frontend developer": "frontend",
    "security": "security",
    "siber güvenlik": "security",
    "siber guvenlik": "security",
    "infrastructure": "infrastructure",
    "sistem ve altyapı": "infrastructure",
    "sistem ve altyapi": "infrastructure",
    "product": "product",
    "ürün yönetimi": "product",
    "urun yonetimi": "product",
    "people_ops": "people_ops",
    "insan kaynakları": "people_ops",
    "insan kaynaklari": "people_ops",
}


def normalize_department(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    return DEPARTMENT_ALIASES.get(cleaned, cleaned)


def department_label(value: str | None) -> str:
    normalized = normalize_department(value)
    if not normalized:
        return "-"
    return DEPARTMENT_LABELS.get(normalized, value or "-")


def parse_departments(value: str | None) -> list[str]:
    if not value:
        return []

    parts = [item.strip() for item in value.split(",") if item.strip()]
    normalized = []
    for item in parts:
        code = normalize_department(item)
        if code and code not in normalized:
            normalized.append(code)
    return normalized


def expand_department_values(departments: Iterable[str]) -> list[str]:
    values: list[str] = []
    for department in departments:
        normalized = normalize_department(department)
        if not normalized:
            continue
        label = DEPARTMENT_LABELS.get(normalized)
        for candidate in (normalized, label, department):
            if candidate and candidate not in values:
                values.append(candidate)
    return values


def authorized_departments(token_data: dict) -> list[str]:
    departments = token_data.get("departments")
    if isinstance(departments, list):
        return [item for item in (normalize_department(value) for value in departments) if item]

    single_department = token_data.get("department")
    if single_department:
        return [department for department in parse_departments(single_department) if department]

    return []