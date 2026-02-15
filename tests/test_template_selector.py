import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ID = "seed-template-selector"
SELECTOR = ROOT / "factory/scripts/python/generate_template_selection.py"
PACK_DIR = ROOT.parent / "subjects" / "english" / ".lcs" / "template-pack" / "v1"


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


def _run_selector(unit_dir: Path, env: dict[str, str]) -> dict:
    cmd = [
        "uv",
        "run",
        "python",
        str(SELECTOR),
        "--repo-root",
        str(ROOT),
        "--unit-dir",
        str(unit_dir),
        "--json",
    ]
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


@pytest.mark.skipif(not PACK_DIR.is_dir(), reason="english template pack missing")
def test_template_selector_is_deterministic_for_same_inputs() -> None:
    unit_id = "992-template-selector-deterministic"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)
        first = _run_selector(unit_dir, env)
        second = _run_selector(unit_dir, env)

        assert first["STATUS"] == "PASS"
        assert second["STATUS"] == "PASS"

        selection_file = unit_dir / "template-selection.json"
        selection_payload = json.loads(selection_file.read_text(encoding="utf-8"))
        assert isinstance(selection_payload.get("selected_templates"), list)
        assert len(selection_payload["selected_templates"]) == selection_payload["top_k"]
        for item in selection_payload["selected_templates"]:
            breakdown = item.get("score_breakdown", {})
            assert set(breakdown.keys()) == {"proficiency_fit", "lo_fit", "level_fit", "duration_fit", "diversity_fit"}

        snapshot_a = json.dumps(selection_payload, sort_keys=True)
        _run_selector(unit_dir, env)
        snapshot_b = json.dumps(json.loads(selection_file.read_text(encoding="utf-8")), sort_keys=True)
        assert snapshot_a == snapshot_b
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


@pytest.mark.skipif(not PACK_DIR.is_dir(), reason="english template pack missing")
def test_template_selector_prioritizes_sentence_rewrite_for_rewrite_focused_lo() -> None:
    unit_id = "992-template-selector-rewrite-bias"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)
        brief_file = unit_dir / "brief.json"
        brief = json.loads(brief_file.read_text(encoding="utf-8"))
        brief["learning_outcomes"][0]["statement"] = "Learner rewrites a sentence while preserving meaning."
        brief["learning_outcomes"][0]["evidence"] = "Assess sentence transformation and meaning preservation."
        brief_file.write_text(json.dumps(brief, indent=2), encoding="utf-8")

        _run_selector(unit_dir, env)
        selection = json.loads((unit_dir / "template-selection.json").read_text(encoding="utf-8"))
        top_template = selection["selected_templates"][0]["template_id"]
        assert top_template == "sentence-rewrite.v1"
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)


@pytest.mark.skipif(not PACK_DIR.is_dir(), reason="english template pack missing")
def test_template_selector_prefers_speaking_templates_for_ielts_speaking_target() -> None:
    unit_id = "992-template-selector-ielts-speaking"
    unit_dir = _prepare_unit(unit_id)
    env = os.environ.copy()
    env["LCS_UNIT"] = unit_id
    env["LCS_PROGRAM"] = PROGRAM_ID

    try:
        _run_setup_design(env)
        brief_file = unit_dir / "brief.json"
        brief = json.loads(brief_file.read_text(encoding="utf-8"))
        brief["proficiency_targets"] = [
            {
                "framework_id": "ielts.v1",
                "scale_id": "band",
                "dimension": "speaking",
                "target": {"value": 7.5},
                "priority": "P1",
                "provenance": "test",
            }
        ]
        brief["learning_outcomes"][0]["statement"] = "Learner will be able to express and justify an opinion in spoken English."
        brief["learning_outcomes"][0]["evidence"] = "Assess spoken opinion quality, coherence, and appropriate language use."
        brief_file.write_text(json.dumps(brief, indent=2), encoding="utf-8")

        _run_selector(unit_dir, env)
        selection = json.loads((unit_dir / "template-selection.json").read_text(encoding="utf-8"))
        top_template = selection["selected_templates"][0]["template_id"]
        speaking_templates = {
            "oral-interview-qa.v1",
            "cue-card-long-turn.v1",
            "collaborative-discussion.v1",
            "read-aloud.v1",
            "describe-picture.v1",
            "repeat-sentence.v1",
            "retell-lecture.v1",
            "answer-short-question.v1",
            "respond-to-information.v1",
            "speak-opinion-long-turn.v1",
        }
        assert top_template in speaking_templates
    finally:
        shutil.rmtree(unit_dir, ignore_errors=True)
