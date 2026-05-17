from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_config(config_path: Path, journals_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = load_yaml(config_path)
    journals_doc = load_yaml(journals_path)
    journals = journals_doc.get("journals", [])
    if not isinstance(journals, list) or not journals:
        raise ValueError("journals.yaml must contain a non-empty 'journals' list")
    return config, journals


def deep_get(mapping: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
