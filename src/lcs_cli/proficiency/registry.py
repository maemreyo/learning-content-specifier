from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def load_framework_registry(repo_root: Path) -> dict[str, Any]:
    path = (repo_root / "contracts" / "fixtures" / "proficiency.framework-registry.v1.json").resolve()
    payload = _load_json(path)
    return payload if isinstance(payload, dict) else {}


def load_crosswalks(repo_root: Path) -> dict[str, Any]:
    path = (repo_root / "contracts" / "fixtures" / "proficiency.crosswalks.v1.json").resolve()
    payload = _load_json(path)
    return payload if isinstance(payload, dict) else {}


def load_subject_pivots(repo_root: Path) -> dict[str, Any]:
    path = (repo_root / "contracts" / "fixtures" / "proficiency.subject-pivots.v1.json").resolve()
    payload = _load_json(path)
    return payload if isinstance(payload, dict) else {}

