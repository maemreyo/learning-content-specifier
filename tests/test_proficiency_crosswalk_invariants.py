import json
from pathlib import Path

import pytest

from lcs_cli.proficiency.normalize import normalize_targets_to_pivot


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _registry_by_id(registry: dict) -> dict[str, dict]:
    frameworks = registry.get("frameworks", []) if isinstance(registry.get("frameworks"), list) else []
    out: dict[str, dict] = {}
    for fw in frameworks:
        if isinstance(fw, dict) and fw.get("framework_id"):
            out[str(fw["framework_id"])] = fw
    return out


def _scale_by_id(framework: dict) -> dict[str, dict]:
    scales = framework.get("scales", []) if isinstance(framework.get("scales"), list) else []
    out: dict[str, dict] = {}
    for s in scales:
        if isinstance(s, dict) and s.get("scale_id"):
            out[str(s["scale_id"])] = s
    return out


def test_crosswalk_mappings_have_non_empty_provenance_source() -> None:
    crosswalks = _load(ROOT / "contracts" / "fixtures" / "proficiency.crosswalks.v1.json")
    mappings = crosswalks.get("mappings", [])
    assert isinstance(mappings, list) and mappings

    for idx, m in enumerate(mappings):
        assert isinstance(m, dict), f"mapping[{idx}] must be an object"
        source = m.get("source")
        assert isinstance(source, str) and source.strip(), f"mapping[{idx}] missing non-empty 'source'"


def test_crosswalks_reference_known_frameworks_scales_and_dimensions() -> None:
    registry = _load(ROOT / "contracts" / "fixtures" / "proficiency.framework-registry.v1.json")
    crosswalks = _load(ROOT / "contracts" / "fixtures" / "proficiency.crosswalks.v1.json")
    frameworks = _registry_by_id(registry)

    for idx, m in enumerate(crosswalks.get("mappings", [])):
        frm = m.get("from", {})
        to = m.get("to", {})
        assert isinstance(frm, dict) and isinstance(to, dict), f"mapping[{idx}] must have from/to objects"

        for side_name, side in (("from", frm), ("to", to)):
            fid = str(side.get("framework_id", "")).strip()
            sid = str(side.get("scale_id", "")).strip()
            dim = str(side.get("dimension", "")).strip()

            assert fid in frameworks, f"mapping[{idx}].{side_name}.framework_id unknown: {fid!r}"
            fw = frameworks[fid]
            scales = _scale_by_id(fw)
            assert sid in scales, f"mapping[{idx}].{side_name}.scale_id unknown: {fid}/{sid}"

            allowed_dims = fw.get("dimensions", [])
            assert isinstance(allowed_dims, list), f"registry framework {fid} must have dimensions[]"
            if dim:
                assert dim in allowed_dims, f"mapping[{idx}].{side_name}.dimension unknown: {fid}/{dim}"


def test_crosswalk_targets_match_scale_kinds_and_bounds() -> None:
    registry = _load(ROOT / "contracts" / "fixtures" / "proficiency.framework-registry.v1.json")
    crosswalks = _load(ROOT / "contracts" / "fixtures" / "proficiency.crosswalks.v1.json")
    frameworks = _registry_by_id(registry)

    for idx, m in enumerate(crosswalks.get("mappings", [])):
        frm = m["from"]
        to = m["to"]

        frm_fw = frameworks[str(frm["framework_id"])]
        to_fw = frameworks[str(to["framework_id"])]
        frm_scale = _scale_by_id(frm_fw)[str(frm["scale_id"])]
        to_scale = _scale_by_id(to_fw)[str(to["scale_id"])]

        frm_kind = str(frm_scale.get("kind", "")).strip()
        to_kind = str(to_scale.get("kind", "")).strip()

        frm_target = frm.get("target", {})
        to_target = to.get("target", {})
        assert isinstance(frm_target, dict), f"mapping[{idx}].from.target must be an object"
        assert isinstance(to_target, dict), f"mapping[{idx}].to.target must be an object"

        if frm_kind == "numeric":
            assert "min" in frm_target and "max" in frm_target, f"mapping[{idx}].from.target must have min/max"
            rmin, rmax = frm_target.get("min"), frm_target.get("max")
            assert _is_number(rmin) and _is_number(rmax), f"mapping[{idx}].from.target min/max must be numbers"
            assert float(rmin) <= float(rmax), f"mapping[{idx}].from.target invalid range (max < min)"
            if _is_number(frm_scale.get("min")) and _is_number(frm_scale.get("max")):
                mn, mx = float(frm_scale["min"]), float(frm_scale["max"])
                assert mn <= float(rmin) <= mx, f"mapping[{idx}].from.target.min out of bounds"
                assert mn <= float(rmax) <= mx, f"mapping[{idx}].from.target.max out of bounds"
        elif frm_kind == "ordinal":
            assert "value" in frm_target, f"mapping[{idx}].from.target must have value"
            v = frm_target.get("value")
            assert isinstance(v, str) and v.strip(), f"mapping[{idx}].from.target.value must be a string"
            allowed = frm_scale.get("ordered_values", [])
            assert isinstance(allowed, list) and allowed, "registry ordinal scale missing ordered_values"
            assert v.strip().upper() in [str(x).strip().upper() for x in allowed], f"mapping[{idx}].from.target.value invalid"
        else:
            pytest.fail(f"mapping[{idx}].from scale kind unsupported: {frm_kind!r}")

        if to_kind == "numeric":
            assert "min" in to_target and "max" in to_target, f"mapping[{idx}].to.target must have min/max"
            rmin, rmax = to_target.get("min"), to_target.get("max")
            assert _is_number(rmin) and _is_number(rmax), f"mapping[{idx}].to.target min/max must be numbers"
            assert float(rmin) <= float(rmax), f"mapping[{idx}].to.target invalid range (max < min)"
        elif to_kind == "ordinal":
            assert "value" in to_target, f"mapping[{idx}].to.target must have value"
            v = to_target.get("value")
            assert isinstance(v, str) and v.strip(), f"mapping[{idx}].to.target.value must be a string"
            allowed = to_scale.get("ordered_values", [])
            assert isinstance(allowed, list) and allowed, "registry ordinal scale missing ordered_values"
            assert v.strip().upper() in [str(x).strip().upper() for x in allowed], f"mapping[{idx}].to.target.value invalid"
        else:
            pytest.fail(f"mapping[{idx}].to scale kind unsupported: {to_kind!r}")


def test_numeric_crosswalk_ranges_do_not_overlap_per_source_group() -> None:
    registry = _load(ROOT / "contracts" / "fixtures" / "proficiency.framework-registry.v1.json")
    crosswalks = _load(ROOT / "contracts" / "fixtures" / "proficiency.crosswalks.v1.json")
    frameworks = _registry_by_id(registry)

    groups: dict[tuple[str, str, str], list[tuple[float, float, int]]] = {}

    for idx, m in enumerate(crosswalks.get("mappings", [])):
        frm = m["from"]
        fid = str(frm.get("framework_id", "")).strip()
        sid = str(frm.get("scale_id", "")).strip()
        dim = str(frm.get("dimension", "")).strip()

        fw = frameworks[fid]
        scale = _scale_by_id(fw)[sid]
        if str(scale.get("kind", "")).strip() != "numeric":
            continue

        t = frm.get("target", {})
        if not (isinstance(t, dict) and _is_number(t.get("min")) and _is_number(t.get("max"))):
            continue

        key = (fid, sid, dim)
        groups.setdefault(key, []).append((float(t["min"]), float(t["max"]), idx))

    assert groups, "expected at least one numeric mapping group"

    for key, ranges in groups.items():
        ranges = sorted(ranges, key=lambda x: (x[0], x[1], x[2]))
        prev_min, prev_max, prev_idx = ranges[0]
        assert prev_min <= prev_max, f"{key}: mapping[{prev_idx}] invalid range"
        for cur_min, cur_max, cur_idx in ranges[1:]:
            assert cur_min <= cur_max, f"{key}: mapping[{cur_idx}] invalid range"
            # Disallow overlaps and shared endpoints to keep mappings unambiguous.
            assert prev_max < cur_min, f"{key}: mapping[{prev_idx}] [{prev_min},{prev_max}] overlaps mapping[{cur_idx}] [{cur_min},{cur_max}]"
            prev_min, prev_max, prev_idx = cur_min, cur_max, cur_idx


def test_normalization_regressions_yield_non_empty_pivot_targets() -> None:
    pivots = _load(ROOT / "contracts" / "fixtures" / "proficiency.subject-pivots.v1.json")
    crosswalks = _load(ROOT / "contracts" / "fixtures" / "proficiency.crosswalks.v1.json")

    # IELTS speaking 7.5+ should map into CEFR pivot targets for English.
    brief_targets = [
        {
            "framework_id": "ielts.v1",
            "scale_id": "band",
            "dimension": "speaking",
            "target": {"min": 7.5, "max": 9.0},
        }
    ]
    out = normalize_targets_to_pivot(brief_targets, subject="english", pivots=pivots, crosswalks=crosswalks)
    assert out.get("pivot_framework_id") == "cefr.v1"
    assert out.get("pivot_targets"), "expected IELTS speaking target to normalize to non-empty pivot_targets"

    # TOEIC LR total should map into CEFR pivot targets for English.
    brief_targets = [
        {
            "framework_id": "toeic.v1",
            "scale_id": "lr_total",
            "dimension": "lr_total",
            "target": {"value": 800},
        }
    ]
    out = normalize_targets_to_pivot(brief_targets, subject="english", pivots=pivots, crosswalks=crosswalks)
    assert out.get("pivot_framework_id") == "cefr.v1"
    assert out.get("pivot_targets"), "expected TOEIC LR target to normalize to non-empty pivot_targets"

