import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ID = "seed-pedagogy-decisions"


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


def test_design_decisions_defaults_match_corporate_lnd_profile():
    unit_id = "994-pedagogy-defaults"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)

        decisions = json.loads((unit_dir / "design-decisions.json").read_text(encoding="utf-8"))
        assert decisions["profile"] == "corporate-lnd-v1"
        assert decisions["weights"] == {
            "outcome_fit": 0.3,
            "evidence_fit": 0.25,
            "learner_fit": 0.2,
            "delivery_fit": 0.15,
            "accessibility_fit": 0.1,
        }
        assert decisions["confidence_threshold"] == 0.7
        assert len(decisions["selected_secondary"]) <= 2
        assert "retrieval-practice" in decisions["candidate_methods"]
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


def test_design_json_has_selection_rule_threshold_defaults():
    unit_id = "994-pedagogy-selection-rules"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)

        design_json = json.loads((unit_dir / "design.json").read_text(encoding="utf-8"))
        decisions = design_json["pedagogy_decisions"]
        assert decisions["profile"] == "corporate-lnd-v1"
        assert decisions["confidence_threshold"] == 0.7
        assert decisions["selection_rules"]["max_secondary_methods"] == 2
        assert decisions["selection_rules"]["score_delta_threshold"] == 0.4
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)
