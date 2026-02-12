#!/usr/bin/env python3
"""Validate machine-readable learning-content artifacts against JSON schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class ContractPair:
    artifact: str
    schema: str


REQUIRED_CONTRACTS = (
    ContractPair("brief.json", "brief.schema.json"),
    ContractPair("design.json", "design.schema.json"),
    ContractPair("sequence.json", "sequence.schema.json"),
    ContractPair("audit-report.json", "audit-report.schema.json"),
    ContractPair("outputs/manifest.json", "manifest.schema.json"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root path")
    parser.add_argument("--unit-dir", required=True, help="Unit directory under specs/")
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

    if schemas_dir is None:
        missing_schemas.append(str(repo_root / "contracts" / "schemas"))
        payload = {
            "STATUS": "BLOCK",
            "UNIT_DIR": str(unit_dir),
            "VALIDATED": validated,
            "MISSING_FILES": missing_files,
            "MISSING_SCHEMAS": missing_schemas,
            "ERRORS": ["schema directory not found (expected contracts/schemas)"],
        }
        if args.json:
            print(json.dumps(payload, separators=(",", ":")))
        else:
            print("STATUS: BLOCK")
            print(f"UNIT_DIR: {unit_dir}")
            print("MISSING_SCHEMAS:")
            for item in missing_schemas:
                print(f"  - {item}")
            print("ERRORS:")
            print("  - schema directory not found (expected contracts/schemas)")
        return 1

    for pair in REQUIRED_CONTRACTS:
        artifact_path = unit_dir / pair.artifact
        schema_path = schemas_dir / pair.schema

        if not schema_path.is_file():
            missing_schemas.append(str(schema_path))
            continue

        if not artifact_path.is_file():
            missing_files.append(str(artifact_path))
            continue

        validated.append(str(artifact_path))
        errors.extend(_validate_json(artifact_path, schema_path))
        loaded = _load_json(artifact_path)
        if loaded is not None:
            artifacts[pair.artifact] = loaded

    if not missing_files and not missing_schemas and not errors:
        errors.extend(_cross_artifact_checks(unit_dir, artifacts))

    status = "PASS" if not missing_files and not missing_schemas and not errors else "BLOCK"
    payload = {
        "STATUS": status,
        "UNIT_DIR": str(unit_dir),
        "VALIDATED": validated,
        "MISSING_FILES": missing_files,
        "MISSING_SCHEMAS": missing_schemas,
        "ERRORS": errors,
    }

    if args.json:
        print(json.dumps(payload, separators=(",", ":")))
    else:
        print(f"STATUS: {status}")
        print(f"UNIT_DIR: {unit_dir}")
        print(f"VALIDATED: {len(validated)}")
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

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
