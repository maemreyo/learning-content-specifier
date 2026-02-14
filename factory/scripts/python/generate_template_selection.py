#!/usr/bin/env python3
"""Generate deterministic template blueprint/selection from unit artifacts."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


FORMULA_WEIGHTS = {
    "lo_fit": 0.35,
    "level_fit": 0.25,
    "duration_fit": 0.20,
    "diversity_fit": 0.20,
}

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

KEYWORD_HINTS = {
    "MCQ": ["multiple choice", "choose", "option", "vocabulary", "grammar", "mcq"],
    "TFNG": ["true", "false", "not given", "evidence", "passage", "statement", "reading"],
    "SENTENCE_REWRITE": ["rewrite", "rephrase", "transform", "sentence", "meaning", "paraphrase"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Factory repository root")
    parser.add_argument("--unit-dir", required=True, help="Unit directory under specs/")
    parser.add_argument("--template-pack-dir", help="Override template pack directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def resolve_template_pack_dir(repo_root: Path, override: str | None) -> Path | None:
    candidates: list[Path] = []
    if override:
        candidates.append(Path(override).expanduser())

    candidates.extend(
        [
            repo_root / ".lcs" / "template-pack" / "v1",
            repo_root / "subjects" / "english" / ".lcs" / "template-pack" / "v1",
            repo_root.parent / "subjects" / "english" / ".lcs" / "template-pack" / "v1",
        ]
    )

    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir():
            return resolved
    return None


def derive_contract_version(repo_root: Path) -> str:
    index = load_json(repo_root / "contracts" / "index.json")
    if isinstance(index, dict):
        version = str(index.get("contract_version", "")).strip()
        if version:
            return version
    return "1.0.0"


def derive_level(brief: dict[str, Any], design: dict[str, Any]) -> str:
    audience = brief.get("audience", {}) if isinstance(brief.get("audience"), dict) else {}
    entry = str(audience.get("entry_level", "")).strip().lower()
    if not entry:
        metadata = design.get("metadata", {}) if isinstance(design.get("metadata"), dict) else {}
        entry = str(metadata.get("audience", "")).strip().lower()

    if re.search(r"\bc2\b|expert", entry):
        return "C2"
    if re.search(r"\bc1\b|advanced", entry):
        return "C1"
    if re.search(r"\bb2\b|upper", entry):
        return "B2"
    if re.search(r"\bb1\b|intermediate", entry):
        return "B1"
    if re.search(r"\ba2\b|beginner", entry):
        return "A2"
    if re.search(r"\ba1\b", entry):
        return "A1"
    return "B1"


def level_fit_for_template(level: str, supported_levels: list[str]) -> float:
    normalized = [str(item).strip().upper() for item in supported_levels if isinstance(item, str)]
    if not normalized:
        return 0.75

    if level in normalized:
        return 1.0

    try:
        requested_idx = CEFR_ORDER.index(level)
        distances = [abs(CEFR_ORDER.index(item) - requested_idx) for item in normalized if item in CEFR_ORDER]
    except ValueError:
        return 0.7

    if not distances:
        return 0.7

    min_distance = min(distances)
    if min_distance == 1:
        return 0.85
    if min_distance == 2:
        return 0.7
    return 0.5


def extract_lo_text(brief: dict[str, Any]) -> str:
    chunks: list[str] = []
    outcomes = brief.get("learning_outcomes", [])
    if isinstance(outcomes, list):
        for item in outcomes:
            if not isinstance(item, dict):
                continue
            for key in ("statement", "evidence"):
                value = item.get(key)
                if isinstance(value, str):
                    chunks.append(value)
            criteria = item.get("acceptance_criteria", [])
            if isinstance(criteria, list):
                chunks.extend(str(c) for c in criteria if isinstance(c, str))
    return " ".join(chunks).lower()


def keyword_hits(text: str, exercise_type: str) -> int:
    hints = KEYWORD_HINTS.get(exercise_type.upper(), [])
    return sum(text.count(token) for token in hints)


def lo_fit_for_template(lo_text: str, templates: list[dict[str, Any]], target: dict[str, Any]) -> float:
    exercise_type = str(target.get("exercise_type", "")).upper()
    counts = [keyword_hits(lo_text, str(item.get("exercise_type", ""))) for item in templates]
    my_hits = keyword_hits(lo_text, exercise_type)

    max_hits = max(counts) if counts else 0
    if max_hits <= 0:
        return 0.8

    return round(0.6 + 0.4 * (my_hits / max_hits), 4)


def duration_fit_for_template(duration_minutes: int, lo_count: int, estimated_time: float) -> float:
    if duration_minutes <= 0:
        return 0.75

    ideal_per_item = max(duration_minutes / max(lo_count, 1) / 3.0, 1.0)
    drift = abs(estimated_time - ideal_per_item) / ideal_per_item
    return round(max(0.4, 1.0 - drift), 4)


def diversity_fit_for_template(template_id: str, existing_selection: dict[str, Any] | None) -> float:
    if not isinstance(existing_selection, dict):
        return 1.0

    selected = existing_selection.get("selected_templates", [])
    count = 0
    if isinstance(selected, list):
        for item in selected:
            if not isinstance(item, dict):
                continue
            if str(item.get("template_id", "")).strip().lower() == template_id:
                count += 1

    return round(max(0.4, 1.0 - 0.2 * count), 4)


def normalize_distribution(values: list[float]) -> list[int]:
    if not values:
        return []
    total = sum(values)
    if total <= 0:
        even = [100.0 / len(values)] * len(values)
        values = even
        total = 100.0

    raw = [value * 100.0 / total for value in values]
    rounded = [int(math.floor(value)) for value in raw]
    remaining = 100 - sum(rounded)
    if remaining > 0:
        fractions = sorted(
            [(raw[idx] - rounded[idx], idx) for idx in range(len(raw))],
            reverse=True,
        )
        for _, idx in fractions[:remaining]:
            rounded[idx] += 1
    return rounded


def build_rationale(score_breakdown: dict[str, float], exercise_type: str) -> str:
    best_key = max(score_breakdown, key=lambda item: score_breakdown[item])
    descriptions = {
        "lo_fit": "strong LO alignment",
        "level_fit": "good learner-level fit",
        "duration_fit": "time budget compatibility",
        "diversity_fit": "diversity contribution",
    }
    phrase = descriptions.get(best_key, "balanced fit")
    return f"Selected {exercise_type} due to {phrase} in weighted scoring."


def main() -> int:
    args = parse_args()

    repo_root = Path(args.repo_root).resolve()
    unit_dir = Path(args.unit_dir).resolve()
    if not unit_dir.is_dir():
        print(f"Unit directory not found: {unit_dir}", file=sys.stderr)
        return 1

    template_pack_dir = resolve_template_pack_dir(repo_root, args.template_pack_dir)
    if template_pack_dir is None:
        payload = {
            "STATUS": "SKIP",
            "REASON": "template-pack-not-found",
            "UNIT_DIR": str(unit_dir),
        }
        print(json.dumps(payload, separators=(",", ":")) if args.json else "Template pack not found; skipped selector")
        return 0

    catalog_path = template_pack_dir / "catalog.json"
    catalog = load_json(catalog_path)
    if not isinstance(catalog, dict):
        print(f"Invalid template catalog: {catalog_path}", file=sys.stderr)
        return 1

    templates = catalog.get("templates", [])
    if not isinstance(templates, list) or not templates:
        print(f"Template catalog has no templates: {catalog_path}", file=sys.stderr)
        return 1

    brief = load_json(unit_dir / "brief.json")
    design = load_json(unit_dir / "design.json")
    if not isinstance(brief, dict):
        brief = {}
    if not isinstance(design, dict):
        design = {}

    existing_selection = load_json(unit_dir / "template-selection.json")
    if not isinstance(existing_selection, dict):
        existing_selection = None

    level = derive_level(brief, design)
    duration_minutes = int(brief.get("duration_minutes", 60)) if isinstance(brief.get("duration_minutes", 60), int) else 60
    lo_text = extract_lo_text(brief)
    learning_outcomes = brief.get("learning_outcomes", []) if isinstance(brief.get("learning_outcomes"), list) else []
    lo_ids = [
        item.get("lo_id")
        for item in learning_outcomes
        if isinstance(item, dict) and isinstance(item.get("lo_id"), str)
    ]
    if not lo_ids:
        lo_ids = ["LO1"]

    ranked: list[dict[str, Any]] = []
    for item in templates:
        if not isinstance(item, dict):
            continue

        template_id = str(item.get("template_id", "")).strip().lower()
        exercise_type = str(item.get("exercise_type", "")).strip().upper()
        if not template_id or not exercise_type:
            continue

        estimated_time = float(item.get("estimated_time_minutes", 3))
        score_breakdown = {
            "lo_fit": lo_fit_for_template(lo_text, templates, item),
            "level_fit": level_fit_for_template(level, item.get("supported_levels", [])),
            "duration_fit": duration_fit_for_template(duration_minutes, len(lo_ids), estimated_time),
            "diversity_fit": diversity_fit_for_template(template_id, existing_selection),
        }

        score = 0.0
        for key, weight in FORMULA_WEIGHTS.items():
            score += weight * score_breakdown[key]

        ranked.append(
            {
                "template_id": template_id,
                "exercise_type": exercise_type,
                "score": round(score, 4),
                "score_breakdown": {k: round(v, 4) for k, v in score_breakdown.items()},
                "rationale": build_rationale(score_breakdown, exercise_type),
            }
        )

    ranked.sort(key=lambda value: (-value["score"], value["template_id"]))

    top_k = min(3, len(ranked))
    selected = ranked[:top_k]

    default_ratios: list[float] = []
    all_template_ids: list[str] = []
    all_exercise_types: list[str] = []
    for item in templates:
        if not isinstance(item, dict):
            continue
        template_id = str(item.get("template_id", "")).strip().lower()
        exercise_type = str(item.get("exercise_type", "")).strip().upper()
        if not template_id or not exercise_type:
            continue
        all_template_ids.append(template_id)
        all_exercise_types.append(exercise_type)
        value = item.get("default_ratio_percent")
        if isinstance(value, (int, float)):
            default_ratios.append(float(value))
        else:
            default_ratios.append(1.0)

    normalized = normalize_distribution(default_ratios)
    distribution = [
        {
            "template_id": all_template_ids[idx],
            "exercise_type": all_exercise_types[idx],
            "ratio_percent": normalized[idx],
        }
        for idx in range(len(all_template_ids))
    ]

    contract_version = derive_contract_version(repo_root)
    catalog_version = str(catalog.get("catalog_version", "1.0.0"))
    subject = str(catalog.get("subject", "english"))

    blueprint = {
        "contract_version": contract_version,
        "unit_id": unit_dir.name,
        "subject": subject,
        "template_pack_version": catalog_version,
        "target_distribution": distribution,
        "tolerance_percent": 10,
        "lo_mapping": {lo_id: [item["template_id"] for item in selected] for lo_id in lo_ids},
    }

    selection = {
        "contract_version": contract_version,
        "unit_id": unit_dir.name,
        "subject": subject,
        "catalog_version": catalog_version,
        "top_k": top_k,
        "selected_templates": selected,
        "selection_rationale": "Deterministic weighted auto-select from brief/design context.",
    }

    blueprint_path = unit_dir / "assessment-blueprint.json"
    selection_path = unit_dir / "template-selection.json"
    dump_json(blueprint_path, blueprint)
    dump_json(selection_path, selection)

    payload = {
        "STATUS": "PASS",
        "UNIT_DIR": str(unit_dir),
        "TEMPLATE_PACK_DIR": str(template_pack_dir),
        "ASSESSMENT_BLUEPRINT_FILE": str(blueprint_path),
        "TEMPLATE_SELECTION_FILE": str(selection_path),
        "TOP_K": top_k,
    }

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(f"STATUS: PASS")
        print(f"UNIT_DIR: {unit_dir}")
        print(f"TEMPLATE_PACK_DIR: {template_pack_dir}")
        print(f"ASSESSMENT_BLUEPRINT_FILE: {blueprint_path}")
        print(f"TEMPLATE_SELECTION_FILE: {selection_path}")
        print(f"TOP_K: {top_k}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
