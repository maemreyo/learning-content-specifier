from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _target_value(target: dict[str, Any]) -> str | float | int | None:
    if not isinstance(target, dict):
        return None
    if "value" in target:
        return target.get("value")
    return None


def _target_range(target: dict[str, Any]) -> tuple[Any, Any] | None:
    if not isinstance(target, dict):
        return None
    if "min" in target and "max" in target:
        return (target.get("min"), target.get("max"))
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _range_contains(value: float, min_v: float, max_v: float) -> bool:
    return min_v <= value <= max_v


def _ranges_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> bool:
    return not (a_max < b_min or b_max < a_min)


def _normalize_cefr_values(values: list[str]) -> dict[str, Any]:
    normalized = [v.strip().upper() for v in values if isinstance(v, str) and v.strip()]
    normalized = [v for v in normalized if v in CEFR_ORDER]
    if not normalized:
        return {}
    if len(set(normalized)) == 1:
        return {"value": normalized[0]}
    indices = sorted(CEFR_ORDER.index(v) for v in set(normalized))
    return {"min": CEFR_ORDER[indices[0]], "max": CEFR_ORDER[indices[-1]]}


def normalize_targets_to_pivot(
    brief_targets: list[dict[str, Any]],
    subject: str,
    pivots: dict[str, Any],
    crosswalks: dict[str, Any],
) -> dict[str, Any]:
    pivot_map = pivots.get("subject_pivots", {}) if isinstance(pivots.get("subject_pivots"), dict) else {}
    pivot_framework_id = str(pivot_map.get(subject, "")).strip()

    requested_modalities: set[str] = set()
    for item in brief_targets:
        if not isinstance(item, dict):
            continue
        dim = str(item.get("dimension", "")).strip().lower()
        if dim in {"speaking", "writing", "reading", "listening"}:
            requested_modalities.add(dim)
        tags = item.get("domain_tags", [])
        if isinstance(tags, list):
            for tag in tags:
                t = str(tag).strip().lower()
                if t in {"speaking", "writing", "reading", "listening"}:
                    requested_modalities.add(t)

    pivot_targets: list[dict[str, Any]] = []
    unmapped: list[dict[str, Any]] = []

    if not pivot_framework_id:
        return {
            "pivot_framework_id": "",
            "pivot_targets": [],
            "unmapped_targets": [t for t in brief_targets if isinstance(t, dict)],
            "requested_modalities": sorted(requested_modalities),
        }

    mappings = crosswalks.get("mappings", []) if isinstance(crosswalks.get("mappings"), list) else []

    for target in brief_targets:
        if not isinstance(target, dict):
            continue

        framework_id = str(target.get("framework_id", "")).strip()
        scale_id = str(target.get("scale_id", "")).strip()
        dimension = str(target.get("dimension", "")).strip()
        t_value = _target_value(target.get("target", {}))
        t_range = _target_range(target.get("target", {}))

        # If already expressed in pivot framework, keep it.
        if framework_id == pivot_framework_id:
            pivot_targets.append(
                {
                    "framework_id": framework_id,
                    "scale_id": scale_id,
                    "dimension": dimension,
                    "target": target.get("target", {}),
                    "source_target": target,
                }
            )
            continue

        matched_cefr_values: list[str] = []

        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            frm = mapping.get("from", {})
            to = mapping.get("to", {})
            if not isinstance(frm, dict) or not isinstance(to, dict):
                continue

            if str(to.get("framework_id", "")).strip() != pivot_framework_id:
                continue
            if str(frm.get("framework_id", "")).strip() != framework_id:
                continue
            if str(frm.get("scale_id", "")).strip() != scale_id:
                continue

            map_dim = str(frm.get("dimension", "")).strip()
            if dimension and map_dim and dimension != map_dim:
                continue
            if not dimension and map_dim:
                # If target is dimensionless, accept only dimensionless mappings.
                continue

            frm_target = frm.get("target", {})
            if not isinstance(frm_target, dict):
                continue

            frm_val = _target_value(frm_target)
            frm_rng = _target_range(frm_target)
            # We only support numeric ranges for V1 mappings.
            if frm_val is not None:
                continue
            if frm_rng is None:
                continue

            frm_min, frm_max = frm_rng
            if not (_is_number(frm_min) and _is_number(frm_max)):
                continue

            intersects = False
            if t_value is not None and _is_number(t_value):
                intersects = _range_contains(float(t_value), float(frm_min), float(frm_max))
            elif t_range is not None:
                t_min, t_max = t_range
                if _is_number(t_min) and _is_number(t_max):
                    intersects = _ranges_overlap(float(t_min), float(t_max), float(frm_min), float(frm_max))

            if not intersects:
                continue

            to_target = to.get("target", {})
            if not isinstance(to_target, dict):
                continue
            cefr_value = _target_value(to_target)
            if isinstance(cefr_value, str) and cefr_value.strip().upper() in CEFR_ORDER:
                matched_cefr_values.append(cefr_value.strip().upper())

        if matched_cefr_values:
            pivot_targets.append(
                {
                    "framework_id": pivot_framework_id,
                    "scale_id": "global",
                    "dimension": "global",
                    "target": _normalize_cefr_values(matched_cefr_values),
                    "source_target": target,
                }
            )
        else:
            unmapped.append(target)

    return {
        "pivot_framework_id": pivot_framework_id,
        "pivot_targets": pivot_targets,
        "unmapped_targets": unmapped,
        "requested_modalities": sorted(requested_modalities),
    }

