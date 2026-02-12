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
            str(ROOT / "factory/scripts/powershell/setup-design.ps1"),
            "-Json",
        ]
    else:
        cmd = ["bash", str(ROOT / "factory/scripts/bash/setup-design.sh"), "--json"]
    subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)


def _run_contract_validator(unit_dir: Path, env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess:
    if os.name == "nt":
        cmd = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(ROOT / "factory/scripts/powershell/validate-artifact-contracts.ps1"),
            "-Json",
            "-UnitDir",
            str(unit_dir),
        ]
    else:
        cmd = [
            "bash",
            str(ROOT / "factory/scripts/bash/validate-artifact-contracts.sh"),
            "--json",
            "--unit-dir",
            str(unit_dir),
        ]
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


def test_artifact_contract_validator_passes_for_generated_contracts():
    unit_id = "996-artifact-contract-pass"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        proc = _run_contract_validator(unit_dir, env)
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "PASS"
        assert len(payload["VALIDATED"]) >= 5
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_without_xapi_manifest_block():
    unit_id = "996-artifact-contract-block"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data.setdefault("interop", {}).pop("xapi", None)
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_with_unsupported_xapi_version():
    unit_id = "996-artifact-contract-xapi-version"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["interop"]["xapi"]["version"] = "3.0.0"
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("interop/xapi/version" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_accepts_xapi_v1_and_v2_versions():
    unit_id = "996-artifact-contract-xapi-supported-versions"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))

        manifest_data["interop"]["xapi"]["version"] = "1.0.3"
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        proc_v1 = _run_contract_validator(unit_dir, env)
        payload_v1 = json.loads(proc_v1.stdout.strip())
        assert payload_v1["STATUS"] == "PASS"

        manifest_data["interop"]["xapi"]["version"] = "2.0.0"
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        proc_v2 = _run_contract_validator(unit_dir, env)
        payload_v2 = json.loads(proc_v2.stdout.strip())
        assert payload_v2["STATUS"] == "PASS"
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_when_brief_has_no_p1_outcome():
    unit_id = "996-artifact-contract-no-p1"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        brief_file = unit_dir / "brief.json"
        manifest_file = unit_dir / "outputs" / "manifest.json"

        brief_data = json.loads(brief_file.read_text(encoding="utf-8"))
        brief_data["learning_outcomes"][0]["priority"] = "P2"
        brief_file.write_text(json.dumps(brief_data, indent=2), encoding="utf-8")

        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["outcomes"][0]["priority"] = "P2"
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("learning_outcomes" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_when_sequence_has_unknown_dependency():
    unit_id = "996-artifact-contract-sequence-unknown-dependency"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        sequence_file = unit_dir / "sequence.json"
        sequence_data = json.loads(sequence_file.read_text(encoding="utf-8"))
        sequence_data["tasks"] = [
            {
                "task_id": "S001",
                "title": "Draft lesson",
                "target_path": "outputs/module-01/lesson-01.md",
                "status": "TODO",
                "lo_refs": ["LO1"],
                "depends_on": ["S099"],
            }
        ]
        sequence_file.write_text(json.dumps(sequence_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("unknown dependencies" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_when_sequence_has_dependency_cycle():
    unit_id = "996-artifact-contract-sequence-cycle"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        sequence_file = unit_dir / "sequence.json"
        sequence_data = json.loads(sequence_file.read_text(encoding="utf-8"))
        sequence_data["tasks"] = [
            {
                "task_id": "S001",
                "title": "Draft lesson",
                "target_path": "outputs/module-01/lesson-01.md",
                "status": "TODO",
                "lo_refs": ["LO1"],
                "depends_on": ["S002"],
            },
            {
                "task_id": "S002",
                "title": "Review lesson",
                "target_path": "outputs/module-01/review.md",
                "status": "TODO",
                "lo_refs": ["LO1"],
                "depends_on": ["S001"],
            },
        ]
        sequence_file.write_text(json.dumps(sequence_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("dependency cycle detected" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_when_manifest_lo_mismatch_brief():
    unit_id = "996-artifact-contract-lo-mismatch"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["outcomes"] = [
            {
                "lo_id": "LO2",
                "priority": "P1",
                "evidence_refs": ["brief:LO2"],
            }
        ]
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("must exactly match brief LO IDs" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_when_manifest_priority_mismatch_brief():
    unit_id = "996-artifact-contract-priority-mismatch"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["outcomes"][0]["priority"] = "P3"
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("must match brief priority" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_when_manifest_checksum_mismatch():
    unit_id = "996-artifact-contract-checksum-mismatch"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest_data["artifacts"][0]["checksum"] = (
            "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("checksum mismatch" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_artifact_contract_validator_blocks_when_audit_open_counts_mismatch_findings():
    unit_id = "996-artifact-contract-audit-count-mismatch"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id

    try:
        _run_setup_design(env)
        audit_json_file = unit_dir / "audit-report.json"
        audit_data = json.loads(audit_json_file.read_text(encoding="utf-8"))
        audit_data["findings"] = [
            {
                "severity": "HIGH",
                "artifact": "design.md",
                "issue": "Unresolved high issue.",
                "remediation": "Resolve before authoring.",
                "status": "OPEN",
            }
        ]
        audit_data["open_high"] = 0
        audit_json_file.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")

        proc = _run_contract_validator(unit_dir, env, check=False)
        assert proc.returncode != 0
        payload = json.loads(proc.stdout.strip())
        assert payload["STATUS"] == "BLOCK"
        assert any("must match OPEN HIGH findings count" in msg for msg in payload["ERRORS"])
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)
