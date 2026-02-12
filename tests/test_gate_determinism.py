import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_setup_design(env: dict[str, str]) -> None:
    if os.name == "nt":
        cmd = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/powershell/setup-design.ps1"),
            "-Json",
        ]
    else:
        cmd = ["bash", str(ROOT / "scripts/bash/setup-design.sh"), "--json"]
    subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)


def _run_gate_validator(env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess:
    if os.name == "nt":
        cmd = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/powershell/validate-author-gates.ps1"),
            "-Json",
        ]
    else:
        cmd = ["bash", str(ROOT / "scripts/bash/validate-author-gates.sh"), "--json"]
    return subprocess.run(cmd, cwd=ROOT, env=env, check=check, capture_output=True, text=True)


def _prepare_unit(unit_id: str) -> Path:
    unit_dir = ROOT / "specs" / unit_id
    if unit_dir.exists():
        shutil.rmtree(unit_dir)
    (unit_dir / "rubrics").mkdir(parents=True, exist_ok=True)
    (unit_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (unit_dir / "brief.md").write_text("# brief\n", encoding="utf-8")
    (unit_dir / "design.md").write_text("# design\n", encoding="utf-8")
    (unit_dir / "sequence.md").write_text("# sequence\n", encoding="utf-8")
    (unit_dir / "audit-report.md").write_text(
        "# Audit Report\nGate Decision: PASS\nOpen Critical: 0\nOpen High: 0\n## Findings\n",
        encoding="utf-8",
    )
    (unit_dir / "rubrics" / "default.md").write_text(
        "- [x] Gate ID: RB001 | Group: alignment | Status: PASS | Severity: LOW | Evidence: design.md\n",
        encoding="utf-8",
    )
    return unit_dir


def test_gate_validator_passes_when_no_blockers_exist():
    unit_id = "995-gate-pass"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

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

        proc = _run_gate_validator(env)
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "PASS"
        assert payload["AUDIT_DECISION"] == "PASS"
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_gate_validator_prefers_audit_json_over_markdown_when_conflicting():
    unit_id = "995-gate-json-priority"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)

        # Keep markdown PASS but force json BLOCK to verify json-priority gate behavior.
        (unit_dir / "audit-report.md").write_text(
            "# Audit Report\nGate Decision: PASS\nOpen Critical: 0\nOpen High: 0\n## Findings\n",
            encoding="utf-8",
        )
        audit_json_file = unit_dir / "audit-report.json"
        audit_data = json.loads(audit_json_file.read_text(encoding="utf-8"))
        audit_data["gate_decision"] = "BLOCK"
        audit_data["open_high"] = 1
        audit_data["findings"] = [
            {
                "severity": "HIGH",
                "artifact": "design.md",
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


def test_gate_validator_blocks_when_rubric_line_is_not_parseable():
    unit_id = "995-gate-rubric-parse-error"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

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

        (unit_dir / "rubrics" / "default.md").write_text(
            "- [x] Gate ID: RB001 | Group alignment | Status PASS | Severity LOW | Evidence design.md\n",
            encoding="utf-8",
        )

        proc = _run_gate_validator(env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert payload["RUBRIC_PARSE_ERRORS"] > 0
        assert "Rubric format validation is BLOCK" in payload["BLOCKERS"]
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)
