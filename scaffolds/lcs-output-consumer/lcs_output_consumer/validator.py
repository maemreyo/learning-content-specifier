from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .api_models import ArtifactStatus, GateSnapshot, UnitMetadata, UnitValidationResult, ValidationIssue
from .contract_sync import ContractBundle


REQUIRED_CONTRACTS: tuple[tuple[str, str], ...] = (
    ("brief.json", "brief.schema.json"),
    ("design.json", "design.schema.json"),
    ("sequence.json", "sequence.schema.json"),
    ("audit-report.json", "audit-report.schema.json"),
    ("outputs/manifest.json", "manifest.schema.json"),
)


def validate_unit(unit_path: Path, bundle: ContractBundle) -> UnitValidationResult:
    unit_path = unit_path.resolve()
    issues: list[ValidationIssue] = []
    payloads: dict[str, dict[str, Any] | list[Any]] = {}

    for artifact_name, schema_name in REQUIRED_CONTRACTS:
        artifact_path = unit_path / artifact_name
        schema_payload = bundle.schemas.get(schema_name)

        if schema_payload is None:
            issues.append(
                _issue(
                    code="IO_CONTRACT_SCHEMA_MISSING",
                    category="IO",
                    message=f"Missing schema in contract bundle: {schema_name}",
                    artifact=artifact_name,
                )
            )
            continue

        if not artifact_path.is_file():
            issues.append(
                _issue(
                    code="IO_ARTIFACT_MISSING",
                    category="IO",
                    message=f"Missing required artifact: {artifact_path}",
                    artifact=artifact_name,
                )
            )
            continue

        try:
            artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            payloads[artifact_name] = artifact_payload
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            issues.append(
                _issue(
                    code="IO_ARTIFACT_INVALID_JSON",
                    category="IO",
                    message=f"Invalid JSON in {artifact_path}: {exc}",
                    artifact=artifact_name,
                )
            )
            continue

        validator = Draft202012Validator(schema_payload)
        for error in sorted(validator.iter_errors(artifact_payload), key=str):
            location = "/".join(str(part) for part in error.path) or "<root>"
            issues.append(
                _issue(
                    code="SCHEMA_VALIDATION_FAILED",
                    category="SCHEMA",
                    message=f"{artifact_name}:{location}: {error.message}",
                    artifact=artifact_name,
                )
            )

    if not issues:
        issues.extend(_cross_artifact_checks(unit_path, payloads))

    manifest = payloads.get("outputs/manifest.json")
    artifacts = _artifact_statuses(unit_path, manifest if isinstance(manifest, dict) else None)
    gates = _gate_snapshot(payloads, issues)
    metadata = _metadata_snapshot(payloads)

    unit_id = _derive_unit_id(unit_path, payloads)
    status = "PASS" if not issues else "BLOCK"

    return UnitValidationResult(
        unit_id=unit_id,
        unit_path=str(unit_path),
        status=status,
        issues=issues,
        gates=gates,
        artifacts=artifacts,
        metadata=metadata,
        manifest=manifest if isinstance(manifest, dict) else None,
    )


def _cross_artifact_checks(
    unit_path: Path,
    payloads: dict[str, dict[str, Any] | list[Any]],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected_unit_id = unit_path.name

    for artifact_name, payload in payloads.items():
        if not isinstance(payload, dict):
            continue
        unit_id = payload.get("unit_id")
        if isinstance(unit_id, str) and unit_id != expected_unit_id:
            issues.append(
                _issue(
                    code="CONSISTENCY_UNIT_ID_MISMATCH",
                    category="CONSISTENCY",
                    message=f"{artifact_name} unit_id '{unit_id}' != '{expected_unit_id}'",
                    artifact=artifact_name,
                )
            )

    brief = payloads.get("brief.json")
    sequence = payloads.get("sequence.json")
    audit = payloads.get("audit-report.json")
    manifest = payloads.get("outputs/manifest.json")

    brief_los: set[str] = set()
    brief_priorities: dict[str, str] = {}
    if isinstance(brief, dict):
        learning_outcomes = brief.get("learning_outcomes", [])
        if isinstance(learning_outcomes, list):
            for item in learning_outcomes:
                if not isinstance(item, dict):
                    continue
                lo_id = item.get("lo_id")
                priority = item.get("priority")
                if isinstance(lo_id, str):
                    brief_los.add(lo_id)
                    if isinstance(priority, str):
                        brief_priorities[lo_id] = priority

    if isinstance(sequence, dict) and brief_los:
        tasks = sequence.get("tasks", [])
        if isinstance(tasks, list):
            task_ids = {
                item.get("task_id")
                for item in tasks
                if isinstance(item, dict) and isinstance(item.get("task_id"), str)
            }
            graph: dict[str, list[str]] = {}
            for idx, task in enumerate(tasks):
                if not isinstance(task, dict):
                    continue
                task_id = task.get("task_id")
                if not isinstance(task_id, str):
                    continue

                lo_refs = task.get("lo_refs", [])
                if isinstance(lo_refs, list):
                    unknown = sorted(
                        ref for ref in lo_refs if isinstance(ref, str) and ref not in brief_los
                    )
                    if unknown:
                        issues.append(
                            _issue(
                                code="CONSISTENCY_UNKNOWN_LO_REF",
                                category="CONSISTENCY",
                                message=f"sequence task {task_id} references unknown LO ids: {unknown}",
                                artifact="sequence.json",
                            )
                        )

                depends_on = task.get("depends_on", [])
                deps: list[str] = []
                if isinstance(depends_on, list):
                    for dep in depends_on:
                        if not isinstance(dep, str):
                            continue
                        deps.append(dep)
                        if dep not in task_ids:
                            issues.append(
                                _issue(
                                    code="CONSISTENCY_UNKNOWN_TASK_DEP",
                                    category="CONSISTENCY",
                                    message=f"sequence task {task_id} has unknown dependency: {dep}",
                                    artifact="sequence.json",
                                )
                            )
                        if dep == task_id:
                            issues.append(
                                _issue(
                                    code="CONSISTENCY_SELF_DEPENDENCY",
                                    category="CONSISTENCY",
                                    message=f"sequence task {task_id} depends on itself",
                                    artifact="sequence.json",
                                )
                            )
                graph[task_id] = deps

            if _has_cycle(graph):
                issues.append(
                    _issue(
                        code="CONSISTENCY_SEQUENCE_CYCLE",
                        category="CONSISTENCY",
                        message="sequence task dependency graph has a cycle",
                        artifact="sequence.json",
                    )
                )

    if isinstance(manifest, dict):
        outcomes = manifest.get("outcomes", [])
        manifest_los: set[str] = set()
        manifest_priorities: dict[str, str] = {}
        if isinstance(outcomes, list):
            for idx, item in enumerate(outcomes):
                if not isinstance(item, dict):
                    continue
                lo_id = item.get("lo_id")
                priority = item.get("priority")
                evidence_refs = item.get("evidence_refs", [])
                if isinstance(lo_id, str):
                    manifest_los.add(lo_id)
                    if isinstance(priority, str):
                        manifest_priorities[lo_id] = priority
                    expected_ref = f"brief:{lo_id}"
                    if isinstance(evidence_refs, list) and expected_ref not in evidence_refs:
                        issues.append(
                            _issue(
                                code="CONSISTENCY_MISSING_BRIEF_EVIDENCE_REF",
                                category="CONSISTENCY",
                                message=f"manifest outcome {lo_id} missing evidence ref '{expected_ref}'",
                                artifact="outputs/manifest.json",
                            )
                        )

        if brief_los and manifest_los != brief_los:
            issues.append(
                _issue(
                    code="CONSISTENCY_LO_SET_MISMATCH",
                    category="CONSISTENCY",
                    message=(
                        f"manifest LO ids {sorted(manifest_los)} must match brief LO ids {sorted(brief_los)}"
                    ),
                    artifact="outputs/manifest.json",
                )
            )

        for lo_id, priority in brief_priorities.items():
            manifest_priority = manifest_priorities.get(lo_id)
            if manifest_priority and manifest_priority != priority:
                issues.append(
                    _issue(
                        code="CONSISTENCY_LO_PRIORITY_MISMATCH",
                        category="CONSISTENCY",
                        message=f"manifest priority for {lo_id} ({manifest_priority}) != brief ({priority})",
                        artifact="outputs/manifest.json",
                    )
                )

        artifacts = manifest.get("artifacts", [])
        if isinstance(artifacts, list):
            seen_ids: set[str] = set()
            seen_paths: set[str] = set()
            for idx, item in enumerate(artifacts):
                if not isinstance(item, dict):
                    continue
                artifact_id = item.get("id")
                rel_path = item.get("path")
                checksum = item.get("checksum")

                if isinstance(artifact_id, str):
                    if artifact_id in seen_ids:
                        issues.append(
                            _issue(
                                code="CONSISTENCY_DUP_ARTIFACT_ID",
                                category="CONSISTENCY",
                                message=f"manifest duplicate artifact id: {artifact_id}",
                                artifact="outputs/manifest.json",
                            )
                        )
                    seen_ids.add(artifact_id)

                if not isinstance(rel_path, str):
                    continue
                if rel_path in seen_paths:
                    issues.append(
                        _issue(
                            code="CONSISTENCY_DUP_ARTIFACT_PATH",
                            category="CONSISTENCY",
                            message=f"manifest duplicate artifact path: {rel_path}",
                            artifact="outputs/manifest.json",
                        )
                    )
                seen_paths.add(rel_path)

                resolved = (unit_path / rel_path).resolve()
                try:
                    resolved.relative_to(unit_path)
                except ValueError:
                    issues.append(
                        _issue(
                            code="IO_PATH_ESCAPE",
                            category="IO",
                            message=f"manifest artifact path escapes unit: {rel_path}",
                            artifact="outputs/manifest.json",
                        )
                    )
                    continue

                if not resolved.is_file():
                    issues.append(
                        _issue(
                            code="IO_ARTIFACT_PATH_MISSING",
                            category="IO",
                            message=f"manifest artifact missing on disk: {rel_path}",
                            artifact="outputs/manifest.json",
                        )
                    )
                    continue

                if isinstance(checksum, str) and checksum.lower().startswith("sha256:"):
                    actual = _sha256_file(resolved)
                    expected = checksum.split(":", 1)[1].lower()
                    if actual != expected:
                        issues.append(
                            _issue(
                                code="CONSISTENCY_CHECKSUM_MISMATCH",
                                category="CONSISTENCY",
                                message=f"checksum mismatch for artifact path: {rel_path}",
                                artifact="outputs/manifest.json",
                            )
                        )

    if isinstance(audit, dict) and isinstance(manifest, dict):
        gate = manifest.get("gate_status", {})
        audit_decision = audit.get("gate_decision")
        gate_decision = gate.get("decision") if isinstance(gate, dict) else None

        if isinstance(audit_decision, str) and isinstance(gate_decision, str) and audit_decision != gate_decision:
            issues.append(
                _issue(
                    code="GATE_DECISION_MISMATCH",
                    category="GATE",
                    message=f"audit gate_decision {audit_decision} != manifest gate_status {gate_decision}",
                    artifact="audit-report.json",
                )
            )

        if isinstance(gate, dict):
            if audit.get("open_critical") != gate.get("open_critical") or audit.get("open_high") != gate.get("open_high"):
                issues.append(
                    _issue(
                        code="GATE_COUNTER_MISMATCH",
                        category="GATE",
                        message="audit open counters must match manifest gate counters",
                        artifact="audit-report.json",
                    )
                )

        findings = audit.get("findings", [])
        if isinstance(findings, list):
            open_critical = 0
            open_high = 0
            for finding in findings:
                if not isinstance(finding, dict):
                    continue
                status = finding.get("status")
                severity = finding.get("severity")
                if status == "OPEN" and severity == "CRITICAL":
                    open_critical += 1
                if status == "OPEN" and severity == "HIGH":
                    open_high += 1

            if audit.get("open_critical") != open_critical:
                issues.append(
                    _issue(
                        code="GATE_CRITICAL_COUNT_MISMATCH",
                        category="GATE",
                        message=f"audit open_critical must equal OPEN/CRITICAL findings ({open_critical})",
                        artifact="audit-report.json",
                    )
                )

            if audit.get("open_high") != open_high:
                issues.append(
                    _issue(
                        code="GATE_HIGH_COUNT_MISMATCH",
                        category="GATE",
                        message=f"audit open_high must equal OPEN/HIGH findings ({open_high})",
                        artifact="audit-report.json",
                    )
                )

            if audit.get("gate_decision") == "PASS" and (open_critical > 0 or open_high > 0):
                issues.append(
                    _issue(
                        code="GATE_PASS_WITH_OPEN_HIGH_SEVERITY",
                        category="GATE",
                        message="audit gate_decision PASS is invalid with OPEN CRITICAL/HIGH findings",
                        artifact="audit-report.json",
                    )
                )

    return issues


def _artifact_statuses(unit_path: Path, manifest: dict[str, Any] | None) -> list[ArtifactStatus]:
    statuses: list[ArtifactStatus] = []
    if manifest is None:
        return statuses

    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list):
        return statuses

    for item in artifacts:
        if not isinstance(item, dict):
            continue
        rel_path = item.get("path")
        if not isinstance(rel_path, str):
            continue

        resolved = (unit_path / rel_path).resolve()
        exists = False
        checksum_ok: bool | None = None
        try:
            resolved.relative_to(unit_path)
            exists = resolved.is_file()
        except ValueError:
            exists = False

        checksum = str(item.get("checksum", ""))
        if exists and checksum.lower().startswith("sha256:"):
            checksum_ok = _sha256_file(resolved) == checksum.split(":", 1)[1].lower()

        statuses.append(
            ArtifactStatus(
                id=str(item.get("id", "")),
                type=str(item.get("type", "")),
                path=rel_path,
                media_type=str(item.get("media_type", "")),
                checksum=checksum,
                exists=exists,
                checksum_ok=checksum_ok,
            )
        )

    return statuses


def _gate_snapshot(
    payloads: dict[str, dict[str, Any] | list[Any]],
    issues: list[ValidationIssue],
) -> GateSnapshot:
    manifest = payloads.get("outputs/manifest.json")
    audit = payloads.get("audit-report.json")

    decision = "BLOCK"
    open_critical = 0
    open_high = 0
    audit_decision = "UNKNOWN"

    if isinstance(manifest, dict):
        gate = manifest.get("gate_status", {})
        if isinstance(gate, dict):
            raw_decision = gate.get("decision")
            if raw_decision in {"PASS", "BLOCK"}:
                decision = raw_decision
            open_critical = int(gate.get("open_critical", 0) or 0)
            open_high = int(gate.get("open_high", 0) or 0)

    if isinstance(audit, dict):
        raw = audit.get("gate_decision")
        if raw in {"PASS", "BLOCK"}:
            audit_decision = raw

    hard_block = any(issue.category == "GATE" for issue in issues)
    hard_block = hard_block or open_critical > 0 or open_high > 0
    authoring_eligible = (decision == "PASS") and not hard_block and not issues

    return GateSnapshot(
        decision="PASS" if authoring_eligible else "BLOCK",
        open_critical=open_critical,
        open_high=open_high,
        authoring_eligible=authoring_eligible,
        audit_decision=audit_decision,
    )


def _metadata_snapshot(payloads: dict[str, dict[str, Any] | list[Any]]) -> UnitMetadata:
    brief = payloads.get("brief.json")
    design = payloads.get("design.json")

    entry_level: str | None = None
    modality: str | None = None
    duration_minutes: int | None = None

    if isinstance(brief, dict):
        audience = brief.get("audience", {})
        if isinstance(audience, dict):
            value = audience.get("entry_level")
            if isinstance(value, str):
                entry_level = value
        duration = brief.get("duration_minutes")
        if isinstance(duration, int):
            duration_minutes = duration

    if isinstance(design, dict):
        metadata = design.get("metadata", {})
        if isinstance(metadata, dict):
            value = metadata.get("modality")
            if isinstance(value, str):
                modality = value
            if duration_minutes is None:
                duration = metadata.get("duration_minutes")
                if isinstance(duration, int):
                    duration_minutes = duration

    return UnitMetadata(entry_level=entry_level, modality=modality, duration_minutes=duration_minutes)


def _derive_unit_id(unit_path: Path, payloads: dict[str, dict[str, Any] | list[Any]]) -> str:
    manifest = payloads.get("outputs/manifest.json")
    if isinstance(manifest, dict):
        unit_id = manifest.get("unit_id")
        if isinstance(unit_id, str) and unit_id:
            return unit_id
    return unit_path.name


def _issue(code: str, category: str, message: str, artifact: str | None = None) -> ValidationIssue:
    return ValidationIssue(code=code, category=category, message=message, artifact=artifact)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        current = state.get(node, 0)
        if current == 1:
            return True
        if current == 2:
            return False

        state[node] = 1
        for child in graph.get(node, []):
            if child in graph and visit(child):
                return True
        state[node] = 2
        return False

    for node in graph:
        if state.get(node, 0) == 0 and visit(node):
            return True
    return False
