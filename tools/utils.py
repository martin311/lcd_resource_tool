from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ToolError(Exception):
    """Raised for expected user-facing command errors."""


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    if not path.exists():
        raise ToolError(f"Missing JSON file: {path}")
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise ToolError(f"Invalid JSON in {path}: {exc}") from exc


def require_dict(value: Any, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ToolError(f"Expected top-level JSON object in {path}")
    return value


def require_list_field(data: dict[str, Any], field: str, path: Path) -> list[Any]:
    value = data.get(field)
    if not isinstance(value, list):
        raise ToolError(f"Expected list field '{field}' in {path}")
    return value
