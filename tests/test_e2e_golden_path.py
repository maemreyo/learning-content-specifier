import json
import os
import shutil
import subprocess
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "golden_path_snapshot.json"
PROGRAM_ID = "seed-e2e-golden"


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


def _run_prereqs(env: dict[str, str]) -> dict:
    if os.name == "nt":
        cmd = [
            "pwsh",
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(ROOT / "factory/scripts/powershell/check-workflow-prereqs.ps1"),
            "-Json",
            "-IncludeSequence",
        ]
    else:
        cmd = [
            "bash",
            str(ROOT / "factory/scripts/bash/check-workflow-prereqs.sh"),
            "--json",
            "--include-sequence",
        ]

    result = subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    return json.loads(result.stdout.strip())


def _run_contract_validator(unit_dir: Path, env: dict[str, str]) -> dict:
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

    result = subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    return json.loads(result.stdout.strip())


def _run_gate_validator(env: dict[str, str]) -> dict:
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

    result = subprocess.run(cmd, cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    return json.loads(result.stdout.strip())


def _prepare_unit(unit_id: str) -> Path:
    unit_dir = ROOT / "programs" / PROGRAM_ID / "units" / unit_id
    if unit_dir.exists():
        shutil.rmtree(unit_dir)
    (unit_dir / "rubrics").mkdir(parents=True, exist_ok=True)
    (unit_dir / "outputs").mkdir(parents=True, exist_ok=True)
    (unit_dir / "brief.md").write_text("# brief\n", encoding="utf-8")
    (unit_dir / "design.md").write_text("# design\n", encoding="utf-8")
    (unit_dir / "sequence.md").write_text("# sequence\n", encoding="utf-8")
    return unit_dir


def test_e2e_golden_path_snapshot_contracts_and_gates():
    unit_id = "993-e2e-golden-path"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        # define/refine/design baseline
        _run_setup_design(env)
        exercise_design = json.loads((unit_dir / "exercise-design.json").read_text(encoding="utf-8"))
        exercise = exercise_design["exercises"][0]

        # sequence
        (unit_dir / "sequence.md").write_text(
            "# Sequence\n"
            f"- [ ] S001 [LO1] Author exercise {exercise['exercise_id']} in programs/{PROGRAM_ID}/units/993-e2e-golden-path/{exercise['target_path']}\n"
            "- [ ] S013 Run rubric and resolve blocking items\n",
            encoding="utf-8",
        )
        (unit_dir / "sequence.json").write_text(
            json.dumps(
                {
                    "contract_version": "1.0.0",
                    "unit_id": unit_id,
                    "tasks": [
                        {
                            "task_id": "S001",
                            "title": f"Author exercise {exercise['exercise_id']}",
                            "target_path": exercise["target_path"],
                            "status": "TODO",
                            "lo_refs": [exercise["lo_id"]],
                            "depends_on": [],
                            "exercise_id": exercise["exercise_id"],
                            "template_id": exercise["template_id"],
                        },
                        {
                            "task_id": "S013",
                            "title": "Run rubric checks",
                            "target_path": "rubrics/default.md",
                            "status": "TODO",
                            "lo_refs": ["LO1"],
                            "depends_on": ["S001"],
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # rubric
        (unit_dir / "rubrics" / "default.md").write_text(
            "- [x] Gate ID: RB001 | Group: alignment | Status: PASS | Severity: LOW | Evidence: design.md\n"
            "- [x] Gate ID: RB004 | Group: pedagogy | Status: PASS | Severity: LOW | Evidence: design.json\n",
            encoding="utf-8",
        )

        # audit
        (unit_dir / "audit-report.md").write_text(
            "# Audit Report: 993-e2e-golden-path\n"
            "Gate Decision: PASS\n"
            "Open Critical: 0\n"
            "Open High: 0\n"
            "## Findings\n"
            "1. LOW | artifact: design.md | issue: none | remediation: n/a\n",
            encoding="utf-8",
        )
        (unit_dir / "audit-report.json").write_text(
            json.dumps(
                {
                    "contract_version": "1.0.0",
                    "unit_id": unit_id,
                    "gate_decision": "PASS",
                    "open_critical": 0,
                    "open_high": 0,
                    "findings": [
                        {
                            "severity": "LOW",
                            "artifact": "design.md",
                            "issue": "none",
                            "remediation": "n/a",
                            "status": "RESOLVED",
                        }
                    ],
                    "role_readiness": {
                        "teacher_ready": True,
                        "creator_ready": True,
                        "ops_ready": True,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # author outputs + manifest update
        exercise_file = unit_dir / exercise["target_path"]
        exercise_file.parent.mkdir(parents=True, exist_ok=True)
        exercise_file.write_text("# Exercise EX001\n", encoding="utf-8")
        exercise_checksum = hashlib.sha256(exercise_file.read_bytes()).hexdigest()

        manifest_file = unit_dir / "outputs" / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest["gate_status"] = {"decision": "PASS", "open_critical": 0, "open_high": 0}
        manifest["artifacts"].append(
            {
                "id": "exercise-001-md",
                "type": "exercise",
                "path": exercise["target_path"],
                "media_type": "text/markdown",
                "checksum": f"sha256:{exercise_checksum}",
            }
        )
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        prereq_payload = _run_prereqs(env)
        contract_payload = _run_contract_validator(unit_dir, env)
        gate_payload = _run_gate_validator(env)
        assert contract_payload["RESPONSE_VERSION"] == "1.0.0"
        assert "AGENT_REPORT" in contract_payload
        assert "rerun_command" in contract_payload["AGENT_REPORT"]

        brief_json = json.loads((unit_dir / "brief.json").read_text(encoding="utf-8"))
        design_json = json.loads((unit_dir / "design.json").read_text(encoding="utf-8"))
        sequence_json = json.loads((unit_dir / "sequence.json").read_text(encoding="utf-8"))
        manifest_json = json.loads(manifest_file.read_text(encoding="utf-8"))

        required_files = sorted(
            [
                "brief.md",
                "brief.json",
                "design.md",
                "design.json",
                "exercise-design.md",
                "exercise-design.json",
                "content-model.md",
                "content-model.json",
                "design-decisions.json",
                "assessment-map.md",
                "delivery-guide.md",
                "sequence.md",
                "sequence.json",
                "rubrics/default.md",
                "audit-report.md",
                "audit-report.json",
                "outputs/manifest.json",
            ]
        )

        actual_snapshot = {
            "available_docs": sorted(prereq_payload["AVAILABLE_DOCS"]),
            "contract_status": contract_payload["STATUS"],
            "gate_status": gate_payload["STATUS"],
            "audit_decision": gate_payload["AUDIT_DECISION"],
            "required_files": required_files,
            "manifest_summary": {
                "decision": manifest_json["gate_status"]["decision"],
                "open_critical": manifest_json["gate_status"]["open_critical"],
                "open_high": manifest_json["gate_status"]["open_high"],
                "artifact_ids": sorted([item["id"] for item in manifest_json["artifacts"]]),
                "xapi_activity_count": len(manifest_json["interop"]["xapi"]["activity_id_set"]),
                "xapi_template_count": len(manifest_json["interop"]["xapi"]["statement_template_refs"]),
            },
            "brief_summary": {
                "lo_ids": [item["lo_id"] for item in brief_json["learning_outcomes"]],
                "priorities": [item["priority"] for item in brief_json["learning_outcomes"]],
                "all_acceptance_gwt": all(
                    all(token in criterion for token in ("Given", "When", "Then"))
                    for item in brief_json["learning_outcomes"]
                    for criterion in item["acceptance_criteria"]
                ),
            },
            "design_summary": {
                "profile": design_json["pedagogy_decisions"]["profile"],
                "confidence_threshold": design_json["pedagogy_decisions"]["confidence_threshold"],
                "max_secondary_methods": design_json["pedagogy_decisions"]["selection_rules"][
                    "max_secondary_methods"
                ],
                "score_delta_threshold": design_json["pedagogy_decisions"]["selection_rules"][
                    "score_delta_threshold"
                ],
            },
            "sequence_summary": {
                "task_count": len(sequence_json["tasks"]),
                "task_ids": [item["task_id"] for item in sequence_json["tasks"]],
            },
        }

        expected_snapshot = json.loads(FIXTURE.read_text(encoding="utf-8"))
        assert actual_snapshot == expected_snapshot
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)
