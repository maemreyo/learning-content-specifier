#!/usr/bin/env python3
"""Manage active program/unit context for LCS agents.

Supports listing programs, recommending a target from intent, and activating
program/unit context deterministically.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TIMESTAMP_SUFFIX = re.compile(r"-\d{8}-\d{4}(?:-\d{2})?$")
UNIT_SLOT_PATTERN = re.compile(r"^(\d{3})-")
DESIGN_REQUIRED_FILES = (
    "design.md",
    "design.json",
    "content-model.md",
    "content-model.json",
    "exercise-design.md",
    "exercise-design.json",
    "assessment-map.md",
    "delivery-guide.md",
    "design-decisions.json",
    "assessment-blueprint.json",
    "template-selection.json",
    "outputs/manifest.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "current", "recommend", "activate", "list-units", "workflow-status"])
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--program", help="Program id (or slug-like hint)")
    parser.add_argument("--unit", help="Unit id to activate or inspect")
    parser.add_argument("--intent", help="Natural-language program intent for recommendation")
    parser.add_argument("--clear-unit", action="store_true", help="Clear current unit when activating a program")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return slug[:40]


def program_base_slug(program_id: str) -> str:
    return TIMESTAMP_SUFFIX.sub("", program_id)


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_context(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def write_context(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def resolve_current_program(repo_root: Path, context_program_file: Path) -> str:
    _ = repo_root
    env_program = os.environ.get("LCS_PROGRAM", "").strip()
    if env_program:
        return env_program
    from_context = read_context(context_program_file)
    if from_context:
        return from_context
    return ""


def resolve_current_unit(context_unit_file: Path) -> str:
    env_unit = os.environ.get("LCS_UNIT", "").strip()
    if env_unit:
        return env_unit
    return read_context(context_unit_file)


@dataclass(frozen=True)
class RepoState:
    repo_root: Path
    programs_root: Path
    context_program_file: Path
    context_unit_file: Path


def discover_state(repo_root: Path) -> RepoState:
    repo_root = repo_root.resolve()
    return RepoState(
        repo_root=repo_root,
        programs_root=repo_root / "programs",
        context_program_file=repo_root / ".lcs" / "context" / "current-program",
        context_unit_file=repo_root / ".lcs" / "context" / "current-unit",
    )


def unit_entries(program_dir: Path, active_unit: str) -> list[dict[str, Any]]:
    units_dir = program_dir / "units"
    entries: list[dict[str, Any]] = []
    if not units_dir.exists():
        return entries

    for path in sorted(units_dir.iterdir()):
        if not path.is_dir():
            continue
        slot = 0
        match = UNIT_SLOT_PATTERN.match(path.name)
        if match:
            slot = int(match.group(1))
        entries.append(
            {
                "unit_id": path.name,
                "slot": slot,
                "is_active": path.name == active_unit,
                "has_brief": (path / "brief.md").is_file(),
                "has_design": (path / "design.md").is_file(),
                "has_sequence": (path / "sequence.md").is_file(),
                "has_manifest": (path / "outputs" / "manifest.json").is_file(),
            }
        )
    return entries


def count_open_questions(brief_payload: dict[str, Any]) -> int:
    count = 0
    value = brief_payload.get("open_questions")
    if isinstance(value, int) and value > 0:
        count = max(count, value)

    refinement = brief_payload.get("refinement")
    if isinstance(refinement, dict):
        ref_open = refinement.get("open_questions")
        if isinstance(ref_open, int) and ref_open > 0:
            count = max(count, ref_open)
    return count


def unit_workflow_status(program_id: str, unit_dir: Path, active_unit: str) -> dict[str, Any]:
    unit_id = unit_dir.name
    brief_md = unit_dir / "brief.md"
    brief_json_file = unit_dir / "brief.json"
    sequence_md = unit_dir / "sequence.md"
    sequence_json = unit_dir / "sequence.json"
    rubric_dir = unit_dir / "rubrics"
    audit_md = unit_dir / "audit-report.md"
    audit_json = unit_dir / "audit-report.json"
    manifest_file = unit_dir / "outputs" / "manifest.json"

    brief_payload = read_json(brief_json_file)
    open_questions = count_open_questions(brief_payload)
    refine_complete = brief_json_file.is_file() and open_questions == 0

    missing_design_files = [name for name in DESIGN_REQUIRED_FILES if not (unit_dir / name).is_file()]
    design_complete = len(missing_design_files) == 0

    sequence_complete = sequence_md.is_file() and sequence_json.is_file()
    rubric_complete = rubric_dir.is_dir() and any(path.is_file() for path in rubric_dir.rglob("*"))
    audit_complete = audit_md.is_file() and audit_json.is_file()

    manifest_payload = read_json(manifest_file) if manifest_file.is_file() else {}
    gate_status = manifest_payload.get("gate_status", {}) if isinstance(manifest_payload, dict) else {}
    gate_decision = ""
    if isinstance(gate_status, dict):
        raw_decision = gate_status.get("decision", "")
        if isinstance(raw_decision, str):
            gate_decision = raw_decision.upper()

    if not brief_md.is_file() and not brief_json_file.is_file():
        stage = "define"
        prompt = f"/lcs.define Define unit {unit_id}"
        reason = "Unit brief is missing."
    elif not refine_complete:
        stage = "refine"
        prompt = f"/lcs.refine Refine unit {unit_id} and close open questions."
        reason = f"Refinement open questions: {open_questions}."
    elif not design_complete:
        stage = "design"
        prompt = f"/lcs.design Generate design artifacts for unit {unit_id}."
        reason = f"Missing design artifacts: {', '.join(missing_design_files[:4])}" + ("..." if len(missing_design_files) > 4 else "")
    elif not sequence_complete:
        stage = "sequence"
        prompt = f"/lcs.sequence Build production sequence for unit {unit_id}."
        reason = "Sequence artifacts are incomplete."
    elif not rubric_complete:
        stage = "rubric"
        prompt = f"/lcs.rubric Generate rubric gates for unit {unit_id}."
        reason = "Rubric artifacts are missing."
    elif not audit_complete or gate_decision in {"", "BLOCK"}:
        stage = "audit"
        prompt = f"/lcs.audit Run quality audit for unit {unit_id}."
        reason = "Audit is missing or gate decision is BLOCK."
    else:
        stage = "author"
        prompt = f"/lcs.author Author output artifacts for unit {unit_id}."
        reason = "Unit has passed upstream gates and is ready for authoring."

    activate_prompt = f"/lcs.programs activate --program {program_id} --unit {unit_id}"
    redesign_prompt = f"/lcs.redesign Rebuild design for unit {unit_id} with reset."

    return {
        "unit_id": unit_id,
        "slot": int(UNIT_SLOT_PATTERN.match(unit_id).group(1)) if UNIT_SLOT_PATTERN.match(unit_id) else 0,
        "is_active": unit_id == active_unit,
        "status": {
            "has_brief": brief_md.is_file() and brief_json_file.is_file(),
            "open_questions": open_questions,
            "refine_complete": refine_complete,
            "design_complete": design_complete,
            "missing_design_files": missing_design_files,
            "sequence_complete": sequence_complete,
            "rubric_complete": rubric_complete,
            "audit_complete": audit_complete,
            "gate_decision": gate_decision or "UNKNOWN",
        },
        "next_stage": stage,
        "next_reason": reason,
        "recommended_prompts": [activate_prompt, prompt, redesign_prompt if stage in {"sequence", "rubric", "audit", "author"} else ""],
    }


def workflow_status(state: RepoState, program_id: str, current_program: str, current_unit: str) -> dict[str, Any]:
    program_dir = state.programs_root / program_id
    if not program_dir.is_dir():
        raise ValueError(f"Program directory not found: {program_dir}")

    effective_active_unit = current_unit if program_id == current_program else ""
    unit_statuses = [
        unit_workflow_status(program_id, path, effective_active_unit)
        for path in sorted((program_dir / "units").iterdir())
        if path.is_dir()
    ] if (program_dir / "units").is_dir() else []

    for item in unit_statuses:
        item["recommended_prompts"] = [cmd for cmd in item["recommended_prompts"] if cmd]

    pending = list(unit_statuses)
    top_follow_ups: list[dict[str, str]] = []
    for item in pending[:5]:
        first = item["recommended_prompts"][0] if item["recommended_prompts"] else ""
        second = item["recommended_prompts"][1] if len(item["recommended_prompts"]) > 1 else ""
        if first:
            top_follow_ups.append({"unit_id": item["unit_id"], "command": first, "reason": "Activate target unit context."})
        if second:
            top_follow_ups.append({"unit_id": item["unit_id"], "command": second, "reason": item["next_reason"]})

    summary = {
        "total_units": len(unit_statuses),
        "define_pending": sum(1 for item in unit_statuses if item["next_stage"] == "define"),
        "refine_pending": sum(1 for item in unit_statuses if item["next_stage"] == "refine"),
        "design_pending": sum(1 for item in unit_statuses if item["next_stage"] == "design"),
        "sequence_pending": sum(1 for item in unit_statuses if item["next_stage"] == "sequence"),
        "rubric_pending": sum(1 for item in unit_statuses if item["next_stage"] == "rubric"),
        "audit_pending": sum(1 for item in unit_statuses if item["next_stage"] == "audit"),
        "author_ready": sum(1 for item in unit_statuses if item["next_stage"] == "author"),
    }

    return {
        "program_id": program_id,
        "current_unit": effective_active_unit,
        "generated_at": now_iso_utc(),
        "summary": summary,
        "units": unit_statuses,
        "follow_up_tasks": top_follow_ups,
    }


def list_programs(state: RepoState, current_program: str, current_unit: str) -> dict[str, Any]:
    programs: list[dict[str, Any]] = []
    if state.programs_root.exists():
        for program_dir in sorted(state.programs_root.iterdir()):
            if not program_dir.is_dir():
                continue
            payload = read_json(program_dir / "program.json")
            units = unit_entries(program_dir, current_unit if program_dir.name == current_program else "")
            programs.append(
                {
                    "program_id": program_dir.name,
                    "base_slug": program_base_slug(program_dir.name),
                    "title": payload.get("title", program_dir.name),
                    "status": payload.get("status", "draft"),
                    "target_sessions": int(payload.get("target_sessions", 0) or 0),
                    "expected_units": int(payload.get("expected_units", 0) or 0),
                    "unit_count": len(units),
                    "is_active": program_dir.name == current_program,
                    "updated_at": payload.get("updated_at", ""),
                }
            )

    return {
        "generated_at": now_iso_utc(),
        "current_program": current_program,
        "current_unit": current_unit,
        "program_count": len(programs),
        "programs": programs,
    }


def generate_program_id(intent: str, programs_root: Path) -> str:
    base_slug = slugify(intent) or "program"
    base = f"{base_slug}-{datetime.now().strftime('%Y%m%d-%H%M')}"
    candidate = base
    counter = 2
    while (programs_root / candidate).exists():
        candidate = f"{base}-{counter:02d}"
        counter += 1
    return candidate


def recommend_program(state: RepoState, intent: str, current_program: str) -> dict[str, Any]:
    intent_slug = slugify(intent)
    matches: list[str] = []

    if intent_slug and state.programs_root.exists():
        for program_dir in sorted(state.programs_root.iterdir()):
            if not program_dir.is_dir():
                continue
            if program_base_slug(program_dir.name) == intent_slug:
                matches.append(program_dir.name)

    if current_program and intent_slug and program_base_slug(current_program) == intent_slug:
        return {
            "recommended_action": "reuse-current",
            "program_id": current_program,
            "intent": intent,
            "intent_slug": intent_slug,
            "matches": matches,
        }

    if len(matches) == 1:
        return {
            "recommended_action": "activate-existing",
            "program_id": matches[0],
            "intent": intent,
            "intent_slug": intent_slug,
            "matches": matches,
        }

    if len(matches) > 1:
        return {
            "recommended_action": "choose-existing",
            "program_id": matches[-1],
            "intent": intent,
            "intent_slug": intent_slug,
            "matches": matches,
            "note": "Multiple matching programs found; latest id selected by default.",
        }

    return {
        "recommended_action": "create-new",
        "program_id": generate_program_id(intent or "program", state.programs_root),
        "intent": intent,
        "intent_slug": intent_slug,
        "matches": matches,
    }


def resolve_program_id(state: RepoState, requested_program: str | None) -> str:
    if requested_program:
        raw = requested_program.strip()
        direct = state.programs_root / raw
        if direct.is_dir():
            return raw
        as_slug = slugify(raw)
        slug_dir = state.programs_root / as_slug
        if slug_dir.is_dir():
            return as_slug
        raise ValueError(f"Program not found: {requested_program}")

    current_program = resolve_current_program(state.repo_root, state.context_program_file)
    if current_program and (state.programs_root / current_program).is_dir():
        return current_program

    raise ValueError("No active program context found")


def activate_context(state: RepoState, program_id: str, unit_id: str | None, clear_unit: bool) -> dict[str, Any]:
    program_dir = state.programs_root / program_id
    if not program_dir.is_dir():
        raise ValueError(f"Program directory not found: {program_dir}")

    write_context(state.context_program_file, program_id)

    resolved_unit = ""
    if unit_id:
        candidate = program_dir / "units" / unit_id
        if not candidate.is_dir():
            raise ValueError(f"Unit not found in program '{program_id}': {unit_id}")
        write_context(state.context_unit_file, unit_id)
        resolved_unit = unit_id
    elif clear_unit:
        if state.context_unit_file.exists():
            state.context_unit_file.unlink()
    else:
        resolved_unit = read_context(state.context_unit_file)

    return {
        "program_id": program_id,
        "unit_id": resolved_unit,
        "context_program_file": str(state.context_program_file),
        "context_unit_file": str(state.context_unit_file),
        "cleared_unit": clear_unit and not unit_id,
    }


def print_text(payload: dict[str, Any], action: str) -> None:
    if action == "list":
        print(f"Current program: {payload.get('current_program') or '<none>'}")
        print(f"Current unit: {payload.get('current_unit') or '<none>'}")
        print(f"Programs: {payload.get('program_count', 0)}")
        for item in payload.get("programs", []):
            marker = "*" if item.get("is_active") else " "
            print(
                f"{marker} {item['program_id']} | units={item['unit_count']} | "
                f"status={item['status']} | title={item['title']}"
            )
        return

    if action == "list-units":
        print(f"Program: {payload['program_id']}")
        print(f"Active unit: {payload.get('current_unit') or '<none>'}")
        for unit in payload.get("units", []):
            marker = "*" if unit.get("is_active") else " "
            print(
                f"{marker} {unit['unit_id']} | brief={unit['has_brief']} | design={unit['has_design']} | "
                f"sequence={unit['has_sequence']} | manifest={unit['has_manifest']}"
            )
        return

    if action == "workflow-status":
        summary = payload.get("summary", {})
        print(f"Program: {payload.get('program_id')}")
        print(f"Active unit: {payload.get('current_unit') or '<none>'}")
        print(
            "Pending"
            f" refine={summary.get('refine_pending', 0)}"
            f" design={summary.get('design_pending', 0)}"
            f" sequence={summary.get('sequence_pending', 0)}"
            f" rubric={summary.get('rubric_pending', 0)}"
            f" audit={summary.get('audit_pending', 0)}"
            f" author_ready={summary.get('author_ready', 0)}"
        )
        for unit in payload.get("units", []):
            marker = "*" if unit.get("is_active") else " "
            print(f"{marker} {unit['unit_id']} -> {unit['next_stage']} ({unit['next_reason']})")
        print("Follow-up tasks:")
        for task in payload.get("follow_up_tasks", []):
            print(f"- [{task.get('unit_id')}] {task.get('command')}")
        return

    for key, value in payload.items():
        print(f"{key}: {value}")


def main() -> int:
    args = parse_args()
    state = discover_state(Path(args.repo_root))
    current_program = resolve_current_program(state.repo_root, state.context_program_file)
    current_unit = resolve_current_unit(state.context_unit_file)

    try:
        if args.action == "list":
            payload = list_programs(state, current_program, current_unit)
        elif args.action == "current":
            payload = {
                "program_id": current_program,
                "unit_id": current_unit,
                "program_exists": bool(current_program and (state.programs_root / current_program).is_dir()),
            }
        elif args.action == "recommend":
            if not args.intent:
                raise ValueError("--intent is required for recommend")
            payload = recommend_program(state, args.intent, current_program)
        elif args.action == "activate":
            program_id = resolve_program_id(state, args.program)
            payload = activate_context(state, program_id, args.unit, clear_unit=args.clear_unit or not args.unit)
        elif args.action == "list-units":
            program_id = resolve_program_id(state, args.program)
            program_dir = state.programs_root / program_id
            payload = {
                "program_id": program_id,
                "current_unit": current_unit if program_id == current_program else "",
                "units": unit_entries(program_dir, current_unit if program_id == current_program else ""),
            }
        elif args.action == "workflow-status":
            program_id = resolve_program_id(state, args.program)
            payload = workflow_status(state, program_id, current_program, current_unit)
        else:
            raise ValueError(f"Unsupported action: {args.action}")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=True))
    else:
        print_text(payload, args.action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
