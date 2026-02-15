#!/usr/bin/env python3
"""Validate machine-readable learning-content artifacts against JSON schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class ContractPair:
    artifact: str
    schema: str


REQUIRED_CONTRACTS = (
    ContractPair("brief.json", "brief.schema.json"),
    ContractPair("design.json", "design.schema.json"),
    ContractPair("assessment-blueprint.json", "assessment-blueprint.schema.json"),
    ContractPair("template-selection.json", "template-selection.schema.json"),
    ContractPair("exercise-design.json", "exercise-design.schema.json"),
    ContractPair("sequence.json", "sequence.schema.json"),
    ContractPair("audit-report.json", "audit-report.schema.json"),
    ContractPair("outputs/manifest.json", "manifest.schema.json"),
)

RESPONSE_VERSION = "1.0.0"
PIPELINE_NAME = "artifact-contract-validation.v1"
PIPELINE_MODE = "collect-all-per-phase"
PIPELINE_PHASES = (
    "preflight",
    "artifact_schema",
    "artifact_consistency",
    "template_catalog",
    "template_schema",
    "template_rules",
    "rubric_audit",
    "gate_eval",
    "finalize",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root path")
    parser.add_argument("--unit-dir", required=True, help="Unit directory under programs/<program-id>/units/")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def _resolve_schemas_dir(repo_root: Path) -> Path | None:
    candidates = (
        repo_root / "contracts" / "schemas",
        repo_root / ".lcs" / "contracts" / "schemas",
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _resolve_template_pack_dir(repo_root: Path) -> Path | None:
    env_path = os.getenv("LCS_TEMPLATE_PACK_DIR", "").strip()
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path).expanduser())

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


def _normalize_template_id(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _validate_json(artifact_path: Path, schema_path: Path) -> list[str]:
    errors: list[str] = []

    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"{artifact_path}: invalid JSON ({exc})"]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"{schema_path}: invalid schema JSON ({exc})"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(artifact), key=str):
        location = "/".join(str(p) for p in error.path) or "<root>"
        errors.append(f"{artifact_path}: {location}: {error.message}")

    return errors


def _load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cross_artifact_checks(unit_dir: Path, artifacts: dict[str, dict | list]) -> list[str]:
    errors: list[str] = []

    expected_unit_id = unit_dir.name
    for name, payload in artifacts.items():
        if not isinstance(payload, dict):
            continue
        unit_id = payload.get("unit_id")
        if isinstance(unit_id, str) and unit_id != expected_unit_id:
            errors.append(
                f"{unit_dir / name}: unit_id '{unit_id}' does not match unit directory '{expected_unit_id}'"
            )

    brief = artifacts.get("brief.json")
    design = artifacts.get("design.json")
    exercise_design = artifacts.get("exercise-design.json")
    sequence = artifacts.get("sequence.json")
    audit = artifacts.get("audit-report.json")
    manifest = artifacts.get("outputs/manifest.json")

    brief_lo_ids: set[str] = set()
    brief_lo_priorities: dict[str, str] = {}
    if isinstance(brief, dict):
        learning_outcomes = brief.get("learning_outcomes", [])
        if isinstance(learning_outcomes, list):
            duplicates = set()
            for item in learning_outcomes:
                if not isinstance(item, dict):
                    continue
                lo_id = item.get("lo_id")
                if not isinstance(lo_id, str):
                    continue
                if lo_id in brief_lo_ids:
                    duplicates.add(lo_id)
                brief_lo_ids.add(lo_id)
                priority = item.get("priority")
                if isinstance(priority, str):
                    brief_lo_priorities[lo_id] = priority
            if duplicates:
                errors.append(f"{unit_dir / 'brief.json'}: duplicate LO IDs found: {sorted(duplicates)}")
            if learning_outcomes and not any(
                isinstance(item, dict) and item.get("priority") == "P1"
                for item in learning_outcomes
            ):
                errors.append(f"{unit_dir / 'brief.json'}: at least one learning outcome must have priority P1")

    if isinstance(sequence, dict):
        tasks = sequence.get("tasks", [])
        if isinstance(tasks, list):
            task_ids: list[str] = []
            seen_task_ids: set[str] = set()
            duplicate_task_ids: set[str] = set()

            for task in tasks:
                if not isinstance(task, dict):
                    continue
                task_id = task.get("task_id")
                if not isinstance(task_id, str):
                    continue
                task_ids.append(task_id)
                if task_id in seen_task_ids:
                    duplicate_task_ids.add(task_id)
                seen_task_ids.add(task_id)

            if duplicate_task_ids:
                errors.append(
                    f"{unit_dir / 'sequence.json'}: duplicate task IDs found: {sorted(duplicate_task_ids)}"
                )

            task_id_set = set(task_ids)
            graph: dict[str, list[str]] = {}
            for index, task in enumerate(tasks):
                if not isinstance(task, dict):
                    continue
                task_id = task.get("task_id")
                if not isinstance(task_id, str):
                    continue
                lo_refs = task.get("lo_refs", [])
                if not isinstance(lo_refs, list):
                    continue
                unknown_refs = sorted(ref for ref in lo_refs if isinstance(ref, str) and ref not in brief_lo_ids)
                if unknown_refs:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: tasks[{index}] references unknown LO IDs: {unknown_refs}"
                    )
                depends_on = task.get("depends_on", [])
                if not isinstance(depends_on, list):
                    continue
                graph[task_id] = [dep for dep in depends_on if isinstance(dep, str)]
                unknown_dependencies = sorted(dep for dep in depends_on if isinstance(dep, str) and dep not in task_id_set)
                if unknown_dependencies:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: tasks[{index}] has unknown dependencies: {unknown_dependencies}"
                    )
                if task_id in depends_on:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: tasks[{index}] task_id '{task_id}' cannot depend on itself"
                    )

            visited: dict[str, int] = {}
            cycle_detected = False

            def _visit(node: str) -> None:
                nonlocal cycle_detected
                if cycle_detected:
                    return
                state = visited.get(node, 0)
                if state == 1:
                    cycle_detected = True
                    return
                if state == 2:
                    return
                visited[node] = 1
                for neighbor in graph.get(node, []):
                    if neighbor in graph:
                        _visit(neighbor)
                visited[node] = 2

            for task_id in graph:
                if visited.get(task_id, 0) == 0:
                    _visit(task_id)
                if cycle_detected:
                    break

            if cycle_detected:
                errors.append(f"{unit_dir / 'sequence.json'}: dependency cycle detected in tasks graph")

    if isinstance(sequence, dict) and isinstance(exercise_design, dict):
        tasks = sequence.get("tasks", [])
        exercises = exercise_design.get("exercises", [])

        exercise_index: dict[str, dict[str, str]] = {}
        if isinstance(exercises, list):
            for exercise in exercises:
                if not isinstance(exercise, dict):
                    continue
                exercise_id = exercise.get("exercise_id")
                target_path = exercise.get("target_path")
                template_id = exercise.get("template_id")
                if (
                    isinstance(exercise_id, str)
                    and isinstance(target_path, str)
                    and isinstance(template_id, str)
                ):
                    exercise_index[exercise_id] = {
                        "target_path": target_path,
                        "template_id": template_id,
                    }

        if isinstance(tasks, list) and tasks and exercise_index:
            tasks_by_target: dict[str, list[tuple[int, dict[str, Any]]]] = {}
            for index, task in enumerate(tasks):
                if not isinstance(task, dict):
                    continue
                target_path = task.get("target_path")
                if isinstance(target_path, str):
                    tasks_by_target.setdefault(target_path, []).append((index, task))

                declared_exercise_ids: set[str] = set()
                single_exercise_id = task.get("exercise_id")
                if isinstance(single_exercise_id, str):
                    declared_exercise_ids.add(single_exercise_id)
                exercise_refs = task.get("exercise_refs", [])
                if isinstance(exercise_refs, list):
                    declared_exercise_ids.update(ref for ref in exercise_refs if isinstance(ref, str))

                declared_template_ids: set[str] = set()
                single_template_id = task.get("template_id")
                if isinstance(single_template_id, str):
                    declared_template_ids.add(single_template_id)
                template_ids = task.get("template_ids", [])
                if isinstance(template_ids, list):
                    declared_template_ids.update(ref for ref in template_ids if isinstance(ref, str))

                if declared_template_ids and not declared_exercise_ids:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: tasks[{index}] declares template metadata but has no "
                        "exercise_id/exercise_refs mapping"
                    )

                if declared_exercise_ids and not declared_template_ids:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: tasks[{index}] declares exercise mapping but has no "
                        "template_id/template_ids metadata"
                    )

                for exercise_id in sorted(declared_exercise_ids):
                    exercise_meta = exercise_index.get(exercise_id)
                    if exercise_meta is None:
                        errors.append(
                            f"{unit_dir / 'sequence.json'}: tasks[{index}] references unknown exercise_id "
                            f"'{exercise_id}'"
                        )
                        continue

                    if not isinstance(target_path, str) or target_path != exercise_meta["target_path"]:
                        errors.append(
                            f"{unit_dir / 'sequence.json'}: tasks[{index}] exercise '{exercise_id}' must target "
                            f"'{exercise_meta['target_path']}'"
                        )

                    expected_template_id = exercise_meta["template_id"]
                    if declared_template_ids and expected_template_id not in declared_template_ids:
                        errors.append(
                            f"{unit_dir / 'sequence.json'}: tasks[{index}] exercise '{exercise_id}' requires "
                            f"template metadata '{expected_template_id}'"
                        )

            for exercise_id, exercise_meta in sorted(exercise_index.items()):
                matched_tasks = tasks_by_target.get(exercise_meta["target_path"], [])
                if not matched_tasks:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: missing task for exercise '{exercise_id}' "
                        f"target_path '{exercise_meta['target_path']}'"
                    )
                    continue

                has_exercise_mapping = False
                has_template_mapping = False
                for _, task in matched_tasks:
                    mapped_ids: set[str] = set()
                    if isinstance(task.get("exercise_id"), str):
                        mapped_ids.add(task["exercise_id"])
                    refs = task.get("exercise_refs", [])
                    if isinstance(refs, list):
                        mapped_ids.update(ref for ref in refs if isinstance(ref, str))

                    if exercise_id not in mapped_ids:
                        continue

                    has_exercise_mapping = True
                    mapped_templates: set[str] = set()
                    if isinstance(task.get("template_id"), str):
                        mapped_templates.add(task["template_id"])
                    template_refs = task.get("template_ids", [])
                    if isinstance(template_refs, list):
                        mapped_templates.update(ref for ref in template_refs if isinstance(ref, str))
                    if exercise_meta["template_id"] in mapped_templates:
                        has_template_mapping = True

                if not has_exercise_mapping:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: tasks targeting '{exercise_meta['target_path']}' must include "
                        f"exercise mapping for '{exercise_id}'"
                    )
                if not has_template_mapping:
                    errors.append(
                        f"{unit_dir / 'sequence.json'}: exercise '{exercise_id}' must include template metadata "
                        f"'{exercise_meta['template_id']}' in mapped task(s)"
                    )

    if isinstance(design, dict):
        decisions = design.get("pedagogy_decisions", {})
        if isinstance(decisions, dict):
            threshold = decisions.get("confidence_threshold", 0.7)
            confidence = decisions.get("confidence", 0.0)
            try:
                threshold_value = float(threshold)
                confidence_value = float(confidence)
                if confidence_value < threshold_value:
                    errors.append(
                        f"{unit_dir / 'design.json'}: confidence {confidence_value:.2f} is below threshold "
                        f"{threshold_value:.2f}; run /lcs.refine or /lcs.design with stronger evidence"
                    )
            except (TypeError, ValueError):
                errors.append(
                    f"{unit_dir / 'design.json'}: pedagogy_decisions confidence/threshold must be numeric"
                )

    if isinstance(manifest, dict):
        outcomes = manifest.get("outcomes", [])
        manifest_lo_priorities: dict[str, str] = {}
        manifest_lo_duplicates: set[str] = set()
        manifest_lo_ids = {
            item.get("lo_id")
            for item in outcomes
            if isinstance(item, dict) and isinstance(item.get("lo_id"), str)
        }
        if isinstance(outcomes, list):
            seen_manifest_lo_ids: set[str] = set()
            for index, item in enumerate(outcomes):
                if not isinstance(item, dict):
                    continue
                lo_id = item.get("lo_id")
                if not isinstance(lo_id, str):
                    continue
                if lo_id in seen_manifest_lo_ids:
                    manifest_lo_duplicates.add(lo_id)
                seen_manifest_lo_ids.add(lo_id)
                priority = item.get("priority")
                if isinstance(priority, str):
                    manifest_lo_priorities[lo_id] = priority
                evidence_refs = item.get("evidence_refs", [])
                if isinstance(evidence_refs, list) and f"brief:{lo_id}" not in evidence_refs:
                    errors.append(
                        f"{unit_dir / 'outputs/manifest.json'}: outcomes[{index}] must include evidence_refs entry "
                        f"'brief:{lo_id}'"
                    )

        if manifest_lo_duplicates:
            errors.append(
                f"{unit_dir / 'outputs/manifest.json'}: duplicate outcome LO IDs found: "
                f"{sorted(manifest_lo_duplicates)}"
            )

        if brief_lo_ids and manifest_lo_ids != brief_lo_ids:
            errors.append(
                f"{unit_dir / 'outputs/manifest.json'}: LO IDs {sorted(manifest_lo_ids)} "
                f"must exactly match brief LO IDs {sorted(brief_lo_ids)}"
            )

        if brief_lo_priorities and manifest_lo_priorities:
            for lo_id in sorted(brief_lo_priorities):
                brief_priority = brief_lo_priorities.get(lo_id)
                manifest_priority = manifest_lo_priorities.get(lo_id)
                if manifest_priority and brief_priority != manifest_priority:
                    errors.append(
                        f"{unit_dir / 'outputs/manifest.json'}: LO {lo_id} priority {manifest_priority} "
                        f"must match brief priority {brief_priority}"
                    )

        artifacts_section = manifest.get("artifacts", [])
        if isinstance(artifacts_section, list):
            seen_artifact_ids: set[str] = set()
            seen_artifact_paths: set[str] = set()
            for index, artifact in enumerate(artifacts_section):
                if not isinstance(artifact, dict):
                    continue
                artifact_id = artifact.get("id")
                if isinstance(artifact_id, str):
                    if artifact_id in seen_artifact_ids:
                        errors.append(
                            f"{unit_dir / 'outputs/manifest.json'}: duplicate artifacts[{index}].id '{artifact_id}'"
                        )
                    seen_artifact_ids.add(artifact_id)
                path_value = artifact.get("path")
                if not isinstance(path_value, str):
                    continue
                if path_value in seen_artifact_paths:
                    errors.append(
                        f"{unit_dir / 'outputs/manifest.json'}: duplicate artifacts[{index}].path '{path_value}'"
                    )
                seen_artifact_paths.add(path_value)
                artifact_path = (unit_dir / path_value).resolve()
                try:
                    artifact_path.relative_to(unit_dir.resolve())
                except ValueError:
                    errors.append(
                        f"{unit_dir / 'outputs/manifest.json'}: artifacts[{index}] path escapes unit dir: {path_value}"
                    )
                    continue
                if not artifact_path.exists():
                    errors.append(
                        f"{unit_dir / 'outputs/manifest.json'}: artifacts[{index}] path does not exist: {path_value}"
                    )
                    continue
                checksum = artifact.get("checksum")
                if isinstance(checksum, str) and checksum.lower().startswith("sha256:"):
                    actual_checksum = _sha256_file(artifact_path)
                    if checksum.split(":", 1)[1].lower() != actual_checksum:
                        errors.append(
                            f"{unit_dir / 'outputs/manifest.json'}: artifacts[{index}] checksum mismatch for "
                            f"path '{path_value}'"
                        )

    if isinstance(audit, dict) and isinstance(manifest, dict):
        audit_decision = audit.get("gate_decision")
        manifest_gate = manifest.get("gate_status", {})
        if isinstance(manifest_gate, dict):
            manifest_decision = manifest_gate.get("decision")
            if isinstance(audit_decision, str) and isinstance(manifest_decision, str):
                if audit_decision != manifest_decision:
                    errors.append(
                        f"{unit_dir / 'audit-report.json'} gate_decision '{audit_decision}' "
                        f"must match {unit_dir / 'outputs/manifest.json'} gate_status.decision '{manifest_decision}'"
                    )

            audit_critical = audit.get("open_critical")
            audit_high = audit.get("open_high")
            manifest_critical = manifest_gate.get("open_critical")
            manifest_high = manifest_gate.get("open_high")
            if audit_critical != manifest_critical or audit_high != manifest_high:
                errors.append(
                    f"{unit_dir / 'audit-report.json'} open counters must match manifest gate_status counters"
                )

        findings = audit.get("findings", [])
        if isinstance(findings, list):
            open_critical = 0
            open_high = 0
            for item in findings:
                if not isinstance(item, dict):
                    continue
                status = item.get("status")
                severity = item.get("severity")
                if status == "OPEN" and severity == "CRITICAL":
                    open_critical += 1
                if status == "OPEN" and severity == "HIGH":
                    open_high += 1

            if audit.get("open_critical") != open_critical:
                errors.append(
                    f"{unit_dir / 'audit-report.json'} open_critical={audit.get('open_critical')} "
                    f"must match OPEN CRITICAL findings count={open_critical}"
                )
            if audit.get("open_high") != open_high:
                errors.append(
                    f"{unit_dir / 'audit-report.json'} open_high={audit.get('open_high')} "
                    f"must match OPEN HIGH findings count={open_high}"
                )
            if audit.get("gate_decision") == "PASS" and (open_critical > 0 or open_high > 0):
                errors.append(
                    f"{unit_dir / 'audit-report.json'} gate_decision PASS is invalid when OPEN CRITICAL/HIGH "
                    f"findings exist"
                )

    return errors


def _derive_scoring_rubric_required_keys(schema_payload: dict[str, Any]) -> list[str]:
    if not isinstance(schema_payload, dict):
        return []
    props = schema_payload.get("properties", {})
    if not isinstance(props, dict):
        return []
    item_props = props.get("item", {})
    if not isinstance(item_props, dict):
        return []
    item_children = item_props.get("properties", {})
    if not isinstance(item_children, dict):
        return []
    scoring = item_children.get("scoring_rubric", {})
    if not isinstance(scoring, dict):
        return []
    required = scoring.get("required", [])
    if not isinstance(required, list):
        return []
    return sorted(str(key).strip() for key in required if isinstance(key, str) and str(key).strip())


def _validate_exercise_design_contract(
    *,
    unit_dir: Path,
    template_pack_dir: Path,
    catalog: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    outputs: list[str] = []

    exercise_design_path = unit_dir / "exercise-design.json"
    payload = _load_json(exercise_design_path)
    if not isinstance(payload, dict):
        findings.append(
            _build_finding(
                code="TMP_EXERCISE_DESIGN_INVALID_JSON",
                category="TEMPLATE",
                severity="HIGH",
                message="exercise-design.json must be a JSON object",
                path=str(exercise_design_path),
                rule_id="exercise-design-json-object",
            )
        )
        return findings, outputs

    outputs.append(str(exercise_design_path))
    exercises = payload.get("exercises", [])
    if not isinstance(exercises, list) or not exercises:
        findings.append(
            _build_finding(
                code="TMP_EXERCISE_DESIGN_EMPTY",
                category="TEMPLATE",
                severity="HIGH",
                message="exercise-design.json must include non-empty exercises",
                path=str(exercise_design_path),
                rule_id="exercise-design-exercises-required",
            )
        )
        return findings, outputs

    catalog_templates = {
        _normalize_template_id(item.get("template_id")): item
        for item in catalog.get("templates", [])
        if isinstance(item, dict)
    }

    for index, item in enumerate(exercises):
        if not isinstance(item, dict):
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_ITEM_INVALID",
                    category="TEMPLATE",
                    severity="HIGH",
                    message="exercise entry must be an object",
                    path=f"{exercise_design_path}#/exercises/{index}",
                    rule_id="exercise-design-item-object",
                )
            )
            continue

        template_id = _normalize_template_id(item.get("template_id"))
        catalog_entry = catalog_templates.get(template_id)
        if not template_id or catalog_entry is None:
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_TEMPLATE_UNKNOWN",
                    category="TEMPLATE",
                    severity="HIGH",
                    message=f"exercise references unknown template_id '{template_id or 'missing'}'",
                    path=f"{exercise_design_path}#/exercises/{index}",
                    rule_id="exercise-template-known",
                )
            )
            continue

        expected_schema_ref = str(catalog_entry.get("schema", "")).strip()
        expected_rules_ref = str(catalog_entry.get("rules", "")).strip()
        actual_schema_ref = str(item.get("template_schema_ref", "")).strip()
        actual_rules_ref = str(item.get("template_rules_ref", "")).strip()
        scoring_source = str(item.get("scoring_rubric_source", "")).strip()

        if actual_schema_ref != expected_schema_ref:
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_SCHEMA_REF_MISMATCH",
                    category="TEMPLATE",
                    severity="HIGH",
                    message=f"template_schema_ref '{actual_schema_ref}' must match catalog schema '{expected_schema_ref}'",
                    path=f"{exercise_design_path}#/exercises/{index}/template_schema_ref",
                    rule_id="exercise-template-schema-ref",
                )
            )

        if actual_rules_ref != expected_rules_ref:
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_RULES_REF_MISMATCH",
                    category="TEMPLATE",
                    severity="HIGH",
                    message=f"template_rules_ref '{actual_rules_ref}' must match catalog rules '{expected_rules_ref}'",
                    path=f"{exercise_design_path}#/exercises/{index}/template_rules_ref",
                    rule_id="exercise-template-rules-ref",
                )
            )

        if scoring_source != "template-pack":
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_SCORING_SOURCE_INVALID",
                    category="TEMPLATE",
                    severity="HIGH",
                    message="scoring_rubric_source must be 'template-pack'",
                    path=f"{exercise_design_path}#/exercises/{index}/scoring_rubric_source",
                    rule_id="exercise-scoring-source",
                )
            )

        schema_path = (template_pack_dir / expected_schema_ref).resolve()
        if not schema_path.is_file():
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_TEMPLATE_SCHEMA_MISSING",
                    category="TEMPLATE",
                    severity="HIGH",
                    message=f"template schema file not found for template '{template_id}'",
                    path=str(schema_path),
                    rule_id="exercise-template-schema-file",
                )
            )
            continue

        schema_payload = _load_json(schema_path)
        if not isinstance(schema_payload, dict):
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_TEMPLATE_SCHEMA_INVALID_JSON",
                    category="TEMPLATE",
                    severity="HIGH",
                    message=f"template schema is invalid JSON for template '{template_id}'",
                    path=str(schema_path),
                    rule_id="exercise-template-schema-json",
                )
            )
            continue

        expected_rubric_keys = _derive_scoring_rubric_required_keys(schema_payload)
        provided_keys = item.get("scoring_rubric_required_keys", [])
        if not isinstance(provided_keys, list):
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_SCORING_RUBRIC_KEYS_INVALID",
                    category="TEMPLATE",
                    severity="HIGH",
                    message="scoring_rubric_required_keys must be a list",
                    path=f"{exercise_design_path}#/exercises/{index}/scoring_rubric_required_keys",
                    rule_id="exercise-scoring-rubric-keys-list",
                )
            )
            continue

        normalized_provided = sorted(
            str(key).strip() for key in provided_keys if isinstance(key, str) and str(key).strip()
        )
        if normalized_provided != expected_rubric_keys:
            findings.append(
                _build_finding(
                    code="TMP_EXERCISE_SCORING_RUBRIC_KEYS_MISMATCH",
                    category="TEMPLATE",
                    severity="HIGH",
                    message=(
                        f"scoring_rubric_required_keys {normalized_provided} do not match template schema "
                        f"required keys {expected_rubric_keys}"
                    ),
                    path=f"{exercise_design_path}#/exercises/{index}/scoring_rubric_required_keys",
                    rule_id="exercise-scoring-rubric-keys-match-template",
                )
            )

    return findings, outputs


def _extract_path_hint(message: str) -> str:
    if ":" not in message:
        return ""
    return message.split(":", 1)[0]


def _build_finding(
    *,
    code: str,
    category: str,
    severity: str,
    message: str,
    path: str = "",
    rule_id: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "category": category,
        "severity": severity,
        "path": path,
        "rule_id": rule_id,
        "message": message,
        "details": details or {},
        "status": "OPEN",
    }


def _phase_status(findings: list[dict[str, Any]], default: str = "PASS") -> tuple[str, str]:
    if not findings:
        return default, "INFO"

    if any(item["severity"] in {"CRITICAL", "HIGH"} for item in findings):
        return "BLOCK", "HIGH"
    if any(item["severity"] in {"MEDIUM", "LOW"} for item in findings):
        return "WARN", "MEDIUM"
    return "PASS", "INFO"


def _build_step(
    *,
    step_id: str,
    phase: str,
    status: str,
    severity: str,
    message: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    findings_ref: list[int] | None = None,
    duration_ms: int = 0,
    next_action: str = "",
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "phase": phase,
        "status": status,
        "severity": severity,
        "message": message,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "findings_ref": findings_ref or [],
        "duration_ms": duration_ms,
        "next_action": next_action,
    }


def _normalize_severity(value: Any) -> str:
    severity = str(value).strip().upper()
    if severity in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}:
        return severity
    return "MEDIUM"


def _dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in findings:
        key = (str(item.get("code", "")), str(item.get("path", "")), str(item.get("message", "")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _validate_template_catalog(
    *,
    template_pack_dir: Path,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    outputs: list[str] = []
    catalog_path = template_pack_dir / "catalog.json"
    if not catalog_path.is_file():
        findings.append(
            _build_finding(
                code="TMP_CATALOG_MISSING",
                category="TEMPLATE",
                severity="HIGH",
                message="Template catalog is missing",
                path=str(catalog_path),
                rule_id="template-catalog-required",
            )
        )
        return None, findings, outputs

    payload = _load_json(catalog_path)
    if not isinstance(payload, dict):
        findings.append(
            _build_finding(
                code="TMP_CATALOG_INVALID_JSON",
                category="TEMPLATE",
                severity="HIGH",
                message="Template catalog is not valid JSON",
                path=str(catalog_path),
                rule_id="template-catalog-json",
            )
        )
        return None, findings, outputs

    templates = payload.get("templates", [])
    if not isinstance(templates, list) or not templates:
        findings.append(
            _build_finding(
                code="TMP_CATALOG_EMPTY",
                category="TEMPLATE",
                severity="HIGH",
                message="Template catalog must include at least one template entry",
                path=str(catalog_path),
                rule_id="template-catalog-non-empty",
            )
        )
        return payload, findings, outputs

    seen_template_ids: set[str] = set()
    for index, item in enumerate(templates):
        if not isinstance(item, dict):
            findings.append(
                _build_finding(
                    code="TMP_CATALOG_ITEM_INVALID",
                    category="TEMPLATE",
                    severity="HIGH",
                    message="Template catalog entry must be an object",
                    path=f"{catalog_path}#/templates/{index}",
                    rule_id="template-catalog-entry-object",
                )
            )
            continue

        template_id = _normalize_template_id(item.get("template_id"))
        if not template_id:
            findings.append(
                _build_finding(
                    code="TMP_CATALOG_TEMPLATE_ID_MISSING",
                    category="TEMPLATE",
                    severity="HIGH",
                    message="Template catalog entry is missing template_id",
                    path=f"{catalog_path}#/templates/{index}",
                    rule_id="template-id-required",
                )
            )
            continue

        if template_id in seen_template_ids:
            findings.append(
                _build_finding(
                    code="TMP_CATALOG_TEMPLATE_ID_DUPLICATE",
                    category="TEMPLATE",
                    severity="HIGH",
                    message=f"Duplicate template_id '{template_id}'",
                    path=f"{catalog_path}#/templates/{index}",
                    rule_id="template-id-unique",
                )
            )
            continue

        seen_template_ids.add(template_id)

        schema_ref = item.get("schema", "")
        rules_ref = item.get("rules", "")
        for label, rel_path in (("schema", schema_ref), ("rules", rules_ref)):
            if not isinstance(rel_path, str) or not rel_path:
                findings.append(
                    _build_finding(
                        code="TMP_CATALOG_REF_MISSING",
                        category="TEMPLATE",
                        severity="HIGH",
                        message=f"Template '{template_id}' is missing {label} reference",
                        path=f"{catalog_path}#/templates/{index}",
                        rule_id="template-ref-required",
                    )
                )
                continue
            resolved = (template_pack_dir / rel_path).resolve()
            if not resolved.is_file():
                findings.append(
                    _build_finding(
                        code="TMP_CATALOG_REF_NOT_FOUND",
                        category="TEMPLATE",
                        severity="HIGH",
                        message=f"Template '{template_id}' {label} reference does not exist",
                        path=str(resolved),
                        rule_id="template-ref-exists",
                    )
                )

    outputs.append(str(catalog_path))
    return payload, findings, outputs


def _validate_blueprint_schema(
    *,
    unit_dir: Path,
    catalog: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any] | None, dict[str, Any] | None]:
    findings: list[dict[str, Any]] = []
    outputs: list[str] = []

    blueprint_path = unit_dir / "assessment-blueprint.json"
    selection_path = unit_dir / "template-selection.json"

    if not blueprint_path.is_file() and not selection_path.is_file():
        return findings, outputs, None, None

    blueprint = _load_json(blueprint_path) if blueprint_path.is_file() else None
    selection = _load_json(selection_path) if selection_path.is_file() else None

    if blueprint_path.is_file() and not isinstance(blueprint, dict):
        findings.append(
            _build_finding(
                code="TMP_BLUEPRINT_INVALID_JSON",
                category="TEMPLATE",
                severity="HIGH",
                message="assessment-blueprint.json must be a JSON object",
                path=str(blueprint_path),
                rule_id="blueprint-json-object",
            )
        )
    if selection_path.is_file() and not isinstance(selection, dict):
        findings.append(
            _build_finding(
                code="TMP_SELECTION_INVALID_JSON",
                category="TEMPLATE",
                severity="HIGH",
                message="template-selection.json must be a JSON object",
                path=str(selection_path),
                rule_id="selection-json-object",
            )
        )

    template_ids = {
        _normalize_template_id(item.get("template_id"))
        for item in catalog.get("templates", [])
        if isinstance(item, dict)
    }

    if isinstance(blueprint, dict):
        outputs.append(str(blueprint_path))
        dist = blueprint.get("target_distribution", [])
        if not isinstance(dist, list) or not dist:
            findings.append(
                _build_finding(
                    code="TMP_BLUEPRINT_DISTRIBUTION_MISSING",
                    category="TEMPLATE",
                    severity="HIGH",
                    message="assessment-blueprint.json must include non-empty target_distribution",
                    path=str(blueprint_path),
                    rule_id="blueprint-target-distribution",
                )
            )
        else:
            for index, item in enumerate(dist):
                if not isinstance(item, dict):
                    findings.append(
                        _build_finding(
                            code="TMP_BLUEPRINT_DISTRIBUTION_ITEM_INVALID",
                            category="TEMPLATE",
                            severity="HIGH",
                            message="target_distribution item must be an object",
                            path=f"{blueprint_path}#/target_distribution/{index}",
                            rule_id="blueprint-distribution-item-object",
                        )
                    )
                    continue
                template_id = _normalize_template_id(item.get("template_id"))
                ratio = item.get("ratio_percent")
                if not template_id:
                    findings.append(
                        _build_finding(
                            code="TMP_BLUEPRINT_TEMPLATE_ID_MISSING",
                            category="TEMPLATE",
                            severity="HIGH",
                            message="target_distribution item is missing template_id",
                            path=f"{blueprint_path}#/target_distribution/{index}",
                            rule_id="blueprint-template-id-required",
                        )
                    )
                elif template_ids and template_id not in template_ids:
                    findings.append(
                        _build_finding(
                            code="TMP_BLUEPRINT_TEMPLATE_UNKNOWN",
                            category="TEMPLATE",
                            severity="HIGH",
                            message=f"target_distribution template_id '{template_id}' is not in catalog",
                            path=f"{blueprint_path}#/target_distribution/{index}",
                            rule_id="blueprint-template-known",
                        )
                    )
                if not isinstance(ratio, (int, float)):
                    findings.append(
                        _build_finding(
                            code="TMP_BLUEPRINT_RATIO_INVALID",
                            category="TEMPLATE",
                            severity="HIGH",
                            message="ratio_percent must be numeric",
                            path=f"{blueprint_path}#/target_distribution/{index}",
                            rule_id="blueprint-ratio-numeric",
                        )
                    )

    if isinstance(selection, dict):
        outputs.append(str(selection_path))
        selected_templates = selection.get("selected_templates", [])
        if not isinstance(selected_templates, list) or not selected_templates:
            findings.append(
                _build_finding(
                    code="TMP_SELECTION_EMPTY",
                    category="TEMPLATE",
                    severity="HIGH",
                    message="template-selection.json must include selected_templates",
                    path=str(selection_path),
                    rule_id="selection-templates-required",
                )
            )
        else:
            for index, item in enumerate(selected_templates):
                if not isinstance(item, dict):
                    findings.append(
                        _build_finding(
                            code="TMP_SELECTION_ITEM_INVALID",
                            category="TEMPLATE",
                            severity="HIGH",
                            message="selected_templates item must be an object",
                            path=f"{selection_path}#/selected_templates/{index}",
                            rule_id="selection-item-object",
                        )
                    )
                    continue
                template_id = _normalize_template_id(item.get("template_id"))
                if not template_id:
                    findings.append(
                        _build_finding(
                            code="TMP_SELECTION_TEMPLATE_ID_MISSING",
                            category="TEMPLATE",
                            severity="HIGH",
                            message="selected_templates item is missing template_id",
                            path=f"{selection_path}#/selected_templates/{index}",
                            rule_id="selection-template-id-required",
                        )
                    )
                elif template_ids and template_id not in template_ids:
                    findings.append(
                        _build_finding(
                            code="TMP_SELECTION_TEMPLATE_UNKNOWN",
                            category="TEMPLATE",
                            severity="HIGH",
                            message=f"selected template '{template_id}' is not in catalog",
                            path=f"{selection_path}#/selected_templates/{index}",
                            rule_id="selection-template-known",
                        )
                    )

    return findings, outputs, blueprint if isinstance(blueprint, dict) else None, selection if isinstance(selection, dict) else None


def _validate_template_rules(
    *,
    unit_dir: Path,
    brief: dict[str, Any] | None,
    blueprint: dict[str, Any] | None,
    selection: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    outputs: list[str] = []

    if blueprint is None and selection is None:
        return findings, outputs

    if isinstance(blueprint, dict):
        dist = blueprint.get("target_distribution", [])
        tolerance = blueprint.get("tolerance_percent", 10)
        ratio_sum = 0.0
        if isinstance(dist, list):
            for item in dist:
                if isinstance(item, dict) and isinstance(item.get("ratio_percent"), (int, float)):
                    ratio_sum += float(item.get("ratio_percent"))
        if abs(ratio_sum - 100.0) > float(tolerance):
            findings.append(
                _build_finding(
                    code="TMP_BLUEPRINT_RATIO_DRIFT",
                    category="TEMPLATE",
                    severity="MEDIUM",
                    message=f"Template ratio sum {ratio_sum:.2f}% is outside tolerance ±{tolerance}%",
                    path=str(unit_dir / "assessment-blueprint.json"),
                    rule_id="blueprint-ratio-tolerance",
                    details={"ratio_sum": ratio_sum, "tolerance": tolerance},
                )
            )

        lo_mapping = blueprint.get("lo_mapping", {})
        if isinstance(brief, dict):
            expected_lo = [
                item.get("lo_id")
                for item in brief.get("learning_outcomes", [])
                if isinstance(item, dict) and isinstance(item.get("lo_id"), str)
            ]
            if isinstance(lo_mapping, dict):
                for lo_id in expected_lo:
                    mapped = lo_mapping.get(lo_id, [])
                    if not isinstance(mapped, list) or not mapped:
                        findings.append(
                            _build_finding(
                                code="TMP_BLUEPRINT_LO_UNMAPPED",
                                category="TEMPLATE",
                                severity="MEDIUM",
                                message=f"LO '{lo_id}' has no mapped template in assessment blueprint",
                                path=str(unit_dir / "assessment-blueprint.json"),
                                rule_id="blueprint-lo-coverage",
                            )
                        )

        outputs.append("assessment-blueprint.rules")

    if isinstance(selection, dict):
        selected_templates = selection.get("selected_templates", [])
        top_k = selection.get("top_k", 3)
        seen: set[str] = set()
        duplicate_ids: set[str] = set()
        for item in selected_templates if isinstance(selected_templates, list) else []:
            if not isinstance(item, dict):
                continue
            template_id = _normalize_template_id(item.get("template_id"))
            if not template_id:
                continue
            if template_id in seen:
                duplicate_ids.add(template_id)
            seen.add(template_id)

        if duplicate_ids:
            findings.append(
                _build_finding(
                    code="TMP_SELECTION_DUPLICATE",
                    category="TEMPLATE",
                    severity="MEDIUM",
                    message=f"Duplicate template IDs in selection: {sorted(duplicate_ids)}",
                    path=str(unit_dir / "template-selection.json"),
                    rule_id="selection-template-unique",
                )
            )

        if isinstance(top_k, int) and isinstance(selected_templates, list) and len(selected_templates) > top_k:
            findings.append(
                _build_finding(
                    code="TMP_SELECTION_EXCEEDS_TOPK",
                    category="TEMPLATE",
                    severity="MEDIUM",
                    message=f"selected_templates has {len(selected_templates)} items but top_k={top_k}",
                    path=str(unit_dir / "template-selection.json"),
                    rule_id="selection-top-k-limit",
                )
            )

        outputs.append("template-selection.rules")

    return findings, outputs


def _validate_template_rules_with_validator(
    *,
    template_pack_dir: Path,
    unit_dir: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    findings: list[dict[str, Any]] = []
    outputs: list[str] = []

    validator_path = template_pack_dir / "validators" / "validate_template_pack.py"
    if not validator_path.is_file():
        findings.append(
            _build_finding(
                code="TMP_VALIDATOR_SCRIPT_MISSING",
                category="TEMPLATE",
                severity="HIGH",
                message="Template pack validator script is missing",
                path=str(validator_path),
                rule_id="template-validator-script-required",
            )
        )
        return findings, outputs

    outputs.append(str(validator_path))
    command = [
        sys.executable,
        str(validator_path),
        "--template-pack-dir",
        str(template_pack_dir),
        "--unit-dir",
        str(unit_dir),
        "--json",
    ]

    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False)
    except Exception as exc:  # noqa: BLE001
        findings.append(
            _build_finding(
                code="TMP_VALIDATOR_EXEC_FAILED",
                category="SYSTEM",
                severity="HIGH",
                message=f"Failed to execute template validator: {exc}",
                path=str(validator_path),
                rule_id="template-validator-exec",
            )
        )
        return findings, outputs

    stdout = process.stdout.strip()
    if not stdout:
        findings.append(
            _build_finding(
                code="TMP_VALIDATOR_NO_OUTPUT",
                category="SYSTEM",
                severity="HIGH",
                message="Template validator returned no JSON payload",
                path=str(validator_path),
                rule_id="template-validator-json-output",
                details={"stderr": process.stderr.strip(), "returncode": process.returncode},
            )
        )
        return findings, outputs

    try:
        payload = json.loads(stdout)
    except Exception as exc:  # noqa: BLE001
        findings.append(
            _build_finding(
                code="TMP_VALIDATOR_OUTPUT_INVALID",
                category="SYSTEM",
                severity="HIGH",
                message=f"Template validator output is not valid JSON: {exc}",
                path=str(validator_path),
                rule_id="template-validator-json-output",
                details={"stdout": stdout[:300], "returncode": process.returncode},
            )
        )
        return findings, outputs

    raw_findings = payload.get("FINDINGS", [])
    if raw_findings and not isinstance(raw_findings, list):
        findings.append(
            _build_finding(
                code="TMP_VALIDATOR_FINDINGS_INVALID",
                category="SYSTEM",
                severity="HIGH",
                message="Template validator FINDINGS must be a list",
                path=str(validator_path),
                rule_id="template-validator-findings-list",
            )
        )
        return findings, outputs

    for item in raw_findings if isinstance(raw_findings, list) else []:
        if not isinstance(item, dict):
            findings.append(
                _build_finding(
                    code="TMP_VALIDATOR_FINDING_INVALID",
                    category="SYSTEM",
                    severity="HIGH",
                    message="Template validator finding entry must be an object",
                    path=str(validator_path),
                    rule_id="template-validator-finding-object",
                )
            )
            continue
        findings.append(
            _build_finding(
                code=str(item.get("code", "TMP_VALIDATOR_FINDING")).strip() or "TMP_VALIDATOR_FINDING",
                category="TEMPLATE",
                severity=_normalize_severity(item.get("severity", "MEDIUM")),
                message=str(item.get("message", "Template validator finding")).strip() or "Template validator finding",
                path=str(item.get("path", "")).strip(),
                rule_id=str(item.get("rule_id", "template-pack-validator")).strip() or "template-pack-validator",
                details=item.get("details", {}) if isinstance(item.get("details"), dict) else {},
            )
        )

    status = str(payload.get("STATUS", "")).strip().upper()
    has_blocking = any(item["severity"] in {"CRITICAL", "HIGH"} for item in findings)
    if status == "BLOCK" and not has_blocking:
        findings.append(
            _build_finding(
                code="TMP_VALIDATOR_BLOCK_UNMAPPED",
                category="TEMPLATE",
                severity="HIGH",
                message="Template validator returned BLOCK without mapped blocking findings",
                path=str(validator_path),
                rule_id="template-validator-block-state",
                details={"returncode": process.returncode},
            )
        )

    return findings, outputs


def _build_phase_summary(steps: list[dict[str, Any]], findings: list[dict[str, Any]], decision: str) -> dict[str, Any]:
    by_phase: dict[str, dict[str, Any]] = {}
    for step in steps:
        phase = step["phase"]
        by_phase[phase] = {
            "status": step["status"],
            "severity": step["severity"],
            "finding_count": len(step.get("findings_ref", [])),
            "duration_ms": step.get("duration_ms", 0),
        }

    open_critical = sum(1 for item in findings if item["severity"] == "CRITICAL")
    open_high = sum(1 for item in findings if item["severity"] == "HIGH")

    return {
        "decision": decision,
        "total_steps": len(steps),
        "phase_order": list(PIPELINE_PHASES),
        "by_phase": by_phase,
        "open_critical": open_critical,
        "open_high": open_high,
        "finding_count": len(findings),
    }


def _build_agent_report(
    *,
    steps: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    decision: str,
    unit_dir: Path,
) -> dict[str, Any]:
    blocking_steps = [step["step_id"] for step in steps if step["status"] == "BLOCK"]
    top_issues = [
        {
            "code": finding["code"],
            "severity": finding["severity"],
            "message": finding["message"],
            "path": finding.get("path", ""),
        }
        for finding in findings[:5]
    ]
    ordered_fix_plan = [
        {
            "code": finding["code"],
            "priority": "P0" if finding["severity"] in {"CRITICAL", "HIGH"} else "P1",
            "action": (
                f"Fix {finding['code']}"
                if not finding.get("path")
                else f"Fix {finding['code']} at {finding['path']}"
            ),
        }
        for finding in findings
        if finding["severity"] in {"CRITICAL", "HIGH", "MEDIUM"}
    ]

    if decision == "PASS":
        summary_line = "All required contract checks passed."
    else:
        summary_line = f"Validation blocked with {len(blocking_steps)} blocking step(s)."

    return {
        "summary_line": summary_line,
        "blocking_steps": blocking_steps,
        "top_issues": top_issues,
        "ordered_fix_plan": ordered_fix_plan,
        "rerun_command": (
            "bash factory/scripts/bash/validate-artifact-contracts.sh --json "
            f"--unit-dir \"{unit_dir}\""
        ),
    }


def main() -> int:
    args = parse_args()

    repo_root = Path(args.repo_root).resolve()
    unit_dir = Path(args.unit_dir).resolve()
    schemas_dir = _resolve_schemas_dir(repo_root)

    missing_files: list[str] = []
    missing_schemas: list[str] = []
    validated: list[str] = []
    errors: list[str] = []
    artifacts: dict[str, dict | list] = {}

    findings: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []

    phase_start = time.perf_counter()
    preflight_findings: list[dict[str, Any]] = []
    if schemas_dir is None:
        missing_schemas.append(str(repo_root / "contracts" / "schemas"))
        preflight_findings.append(
            _build_finding(
                code="SCHEMA_DIR_NOT_FOUND",
                category="IO",
                severity="CRITICAL",
                message="Schema directory not found (expected contracts/schemas)",
                path=str(repo_root),
                rule_id="schema-dir-required",
            )
        )
    preflight_status, preflight_severity = _phase_status(preflight_findings)
    if preflight_findings:
        findings.extend(preflight_findings)
        preflight_refs = list(range(len(findings) - len(preflight_findings), len(findings)))
    else:
        preflight_refs = []
    steps.append(
        _build_step(
            step_id="PRE_001",
            phase="preflight",
            status=preflight_status,
            severity=preflight_severity,
            message="Resolved validator inputs and schema bundle",
            inputs=[str(repo_root), str(unit_dir)],
            outputs=[str(schemas_dir)] if schemas_dir else [],
            findings_ref=preflight_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action="Ensure contracts/schemas exists before re-running." if preflight_status == "BLOCK" else "",
        )
    )

    phase_start = time.perf_counter()
    schema_phase_findings: list[dict[str, Any]] = []
    if schemas_dir is not None:
        for pair in REQUIRED_CONTRACTS:
            artifact_path = unit_dir / pair.artifact
            schema_path = schemas_dir / pair.schema

            if not schema_path.is_file():
                missing_schemas.append(str(schema_path))
                schema_phase_findings.append(
                    _build_finding(
                        code="SCHEMA_FILE_MISSING",
                        category="SCHEMA",
                        severity="HIGH",
                        message=f"Missing schema file for {pair.artifact}",
                        path=str(schema_path),
                        rule_id="schema-file-required",
                    )
                )
                continue

            if not artifact_path.is_file():
                missing_files.append(str(artifact_path))
                schema_phase_findings.append(
                    _build_finding(
                        code="ARTIFACT_FILE_MISSING",
                        category="IO",
                        severity="HIGH",
                        message=f"Missing required artifact file {pair.artifact}",
                        path=str(artifact_path),
                        rule_id="artifact-file-required",
                    )
                )
                continue

            validated.append(str(artifact_path))
            schema_errors = _validate_json(artifact_path, schema_path)
            errors.extend(schema_errors)
            for msg in schema_errors:
                schema_phase_findings.append(
                    _build_finding(
                        code="SCHEMA_VALIDATION_ERROR",
                        category="SCHEMA",
                        severity="HIGH",
                        message=msg,
                        path=_extract_path_hint(msg),
                        rule_id=pair.schema,
                    )
                )

            loaded = _load_json(artifact_path)
            if loaded is not None:
                artifacts[pair.artifact] = loaded
    else:
        schema_phase_findings.append(
            _build_finding(
                code="SCHEMA_PHASE_SKIPPED",
                category="SYSTEM",
                severity="INFO",
                message="Artifact schema phase skipped due to missing schema directory",
                path=str(unit_dir),
                rule_id="artifact-schema-skip",
            )
        )

    schema_status, schema_severity = _phase_status(schema_phase_findings, default="PASS")
    findings.extend(schema_phase_findings)
    schema_refs = list(range(len(findings) - len(schema_phase_findings), len(findings))) if schema_phase_findings else []
    steps.append(
        _build_step(
            step_id="ART_SCHEMA_001",
            phase="artifact_schema",
            status=schema_status if schemas_dir is not None else "BLOCK",
            severity=schema_severity if schemas_dir is not None else "HIGH",
            message="Validated required artifact JSON files against schema contracts",
            inputs=[str(unit_dir / pair.artifact) for pair in REQUIRED_CONTRACTS],
            outputs=validated,
            findings_ref=schema_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action="Fix missing files/schemas and schema violations." if schema_status != "PASS" else "",
        )
    )

    phase_start = time.perf_counter()
    consistency_findings: list[dict[str, Any]] = []
    consistency_errors: list[str] = []
    if schemas_dir is not None and not missing_files and not missing_schemas and not errors:
        consistency_errors = _cross_artifact_checks(unit_dir, artifacts)
        errors.extend(consistency_errors)
        for msg in consistency_errors:
            consistency_findings.append(
                _build_finding(
                    code="CONSISTENCY_CHECK_FAILED",
                    category="CONSISTENCY",
                    severity="HIGH",
                    message=msg,
                    path=_extract_path_hint(msg),
                    rule_id="cross-artifact-consistency",
                )
            )
        consistency_status, consistency_severity = _phase_status(consistency_findings)
    else:
        consistency_status = "SKIP"
        consistency_severity = "INFO"

    findings.extend(consistency_findings)
    consistency_refs = (
        list(range(len(findings) - len(consistency_findings), len(findings))) if consistency_findings else []
    )
    steps.append(
        _build_step(
            step_id="ART_CONS_001",
            phase="artifact_consistency",
            status=consistency_status,
            severity=consistency_severity,
            message=(
                "Cross-artifact consistency checks completed"
                if consistency_status != "SKIP"
                else "Cross-artifact consistency skipped (schema phase not clean)"
            ),
            inputs=[str(unit_dir / pair.artifact) for pair in REQUIRED_CONTRACTS],
            outputs=["cross-artifact-consistency"],
            findings_ref=consistency_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action="Resolve cross-artifact mismatch before publish." if consistency_status == "BLOCK" else "",
        )
    )

    template_pack_dir = _resolve_template_pack_dir(repo_root)

    phase_start = time.perf_counter()
    catalog_payload: dict[str, Any] | None = None
    catalog_phase_findings: list[dict[str, Any]] = []
    catalog_outputs: list[str] = []
    if template_pack_dir is not None:
        catalog_payload, catalog_phase_findings, catalog_outputs = _validate_template_catalog(
            template_pack_dir=template_pack_dir
        )
        catalog_status, catalog_severity = _phase_status(catalog_phase_findings)
    else:
        catalog_phase_findings.append(
            _build_finding(
                code="TMP_PACK_DIR_MISSING",
                category="TEMPLATE",
                severity="HIGH",
                message="Template pack directory not found; fail-closed policy blocks workflow",
                path=str(repo_root),
                rule_id="template-pack-required",
            )
        )
        catalog_status, catalog_severity = _phase_status(catalog_phase_findings)

    findings.extend(catalog_phase_findings)
    catalog_refs = list(range(len(findings) - len(catalog_phase_findings), len(findings))) if catalog_phase_findings else []
    steps.append(
        _build_step(
            step_id="TMP_CAT_001",
            phase="template_catalog",
            status=catalog_status,
            severity=catalog_severity,
            message=(
                "Template catalog loaded"
                if catalog_status != "SKIP"
                else "Template catalog not found"
            ),
            inputs=[str(template_pack_dir)] if template_pack_dir else [],
            outputs=catalog_outputs,
            findings_ref=catalog_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action="Add/repair template-pack catalog.json." if catalog_status == "BLOCK" else "",
        )
    )

    phase_start = time.perf_counter()
    template_schema_findings: list[dict[str, Any]] = []
    template_schema_outputs: list[str] = []
    blueprint_payload: dict[str, Any] | None = None
    selection_payload: dict[str, Any] | None = None
    if catalog_payload is not None:
        (
            template_schema_findings,
            template_schema_outputs,
            blueprint_payload,
            selection_payload,
        ) = _validate_blueprint_schema(unit_dir=unit_dir, catalog=catalog_payload)
        if template_pack_dir is not None:
            exercise_design_findings, exercise_design_outputs = _validate_exercise_design_contract(
                unit_dir=unit_dir,
                template_pack_dir=template_pack_dir,
                catalog=catalog_payload,
            )
            template_schema_findings.extend(exercise_design_findings)
            template_schema_outputs.extend(exercise_design_outputs)
        if not template_schema_outputs and not template_schema_findings:
            template_schema_status, template_schema_severity = "SKIP", "INFO"
        else:
            template_schema_status, template_schema_severity = _phase_status(template_schema_findings)
    else:
        template_schema_status, template_schema_severity = "SKIP", "INFO"

    findings.extend(template_schema_findings)
    template_schema_refs = (
        list(range(len(findings) - len(template_schema_findings), len(findings)))
        if template_schema_findings
        else []
    )
    steps.append(
        _build_step(
            step_id="TMP_SCHEMA_001",
            phase="template_schema",
            status=template_schema_status,
            severity=template_schema_severity,
            message=(
                "Template schema checks completed"
                if template_schema_status != "SKIP"
                else "Template schema checks skipped"
            ),
            inputs=[
                str(unit_dir / "assessment-blueprint.json"),
                str(unit_dir / "template-selection.json"),
                str(unit_dir / "exercise-design.json"),
            ],
            outputs=template_schema_outputs,
            findings_ref=template_schema_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action=(
                "Fix template blueprint/selection schema errors before authoring."
                if template_schema_status == "BLOCK"
                else ""
            ),
        )
    )

    brief_payload = artifacts.get("brief.json") if isinstance(artifacts.get("brief.json"), dict) else None

    phase_start = time.perf_counter()
    prof_findings: list[dict[str, Any]] = []
    prof_outputs: list[str] = []
    prof_status: str = "SKIP"
    prof_severity: str = "INFO"

    if isinstance(brief_payload, dict) and isinstance(brief_payload.get("proficiency_targets"), list):
        try:
            from lcs_cli.proficiency.registry import (  # type: ignore
                load_crosswalks,
                load_framework_registry,
                load_subject_pivots,
            )
            from lcs_cli.proficiency.normalize import normalize_targets_to_pivot  # type: ignore
            from lcs_cli.proficiency.validate import validate_proficiency_targets  # type: ignore

            registry = load_framework_registry(repo_root)
            crosswalks = load_crosswalks(repo_root)
            pivots = load_subject_pivots(repo_root)
            subject = str((catalog_payload or {}).get("subject", "")).strip() if isinstance(catalog_payload, dict) else ""
            targets = brief_payload.get("proficiency_targets", [])

            issues = validate_proficiency_targets(
                brief=brief_payload,
                registry=registry,
                crosswalks=crosswalks,
                subject=subject,
            )
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                code = str(issue.get("code", "PROF_TARGET_INVALID")).strip() or "PROF_TARGET_INVALID"
                severity = str(issue.get("severity", "HIGH")).strip().upper() or "HIGH"
                message = str(issue.get("message", "Invalid proficiency target")).strip() or "Invalid proficiency target"
                details = issue.get("details", {})
                prof_findings.append(
                    _build_finding(
                        code=code,
                        category="PROFICIENCY",
                        severity=severity,
                        message=message,
                        path=str(unit_dir / "brief.json"),
                        rule_id="proficiency-targets",
                        details=details if isinstance(details, dict) else {},
                    )
                )

            normalized = normalize_targets_to_pivot(
                brief_targets=[t for t in targets if isinstance(t, dict)],
                subject=subject,
                pivots=pivots,
                crosswalks=crosswalks,
            )

            pivot_targets = normalized.get("pivot_targets", [])
            unmapped_targets = normalized.get("unmapped_targets", [])
            if not isinstance(pivot_targets, list) or not pivot_targets:
                prof_findings.append(
                    _build_finding(
                        code="PROF_NORMALIZE_EMPTY",
                        category="PROFICIENCY",
                        severity="HIGH",
                        message="proficiency_targets declared but none could be normalized to subject pivot framework",
                        path=str(unit_dir / "brief.json"),
                        rule_id="proficiency-normalize-to-pivot",
                        details={
                            "subject": subject,
                            "pivot_framework_id": normalized.get("pivot_framework_id", ""),
                            "unmapped_count": len(unmapped_targets) if isinstance(unmapped_targets, list) else None,
                        },
                    )
                )
            elif isinstance(unmapped_targets, list) and unmapped_targets:
                prof_findings.append(
                    _build_finding(
                        code="PROF_TARGET_UNMAPPED",
                        category="PROFICIENCY",
                        severity="MEDIUM",
                        message="Some proficiency_targets could not be normalized to subject pivot framework",
                        path=str(unit_dir / "brief.json"),
                        rule_id="proficiency-normalize-to-pivot",
                        details={"unmapped_targets": unmapped_targets[:3], "unmapped_count": len(unmapped_targets)},
                    )
                )

            if prof_findings:
                prof_status, prof_severity = _phase_status(prof_findings)
            else:
                prof_status, prof_severity = "PASS", "INFO"
            prof_outputs.append("proficiency.rules")
        except Exception as exc:  # noqa: BLE001
            prof_findings.append(
                _build_finding(
                    code="PROF_ENGINE_FAILED",
                    category="SYSTEM",
                    severity="HIGH",
                    message=f"Failed to validate proficiency targets: {exc}",
                    path=str(unit_dir / "brief.json"),
                    rule_id="proficiency-engine",
                )
            )
            prof_status, prof_severity = _phase_status(prof_findings)

    findings.extend(prof_findings)
    prof_refs = list(range(len(findings) - len(prof_findings), len(findings))) if prof_findings else []
    steps.append(
        _build_step(
            step_id="PROF_RULE_001",
            phase="proficiency_rules",
            status=prof_status,
            severity=prof_severity,
            message=(
                "Proficiency target checks completed" if prof_status != "SKIP" else "Proficiency target checks skipped"
            ),
            inputs=[str(unit_dir / "brief.json")] + ([str(template_pack_dir / "catalog.json")] if template_pack_dir else []),
            outputs=prof_outputs,
            findings_ref=prof_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action=("Fix proficiency_targets before authoring." if prof_status == "BLOCK" else ""),
        )
    )

    phase_start = time.perf_counter()
    template_rule_findings: list[dict[str, Any]] = []
    template_rule_outputs: list[str] = []
    if catalog_payload is not None and (blueprint_payload is not None or selection_payload is not None):
        template_rule_findings, template_rule_outputs = _validate_template_rules(
            unit_dir=unit_dir,
            brief=brief_payload,
            blueprint=blueprint_payload,
            selection=selection_payload,
        )
        if template_pack_dir is not None:
            validator_findings, validator_outputs = _validate_template_rules_with_validator(
                template_pack_dir=template_pack_dir,
                unit_dir=unit_dir,
            )
            template_rule_findings.extend(validator_findings)
            template_rule_outputs.extend(validator_outputs)
            template_rule_findings = _dedupe_findings(template_rule_findings)
        if template_rule_findings:
            template_rule_status, template_rule_severity = _phase_status(template_rule_findings)
        else:
            template_rule_status, template_rule_severity = "PASS", "INFO"
    else:
        template_rule_status, template_rule_severity = "SKIP", "INFO"

    findings.extend(template_rule_findings)
    template_rule_refs = (
        list(range(len(findings) - len(template_rule_findings), len(findings))) if template_rule_findings else []
    )
    steps.append(
        _build_step(
            step_id="TMP_RULE_001",
            phase="template_rules",
            status=template_rule_status,
            severity=template_rule_severity,
            message=(
                "Template semantic checks completed"
                if template_rule_status != "SKIP"
                else "Template semantic checks skipped"
            ),
            inputs=[
                str(unit_dir / "assessment-blueprint.json"),
                str(unit_dir / "template-selection.json"),
                str(unit_dir / "exercise-design.json"),
            ],
            outputs=template_rule_outputs,
            findings_ref=template_rule_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action=(
                "Address template semantic warnings for better LO coverage and distribution."
                if template_rule_status in {"WARN", "BLOCK"}
                else ""
            ),
        )
    )

    phase_start = time.perf_counter()
    rubric_audit_findings: list[dict[str, Any]] = []
    audit_payload = artifacts.get("audit-report.json")
    if isinstance(audit_payload, dict):
        gate_decision = str(audit_payload.get("gate_decision", "BLOCK")).upper()
        open_critical = int(audit_payload.get("open_critical", 0))
        open_high = int(audit_payload.get("open_high", 0))
        if gate_decision == "BLOCK" or open_critical > 0 or open_high > 0:
            rubric_audit_findings.append(
                _build_finding(
                    code="AUDIT_GATE_BLOCK",
                    category="GATE",
                    severity="LOW",
                    message=(
                        "Audit report currently indicates BLOCK/OPEN findings; author gate will enforce hard stop"
                    ),
                    path=str(unit_dir / "audit-report.json"),
                    rule_id="audit-gate-preview",
                    details={
                        "gate_decision": gate_decision,
                        "open_critical": open_critical,
                        "open_high": open_high,
                    },
                )
            )
        rubric_status, rubric_severity = _phase_status(rubric_audit_findings)
    else:
        rubric_status, rubric_severity = "SKIP", "INFO"

    findings.extend(rubric_audit_findings)
    rubric_refs = (
        list(range(len(findings) - len(rubric_audit_findings), len(findings))) if rubric_audit_findings else []
    )
    steps.append(
        _build_step(
            step_id="RUBRIC_001",
            phase="rubric_audit",
            status=rubric_status,
            severity=rubric_severity,
            message=(
                "Rubric/audit parity snapshot collected"
                if rubric_status != "SKIP"
                else "Rubric/audit snapshot skipped"
            ),
            inputs=[str(unit_dir / "audit-report.json")],
            outputs=["audit-gate-preview"] if rubric_status != "SKIP" else [],
            findings_ref=rubric_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action="Resolve audit blockers before /lcs.author." if rubric_status in {"WARN", "BLOCK"} else "",
        )
    )

    phase_start = time.perf_counter()
    blocking_findings = [item for item in findings if item["severity"] in {"CRITICAL", "HIGH"}]
    decision = "PASS" if not blocking_findings else "BLOCK"
    gate_findings: list[dict[str, Any]] = []
    if decision == "BLOCK":
        gate_findings.append(
            _build_finding(
                code="PIPELINE_BLOCKED",
                category="GATE",
                severity="HIGH",
                message="Validation pipeline contains blocking findings",
                rule_id="gate-eval-high-critical",
                details={"blocking_finding_count": len(blocking_findings)},
            )
        )
    findings.extend(gate_findings)
    gate_refs = list(range(len(findings) - len(gate_findings), len(findings))) if gate_findings else []
    steps.append(
        _build_step(
            step_id="GATE_001",
            phase="gate_eval",
            status=("BLOCK" if decision == "BLOCK" else "PASS"),
            severity=("HIGH" if decision == "BLOCK" else "INFO"),
            message=(
                "Gate decision computed from pipeline severities"
                if decision == "PASS"
                else "Gate decision is BLOCK due to CRITICAL/HIGH findings"
            ),
            inputs=["pipeline-findings"],
            outputs=[f"decision:{decision}"],
            findings_ref=gate_refs,
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
            next_action="Fix blocking findings and rerun validation." if decision == "BLOCK" else "",
        )
    )

    phase_start = time.perf_counter()
    steps.append(
        _build_step(
            step_id="FINAL_001",
            phase="finalize",
            status="PASS",
            severity="INFO",
            message="Compiled validation response envelope",
            inputs=["pipeline-steps", "pipeline-findings"],
            outputs=["PHASE_SUMMARY", "AGENT_REPORT"],
            duration_ms=int((time.perf_counter() - phase_start) * 1000),
        )
    )
    phase_summary = _build_phase_summary(steps=steps, findings=findings, decision=decision)
    agent_report = _build_agent_report(steps=steps, findings=findings, decision=decision, unit_dir=unit_dir)

    status = "PASS" if decision == "PASS" else "BLOCK"
    payload = {
        "STATUS": status,
        "UNIT_DIR": str(unit_dir),
        "VALIDATED": validated,
        "MISSING_FILES": missing_files,
        "MISSING_SCHEMAS": missing_schemas,
        "ERRORS": errors,
        "RESPONSE_VERSION": RESPONSE_VERSION,
        "PIPELINE": {
            "name": PIPELINE_NAME,
            "mode": PIPELINE_MODE,
            "phases": list(PIPELINE_PHASES),
        },
        "STEPS": steps,
        "FINDINGS": findings,
        "PHASE_SUMMARY": phase_summary,
        "AGENT_REPORT": agent_report,
    }

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(f"STATUS: {status}")
        print(f"UNIT_DIR: {unit_dir}")
        print(f"VALIDATED: {len(validated)}")
        print(f"RESPONSE_VERSION: {RESPONSE_VERSION}")
        print(f"PIPELINE: {PIPELINE_NAME}")
        if missing_schemas:
            print("MISSING_SCHEMAS:")
            for item in missing_schemas:
                print(f"  - {item}")
        if missing_files:
            print("MISSING_FILES:")
            for item in missing_files:
                print(f"  - {item}")
        if errors:
            print("ERRORS:")
            for item in errors:
                print(f"  - {item}")
        if findings:
            print("FINDINGS:")
            for item in findings:
                print(f"  - [{item['severity']}] {item['code']}: {item['message']}")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
