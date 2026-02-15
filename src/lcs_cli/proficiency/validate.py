from __future__ import annotations

from typing import Any

from .normalize import CEFR_ORDER, _target_range, _target_value, _is_number


def _registry_lookup(registry: dict[str, Any]) -> dict[str, Any]:
    frameworks = registry.get("frameworks", []) if isinstance(registry.get("frameworks"), list) else []
    by_id: dict[str, Any] = {}
    for fw in frameworks:
        if not isinstance(fw, dict):
            continue
        fid = str(fw.get("framework_id", "")).strip()
        if fid:
            by_id[fid] = fw
    return by_id


def _scale_by_id(framework: dict[str, Any]) -> dict[str, Any]:
    scales = framework.get("scales", []) if isinstance(framework.get("scales"), list) else []
    by_id: dict[str, Any] = {}
    for scale in scales:
        if not isinstance(scale, dict):
            continue
        sid = str(scale.get("scale_id", "")).strip()
        if sid:
            by_id[sid] = scale
    return by_id


def validate_proficiency_targets(
    brief: dict[str, Any],
    registry: dict[str, Any],
    crosswalks: dict[str, Any],
    subject: str,
) -> list[dict[str, Any]]:
    targets = brief.get("proficiency_targets", [])
    if not isinstance(targets, list) or not targets:
        return []

    issues: list[dict[str, Any]] = []
    frameworks = _registry_lookup(registry)

    for idx, item in enumerate(targets):
        if not isinstance(item, dict):
            issues.append(
                {
                    "code": "PROF_TARGET_INVALID",
                    "severity": "HIGH",
                    "message": f"proficiency_targets[{idx}] must be an object",
                }
            )
            continue

        framework_id = str(item.get("framework_id", "")).strip()
        scale_id = str(item.get("scale_id", "")).strip()
        dimension = str(item.get("dimension", "")).strip()

        if not framework_id or framework_id not in frameworks:
            issues.append(
                {
                    "code": "PROF_FRAMEWORK_UNKNOWN",
                    "severity": "HIGH",
                    "message": f"Unknown framework_id '{framework_id}' in proficiency_targets[{idx}]",
                    "details": {"framework_id": framework_id},
                }
            )
            continue

        framework = frameworks[framework_id]
        scales = _scale_by_id(framework)
        if not scale_id or scale_id not in scales:
            issues.append(
                {
                    "code": "PROF_SCALE_UNKNOWN",
                    "severity": "HIGH",
                    "message": f"Unknown scale_id '{scale_id}' for framework '{framework_id}'",
                    "details": {"framework_id": framework_id, "scale_id": scale_id},
                }
            )
            continue

        allowed_dims = framework.get("dimensions", [])
        if dimension and isinstance(allowed_dims, list):
            if dimension not in allowed_dims:
                issues.append(
                    {
                        "code": "PROF_DIMENSION_UNKNOWN",
                        "severity": "HIGH",
                        "message": f"Unknown dimension '{dimension}' for framework '{framework_id}'",
                        "details": {"framework_id": framework_id, "dimension": dimension},
                    }
                )

        scale = scales[scale_id]
        kind = str(scale.get("kind", "")).strip()
        target = item.get("target", {})
        if not isinstance(target, dict):
            issues.append(
                {
                    "code": "PROF_TARGET_INVALID",
                    "severity": "HIGH",
                    "message": f"proficiency_targets[{idx}].target must be an object",
                }
            )
            continue

        value = _target_value(target)
        rng = _target_range(target)

        if kind == "numeric":
            if value is not None:
                if not _is_number(value):
                    issues.append(
                        {
                            "code": "PROF_TARGET_TYPE_MISMATCH",
                            "severity": "HIGH",
                            "message": f"Numeric scale '{framework_id}/{scale_id}' requires numeric value",
                        }
                    )
                else:
                    mn = scale.get("min")
                    mx = scale.get("max")
                    if _is_number(mn) and _is_number(mx):
                        if float(value) < float(mn) or float(value) > float(mx):
                            issues.append(
                                {
                                    "code": "PROF_TARGET_OUT_OF_BOUNDS",
                                    "severity": "HIGH",
                                    "message": f"value {value} outside bounds [{mn}, {mx}] for '{framework_id}/{scale_id}'",
                                }
                            )
            elif rng is not None:
                rmin, rmax = rng
                if not (_is_number(rmin) and _is_number(rmax)):
                    issues.append(
                        {
                            "code": "PROF_TARGET_TYPE_MISMATCH",
                            "severity": "HIGH",
                            "message": f"Numeric scale '{framework_id}/{scale_id}' requires numeric min/max",
                        }
                    )
                else:
                    if float(rmax) < float(rmin):
                        issues.append(
                            {
                                "code": "PROF_TARGET_RANGE_INVALID",
                                "severity": "HIGH",
                                "message": f"Invalid range: max < min for '{framework_id}/{scale_id}'",
                            }
                        )
                    mn = scale.get("min")
                    mx = scale.get("max")
                    if _is_number(mn) and _is_number(mx):
                        if float(rmin) < float(mn) or float(rmax) > float(mx):
                            issues.append(
                                {
                                    "code": "PROF_TARGET_OUT_OF_BOUNDS",
                                    "severity": "HIGH",
                                    "message": f"range [{rmin}, {rmax}] outside bounds [{mn}, {mx}] for '{framework_id}/{scale_id}'",
                                }
                            )
            else:
                issues.append(
                    {
                        "code": "PROF_TARGET_MISSING",
                        "severity": "HIGH",
                        "message": f"Target must include value or min/max for '{framework_id}/{scale_id}'",
                    }
                )

        elif kind == "ordinal":
            if value is None or not isinstance(value, str):
                issues.append(
                    {
                        "code": "PROF_TARGET_TYPE_MISMATCH",
                        "severity": "HIGH",
                        "message": f"Ordinal scale '{framework_id}/{scale_id}' requires string value",
                    }
                )
            else:
                ordered = scale.get("ordered_values", [])
                if isinstance(ordered, list):
                    normalized = value.strip().upper()
                    if normalized not in [str(v).strip().upper() for v in ordered]:
                        issues.append(
                            {
                                "code": "PROF_TARGET_VALUE_UNKNOWN",
                                "severity": "HIGH",
                                "message": f"Unknown ordinal value '{value}' for '{framework_id}/{scale_id}'",
                                "details": {"allowed": ordered},
                            }
                        )

        else:
            issues.append(
                {
                    "code": "PROF_SCALE_KIND_UNKNOWN",
                    "severity": "HIGH",
                    "message": f"Unknown scale kind '{kind}' for '{framework_id}/{scale_id}'",
                }
            )

    # Crosswalk presence sanity: if user declares non-pivot targets, we should have at least one mapping table.
    if issues:
        return issues

    mappings = crosswalks.get("mappings", []) if isinstance(crosswalks.get("mappings"), list) else []
    if not mappings:
        issues.append(
            {
                "code": "PROF_CROSSWALK_MISSING",
                "severity": "HIGH",
                "message": "Crosswalk mappings are missing; cannot normalize proficiency targets",
            }
        )

    return issues

