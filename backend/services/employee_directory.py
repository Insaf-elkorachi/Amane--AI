import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any


EMPLOYEES_PATH = Path(__file__).resolve().parents[1] / "knowledge" / "employees_sonasid.json"


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


class EmployeeDirectory:
    @staticmethod
    @lru_cache(maxsize=1)
    def _employees() -> list[dict[str, str]]:
        if not EMPLOYEES_PATH.exists():
            return []
        return json.loads(EMPLOYEES_PATH.read_text(encoding="utf-8"))

    def find_by_matricule(self, value: str) -> dict[str, str] | None:
        normalized = _normalize(value)
        match = re.search(r"\b(?:matricule|mat|numero|num|n)?\s*(\d{2,8})\b", normalized)
        if not match:
            return None

        matricule = match.group(1).lstrip("0") or "0"
        for employee in self._employees():
            if str(employee.get("matricule", "")).lstrip("0") == matricule:
                return employee
        return None

    def find_by_name(self, value: str) -> dict[str, str] | None:
        normalized = _normalize(value)
        if len(normalized) < 4:
            return None

        for employee in self._employees():
            full_name = _normalize(employee.get("display_name", ""))
            reverse_name = _normalize(f"{employee.get('nom', '')} {employee.get('prenom', '')}")
            if normalized in {full_name, reverse_name}:
                return employee
        return None


employee_directory = EmployeeDirectory()
