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


def _run_contract_validator(unit_dir: Path, env: dict[str, str], check: bool = True) -> subprocess.CompletedProcess:
    if os.name == "nt":
        cmd = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(ROOT / "scripts/powershell/validate-artifact-contracts.ps1"),
            "-Json",
            "-UnitDir",
            str(unit_dir),
        ]
    else:
        cmd = [
            "bash",
            str(ROOT / "scripts/bash/validate-artifact-contracts.sh"),
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
