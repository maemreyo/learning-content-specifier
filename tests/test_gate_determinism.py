import json
import os
import shutil
import subprocess
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ID = "seed-gate-determinism"


def _run_setup_design(env: dict[str, str]) -> None:
    if os.name == "nt":
        cmd = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(ROOT / "factory/scripts/powershell/setup-design.ps1"),
            "-Json",
            "-ForceReset",
        ]
    else:
        cmd = ["bash", str(ROOT / "factory/scripts/bash/setup-design.sh"), "--json", "--force-reset"]
    subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)


def _run_gate_validator(env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess:
    if os.name == "nt":
        cmd = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(ROOT / "factory/scripts/powershell/validate-author-gates.ps1"),
            "-Json",
        ]
    else:
        cmd = ["bash", str(ROOT / "factory/scripts/bash/validate-author-gates.sh"), "--json"]
    return subprocess.run(cmd, cwd=ROOT, env=env, check=check, capture_output=True, text=True)


def _prepare_unit(unit_id: str) -> Path:
    unit_dir = ROOT / "programs" / PROGRAM_ID / "units" / unit_id
    if unit_dir.exists():
        shutil.rmtree(unit_dir)
    (unit_dir / "rubrics").mkdir(parents=True, exist_ok=True)
    (unit_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (unit_dir / "brief.json").write_text(
        json.dumps(
            {
                "contract_version": "1.0.0",
                "unit_id": unit_id,
                "title": unit_id,
                "audience": {
                    "primary": "general learners",
                    "entry_level": "beginner",
                    "delivery_context": "self-paced",
                },
                "duration_minutes": 60,
                "learning_outcomes": [
                    {
                        "lo_id": "LO1",
                        "priority": "P1",
                        "statement": "Learner will be able to demonstrate LO1 with measurable evidence.",
                        "evidence": "Assessment evidence mapped to LO1 is available in artifacts.",
                        "acceptance_criteria": [
                            "Given the learning context, When the learner attempts LO1 practice, Then observable evidence meets the completion criteria."
                        ],
                    }
                ],
                "scope": {"in_scope": [], "out_of_scope": []},
                "proficiency_targets": [],
                "assumptions": [],
                "risks": [],
                "refinement": {"open_questions": 0, "decisions": []},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return unit_dir


def test_gate_validator_passes_when_no_blockers_exist():
    unit_id = "995-gate-pass"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)
        audit_json_file = unit_dir / "audit-report.json"
        audit_data = json.loads(audit_json_file.read_text(encoding="utf-8"))
        audit_data["gate_decision"] = "PASS"
        audit_data["open_critical"] = 0
        audit_data["open_high"] = 0
        audit_data["findings"] = []
        audit_json_file.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["gate_status"] = {"decision": "PASS", "open_critical": 0, "open_high": 0}
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        rubric_gates_file = unit_dir / "rubric-gates.json"
        rubric_data = json.loads(rubric_gates_file.read_text(encoding="utf-8"))
        rubric_data["gates"] = [
            {
                "gate_id": "RB001",
                "group": "alignment",
                "status": "PASS",
                "severity": "LOW",
                "evidence": "design.json#LO1",
                "checked": True,
            }
        ]
        rubric_gates_file.write_text(json.dumps(rubric_data, indent=2), encoding="utf-8")
        rubric_checksum = hashlib.sha256(rubric_gates_file.read_bytes()).hexdigest()
        manifest_data["artifacts"] = [
            {
                **item,
                "checksum": f"sha256:{rubric_checksum}" if item.get("id") == "rubric-gates-json" else item.get("checksum"),
            }
            for item in manifest_data["artifacts"]
        ]
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_gate_validator(env)
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "PASS"
        assert payload["AUDIT_DECISION"] == "PASS"
        assert "CONTRACT_RESPONSE_VERSION" in payload
        assert "CONTRACT_PIPELINE" in payload
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_gate_validator_prefers_audit_json_over_markdown_when_conflicting():
    unit_id = "995-gate-json-priority"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)

        rubric_gates_file = unit_dir / "rubric-gates.json"
        rubric_data = json.loads(rubric_gates_file.read_text(encoding="utf-8"))
        rubric_data["gates"] = [
            {
                "gate_id": "RB001",
                "group": "alignment",
                "status": "PASS",
                "severity": "LOW",
                "evidence": "design.json#LO1",
                "checked": True,
            }
        ]
        rubric_gates_file.write_text(json.dumps(rubric_data, indent=2), encoding="utf-8")
        rubric_checksum = hashlib.sha256(rubric_gates_file.read_bytes()).hexdigest()
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["artifacts"] = [
            {
                **item,
                "checksum": f"sha256:{rubric_checksum}" if item.get("id") == "rubric-gates-json" else item.get("checksum"),
            }
            for item in manifest_data["artifacts"]
        ]
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        # Force audit json BLOCK to verify canonical json priority behavior.
        audit_json_file = unit_dir / "audit-report.json"
        audit_data = json.loads(audit_json_file.read_text(encoding="utf-8"))
        audit_data["gate_decision"] = "BLOCK"
        audit_data["open_high"] = 1
        audit_data["findings"] = [
            {
                "severity": "HIGH",
                "artifact": "design.json",
                "issue": "High severity unresolved",
                "remediation": "Resolve before authoring",
                "status": "OPEN",
            }
        ]
        audit_json_file.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")

        proc = _run_gate_validator(env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert payload["AUDIT_DECISION"] == "BLOCK"
        assert payload["AUDIT_OPEN_HIGH"] == 1
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_gate_validator_blocks_when_rubric_gates_json_has_invalid_pass_consistency():
    unit_id = "995-gate-rubric-json-consistency"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)

        # Force contract + audit to PASS so rubric parser is the blocker.
        audit_json_file = unit_dir / "audit-report.json"
        audit_data = json.loads(audit_json_file.read_text(encoding="utf-8"))
        audit_data["gate_decision"] = "PASS"
        audit_data["open_critical"] = 0
        audit_data["open_high"] = 0
        audit_data["findings"] = []
        audit_json_file.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")

        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["gate_status"] = {"decision": "PASS", "open_critical": 0, "open_high": 0}
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        rubric_gates_file = unit_dir / "rubric-gates.json"
        rubric_data = json.loads(rubric_gates_file.read_text(encoding="utf-8"))
        rubric_data["gates"] = [
            {
                "gate_id": "RB001",
                "group": "alignment",
                "status": "PASS",
                "severity": "LOW",
                "evidence": "pending",
                "checked": False,
            }
        ]
        rubric_gates_file.write_text(json.dumps(rubric_data, indent=2), encoding="utf-8")
        rubric_checksum = hashlib.sha256(rubric_gates_file.read_bytes()).hexdigest()
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["artifacts"] = [
            {
                **item,
                "checksum": f"sha256:{rubric_checksum}" if item.get("id") == "rubric-gates-json" else item.get("checksum"),
            }
            for item in manifest_data["artifacts"]
        ]
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_gate_validator(env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert payload["RUBRIC_PARSE_ERRORS"] == 0
        assert "Rubric format validation is BLOCK" in payload["BLOCKERS"]
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_gate_validator_blocks_when_required_json_gate_inputs_missing():
    unit_id = "995-gate-missing-json-inputs"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)
        (unit_dir / "rubric-gates.json").unlink(missing_ok=True)
        proc = _run_gate_validator(env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert "Rubric format validation is BLOCK" in payload["BLOCKERS"]
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)
