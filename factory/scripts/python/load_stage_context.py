#!/usr/bin/env python3
"""Resolve stage context and enforce previous-step input contracts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root")
    parser.add_argument("--stage", required=True, help="Workflow stage name")
    parser.add_argument("--intent", default="", help="Optional natural-language intent for unit resolution")
    parser.add_argument("--program", default="", help="Optional program override")
    parser.add_argument("--unit", default="", help="Optional unit override")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _to_non_negative_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except Exception:
        return default
    return parsed if parsed >= 0 else default


def _read_context_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _run_manage(repo_root: Path, args: list[str]) -> dict[str, Any] | None:
    tool = repo_root / "factory" / "scripts" / "python" / "manage_program_context.py"
    if not tool.is_file():
        return None

    cmd = [sys.executable, str(tool), "--repo-root", str(repo_root), "--json", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None

    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return None


def _count_open_questions(brief_payload: dict[str, Any]) -> int:
    value = 0
    if isinstance(brief_payload.get("open_questions"), int):
        value = max(value, int(brief_payload["open_questions"]))

    refinement = brief_payload.get("refinement")
    if isinstance(refinement, dict) and isinstance(refinement.get("open_questions"), int):
        value = max(value, int(refinement["open_questions"]))
    return value


def _resolve_paths(repo_root: Path, program_id: str, unit_id: str) -> dict[str, Path]:
    program_dir = repo_root / "programs" / program_id
    unit_dir = program_dir / "units" / unit_id if unit_id else Path("")
    return {
        "program_dir": program_dir,
        "unit_dir": unit_dir,
        "program_json": program_dir / "program.json",
        "brief_json": unit_dir / "brief.json",
        "design_json": unit_dir / "design.json",
        "assessment_blueprint_json": unit_dir / "assessment-blueprint.json",
        "template_selection_json": unit_dir / "template-selection.json",
        "exercise_design_json": unit_dir / "exercise-design.json",
        "sequence_json": unit_dir / "sequence.json",
        "rubric_gates_json": unit_dir / "rubric-gates.json",
        "audit_report_json": unit_dir / "audit-report.json",
        "manifest_json": unit_dir / "outputs" / "manifest.json",
    }


def _required_to_path(required_input: str, paths: dict[str, Path]) -> Path | None:
    mapping = {
        "program:program.json": paths["program_json"],
        "unit:brief.json": paths["brief_json"],
        "unit:design.json": paths["design_json"],
        "unit:assessment-blueprint.json": paths["assessment_blueprint_json"],
        "unit:template-selection.json": paths["template_selection_json"],
        "unit:exercise-design.json": paths["exercise_design_json"],
        "unit:sequence.json": paths["sequence_json"],
        "unit:rubric-gates.json": paths["rubric_gates_json"],
        "unit:audit-report.json": paths["audit_report_json"],
        "unit:outputs/manifest.json": paths["manifest_json"],
    }
    return mapping.get(required_input)


def _build_response(*, stage: str, program_id: str, unit_id: str, unit_dir: str, previous_stage: str | None,
                    required_inputs: list[str], missing_inputs: list[str], blockers: list[str],
                    next_actions: list[str], resolved_from_intent: bool, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "STATUS": "PASS" if not blockers and not missing_inputs else "BLOCK",
        "STAGE": stage,
        "PROGRAM_ID": program_id,
        "UNIT_ID": unit_id,
        "UNIT_DIR": unit_dir,
        "PREVIOUS_STAGE": previous_stage,
        "REQUIRED_INPUTS": required_inputs,
        "MISSING_INPUTS": missing_inputs,
        "BLOCKERS": blockers,
        "NEXT_ACTIONS": next_actions,
        "RESOLVED_FROM_INTENT": resolved_from_intent,
    }
    if extra:
        payload.update(extra)
    return payload


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    stage = args.stage.strip().lower()

    stage_map_path = repo_root / "factory" / "config" / "stage-context-map.v1.json"
    if not stage_map_path.is_file():
        stage_map_path = repo_root / ".lcs" / "config" / "stage-context-map.v1.json"
    if not stage_map_path.is_file():
        print(json.dumps(_build_response(
            stage=stage,
            program_id="",
            unit_id="",
            unit_dir="",
            previous_stage=None,
            required_inputs=[],
            missing_inputs=[],
            blockers=[f"Missing stage map: {stage_map_path}"],
            next_actions=[],
            resolved_from_intent=False,
        )))
        return 1

    stage_map_payload = _load_json(stage_map_path)
    stages = stage_map_payload.get("stages", {}) if isinstance(stage_map_payload, dict) else {}
    stage_cfg = stages.get(stage)
    if not isinstance(stage_cfg, dict):
        print(json.dumps(_build_response(
            stage=stage,
            program_id="",
            unit_id="",
            unit_dir="",
            previous_stage=None,
            required_inputs=[],
            missing_inputs=[],
            blockers=[f"Unknown stage '{stage}'"],
            next_actions=[],
            resolved_from_intent=False,
        )))
        return 1

    context_program_file = repo_root / ".lcs" / "context" / "current-program"
    context_unit_file = repo_root / ".lcs" / "context" / "current-unit"

    resolved_from_intent = False
    if args.intent:
        resolve_args = [
            "resolve-unit",
            "--for-stage",
            stage,
            "--intent",
            args.intent,
            "--activate-resolved",
        ]
        if args.program:
            resolve_args.extend(["--program", args.program])
        resolved = _run_manage(repo_root, resolve_args)
        resolved_from_intent = bool(resolved)

    env_program = os.environ.get("LCS_PROGRAM", "").strip()
    env_unit = os.environ.get("LCS_UNIT", "").strip()

    program_id = (
        args.program.strip()
        if args.program
        else (env_program or _read_context_file(context_program_file))
    )
    unit_id = (
        args.unit.strip()
        if args.unit
        else (env_unit or _read_context_file(context_unit_file))
    )

    blockers: list[str] = []
    missing_inputs: list[str] = []
    next_actions: list[str] = []

    if not program_id and stage != "charter":
        blockers.append("No active program context found. Run /lcs.charter first.")

    if stage not in {"charter", "define"} and not unit_id:
        blockers.append("No active unit context found. Activate a unit or run /lcs.define.")

    unit_dir = ""
    required_inputs = stage_cfg.get("required_inputs", [])
    if not isinstance(required_inputs, list):
        required_inputs = []

    checks = stage_cfg.get("checks", [])
    if not isinstance(checks, list):
        checks = []

    extra: dict[str, Any] = {"CHECKS": [], "METADATA": {}}

    if not blockers and program_id:
        paths = _resolve_paths(repo_root, program_id, unit_id)
        unit_dir = str(paths["unit_dir"]) if unit_id else ""

        for required in required_inputs:
            path = _required_to_path(str(required), paths)
            if path is None or not path.is_file():
                missing_inputs.append(str(required))

        for check in checks:
            if not isinstance(check, dict):
                continue
            check_type = str(check.get("type", "")).strip()
            check_name = str(check.get("name", "")).strip() or check_type
            check_payload: dict[str, Any] = {"name": check_name, "type": check_type, "status": "PASS"}

            if check_type == "max_open_questions":
                brief_file = paths["brief_json"]
                if not brief_file.is_file():
                    check_payload["status"] = "BLOCK"
                    check_payload["message"] = "brief.json is missing"
                    blockers.append("brief.json is required before /lcs.design")
                else:
                    brief_payload = _load_json(brief_file)
                    open_questions = _count_open_questions(brief_payload if isinstance(brief_payload, dict) else {})
                    max_allowed = int(check.get("max", 0))
                    check_payload["open_questions"] = open_questions
                    check_payload["max"] = max_allowed
                    if open_questions > max_allowed:
                        check_payload["status"] = "BLOCK"
                        check_payload["message"] = f"open_questions={open_questions} exceeds max={max_allowed}"
                        blockers.append(
                            f"brief.json has {open_questions} unresolved open questions. Run /lcs.refine first."
                        )
            elif check_type == "manifest_gate_pass":
                manifest_file = paths["manifest_json"]
                if not manifest_file.is_file():
                    check_payload["status"] = "BLOCK"
                    check_payload["message"] = "manifest missing"
                    blockers.append("outputs/manifest.json is required before /lcs.author")
                else:
                    payload = _load_json(manifest_file)
                    gate_status = payload.get("gate_status", {}) if isinstance(payload, dict) else {}
                    decision = str(gate_status.get("decision", "")).upper() if isinstance(gate_status, dict) else ""
                    open_critical = (
                        _to_non_negative_int(gate_status.get("open_critical", 0)) if isinstance(gate_status, dict) else 0
                    )
                    open_high = (
                        _to_non_negative_int(gate_status.get("open_high", 0)) if isinstance(gate_status, dict) else 0
                    )
                    check_payload.update({
                        "decision": decision,
                        "open_critical": open_critical,
                        "open_high": open_high,
                    })
                    if decision != "PASS" or open_critical > 0 or open_high > 0:
                        check_payload["status"] = "BLOCK"
                        check_payload["message"] = "manifest gate_status must be PASS with zero blockers"
                        blockers.append("Manifest gate_status is not PASS/clean.")
            elif check_type == "audit_gate_pass":
                audit_file = paths["audit_report_json"]
                if not audit_file.is_file():
                    check_payload["status"] = "BLOCK"
                    check_payload["message"] = "audit-report.json missing"
                    blockers.append("audit-report.json is required before /lcs.author")
                else:
                    payload = _load_json(audit_file)
                    decision = str(payload.get("gate_decision", "")).upper() if isinstance(payload, dict) else ""
                    open_critical = _to_non_negative_int(payload.get("open_critical", 0)) if isinstance(payload, dict) else 0
                    open_high = _to_non_negative_int(payload.get("open_high", 0)) if isinstance(payload, dict) else 0
                    check_payload.update({
                        "decision": decision,
                        "open_critical": open_critical,
                        "open_high": open_high,
                    })
                    if decision != "PASS" or open_critical > 0 or open_high > 0:
                        check_payload["status"] = "BLOCK"
                        check_payload["message"] = "audit gate_decision must be PASS with zero blockers"
                        blockers.append("Audit decision is not PASS/clean.")

            extra["CHECKS"].append(check_payload)

        contract_index = repo_root / "contracts" / "index.json"
        if not contract_index.is_file():
            contract_index = repo_root / ".lcs" / "contracts" / "index.json"
        if contract_index.is_file():
            contract_payload = _load_json(contract_index)
            if isinstance(contract_payload, dict):
                contract_version = contract_payload.get("contract_version")
                if isinstance(contract_version, str) and contract_version:
                    extra["METADATA"]["contract_version"] = contract_version

        brief_payload = _load_json(paths["brief_json"]) if paths["brief_json"].is_file() else {}
        if isinstance(brief_payload, dict):
            extra["METADATA"]["brief_open_questions"] = _count_open_questions(brief_payload)

        manifest_payload = _load_json(paths["manifest_json"]) if paths["manifest_json"].is_file() else {}
        if isinstance(manifest_payload, dict):
            gate_status = manifest_payload.get("gate_status")
            if isinstance(gate_status, dict):
                extra["METADATA"]["manifest_gate_status"] = {
                    "decision": str(gate_status.get("decision", "")).upper(),
                    "open_critical": _to_non_negative_int(gate_status.get("open_critical", 0)),
                    "open_high": _to_non_negative_int(gate_status.get("open_high", 0)),
                }

        audit_payload = _load_json(paths["audit_report_json"]) if paths["audit_report_json"].is_file() else {}
        if isinstance(audit_payload, dict):
            extra["METADATA"]["audit_gate_status"] = {
                "decision": str(audit_payload.get("gate_decision", "")).upper(),
                "open_critical": _to_non_negative_int(audit_payload.get("open_critical", 0)),
                "open_high": _to_non_negative_int(audit_payload.get("open_high", 0)),
            }

    if missing_inputs:
        for missing in missing_inputs:
            if missing.startswith("program:"):
                next_actions.append("Run /lcs.charter to initialize program context and contracts.")
                break
        for missing in missing_inputs:
            if missing.startswith("unit:"):
                next_actions.append("Run the previous workflow stage to generate missing unit JSON artifacts.")
                break

    previous_stage = stage_cfg.get("previous_stage")
    if previous_stage is not None and not isinstance(previous_stage, str):
        previous_stage = None

    response = _build_response(
        stage=stage,
        program_id=program_id,
        unit_id=unit_id,
        unit_dir=unit_dir,
        previous_stage=previous_stage,
        required_inputs=[str(item) for item in required_inputs],
        missing_inputs=missing_inputs,
        blockers=blockers,
        next_actions=next_actions,
        resolved_from_intent=resolved_from_intent,
        extra=extra,
    )

    if args.json:
        print(json.dumps(response, ensure_ascii=True))
    else:
        print(f"STATUS: {response['STATUS']}")
        print(f"STAGE: {response['STAGE']}")
        print(f"PROGRAM_ID: {response['PROGRAM_ID']}")
        print(f"UNIT_ID: {response['UNIT_ID']}")
        print(f"UNIT_DIR: {response['UNIT_DIR']}")
        print(f"PREVIOUS_STAGE: {response['PREVIOUS_STAGE']}")
        print(f"MISSING_INPUTS: {', '.join(response['MISSING_INPUTS']) if response['MISSING_INPUTS'] else '-'}")
        if response["BLOCKERS"]:
            print("BLOCKERS:")
            for blocker in response["BLOCKERS"]:
                print(f"- {blocker}")

    return 0 if response["STATUS"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
