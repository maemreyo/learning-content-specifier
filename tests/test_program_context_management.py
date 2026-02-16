import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name == "nt", reason="Bash workflow test")
def test_ensure_program_context_does_not_reuse_unrelated_current_program(tmp_path: Path):
    repo = tmp_path / "repo"
    scripts_dir = repo / ".lcs" / "scripts" / "bash"
    generic_scripts_dir = repo / ".lcs" / "scripts"
    config_dir = repo / ".lcs" / "config"
    templates_dir = repo / ".lcs" / "templates"
    context_dir = repo / ".lcs" / "context"
    programs_dir = repo / "programs"

    scripts_dir.mkdir(parents=True)
    generic_scripts_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True)
    context_dir.mkdir(parents=True)
    programs_dir.mkdir(parents=True)

    shutil.copy(ROOT / "factory/scripts/bash/common.sh", scripts_dir / "common.sh")
    shutil.copy(ROOT / "factory/scripts/bash/ensure-program-context.sh", scripts_dir / "ensure-program-context.sh")
    shutil.copy(ROOT / "factory/scripts/bash/load-stage-context.sh", scripts_dir / "load-stage-context.sh")
    shutil.copy(ROOT / "factory/scripts/python/load_stage_context.py", generic_scripts_dir / "load_stage_context.py")
    shutil.copy(ROOT / "factory/scripts/python/manage_program_context.py", generic_scripts_dir / "manage_program_context.py")
    shutil.copy(ROOT / "factory/config/stage-context-map.v1.json", config_dir / "stage-context-map.v1.json")
    shutil.copy(ROOT / "factory/templates/charter-template.md", templates_dir / "charter-template.md")

    current_program = "ielts-speaking-5-0-to-6-5-in-30-days-20260215-1834"
    (programs_dir / current_program / "units").mkdir(parents=True)
    (programs_dir / current_program / "program.json").write_text(
        json.dumps({"program_id": current_program, "title": "Speaking", "status": "draft"}),
        encoding="utf-8",
    )
    (context_dir / "current-program").write_text(current_program, encoding="utf-8")

    cmd = ["bash", str(scripts_dir / "ensure-program-context.sh"), "--json", "IELTS Writing 5.0 to 7.5 in 30 days"]
    result = subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout.strip())

    assert payload["PROGRAM_ID"] != current_program
    assert payload["PROGRAM_ID"].startswith("ielts-writing-5-0-to-7-5-in-30-days-")
    assert (context_dir / "current-program").read_text(encoding="utf-8").strip() == payload["PROGRAM_ID"]


@pytest.mark.skipif(os.name == "nt", reason="Bash workflow test")
def test_manage_program_context_recommend_activate_and_list_units(tmp_path: Path):
    repo = tmp_path / "repo"
    bash_scripts_dir = repo / ".lcs" / "scripts" / "bash"
    generic_scripts_dir = repo / ".lcs" / "scripts"
    context_dir = repo / ".lcs" / "context"
    programs_dir = repo / "programs"

    bash_scripts_dir.mkdir(parents=True)
    generic_scripts_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True)
    programs_dir.mkdir(parents=True)

    shutil.copy(ROOT / "factory/scripts/bash/common.sh", bash_scripts_dir / "common.sh")
    shutil.copy(ROOT / "factory/scripts/bash/manage-program-context.sh", bash_scripts_dir / "manage-program-context.sh")
    shutil.copy(ROOT / "factory/scripts/python/manage_program_context.py", generic_scripts_dir / "manage_program_context.py")

    writing = "ielts-writing-5-0-to-7-5-in-30-days-20260215-2122"
    speaking = "ielts-speaking-5-0-to-6-5-in-30-days-20260215-1834"

    (programs_dir / writing / "units" / "001-unit-a").mkdir(parents=True)
    (programs_dir / writing / "units" / "002-unit-b").mkdir(parents=True)
    (programs_dir / writing / "program.json").write_text(
        json.dumps({"program_id": writing, "title": "Writing", "status": "draft"}), encoding="utf-8"
    )

    (programs_dir / speaking / "units" / "001-speaking").mkdir(parents=True)
    (programs_dir / speaking / "program.json").write_text(
        json.dumps({"program_id": speaking, "title": "Speaking", "status": "draft"}), encoding="utf-8"
    )

    (context_dir / "current-program").write_text(speaking, encoding="utf-8")
    (context_dir / "current-unit").write_text("001-speaking", encoding="utf-8")

    script = bash_scripts_dir / "manage-program-context.sh"

    recommend_cmd = [
        "bash",
        str(script),
        "--json",
        "recommend",
        "--intent",
        "IELTS Writing 5.0 to 7.5 in 30 days",
    ]
    recommend = subprocess.run(recommend_cmd, cwd=repo, check=True, capture_output=True, text=True)
    recommend_payload = json.loads(recommend.stdout.strip())
    assert recommend_payload["recommended_action"] in {"activate-existing", "choose-existing", "reuse-current", "create-new"}
    assert recommend_payload["program_id"].startswith("ielts-writing-5-0-to-7-5-in-30-days")

    activate_cmd = [
        "bash",
        str(script),
        "--json",
        "activate",
        "--program",
        writing,
        "--unit",
        "002-unit-b",
    ]
    activate = subprocess.run(activate_cmd, cwd=repo, check=True, capture_output=True, text=True)
    activate_payload = json.loads(activate.stdout.strip())
    assert activate_payload["program_id"] == writing
    assert activate_payload["unit_id"] == "002-unit-b"

    assert (context_dir / "current-program").read_text(encoding="utf-8").strip() == writing
    assert (context_dir / "current-unit").read_text(encoding="utf-8").strip() == "002-unit-b"

    units_cmd = ["bash", str(script), "--json", "list-units", "--program", writing]
    units = subprocess.run(units_cmd, cwd=repo, check=True, capture_output=True, text=True)
    units_payload = json.loads(units.stdout.strip())

    assert units_payload["program_id"] == writing
    assert any(unit["unit_id"] == "002-unit-b" and unit["is_active"] for unit in units_payload["units"])


@pytest.mark.skipif(os.name == "nt", reason="Bash workflow test")
def test_manage_program_context_workflow_status_generates_follow_up_tasks(tmp_path: Path):
    repo = tmp_path / "repo"
    bash_scripts_dir = repo / ".lcs" / "scripts" / "bash"
    generic_scripts_dir = repo / ".lcs" / "scripts"
    context_dir = repo / ".lcs" / "context"
    programs_dir = repo / "programs"

    bash_scripts_dir.mkdir(parents=True)
    generic_scripts_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True)
    programs_dir.mkdir(parents=True)

    shutil.copy(ROOT / "factory/scripts/bash/common.sh", bash_scripts_dir / "common.sh")
    shutil.copy(ROOT / "factory/scripts/bash/manage-program-context.sh", bash_scripts_dir / "manage-program-context.sh")
    shutil.copy(ROOT / "factory/scripts/python/manage_program_context.py", generic_scripts_dir / "manage_program_context.py")

    program_id = "ielts-writing-5-0-to-7-5-in-30-days-20260215-2122"
    program_dir = programs_dir / program_id
    program_dir.mkdir(parents=True)
    (program_dir / "program.json").write_text(
        json.dumps({"program_id": program_id, "title": "Writing", "status": "draft"}), encoding="utf-8"
    )

    # Unit 001: needs refine (open questions remain).
    unit1 = program_dir / "units" / "001-foundation"
    unit1.mkdir(parents=True)
    (unit1 / "brief.md").write_text("# brief", encoding="utf-8")
    (unit1 / "brief.json").write_text(
        json.dumps({"refinement": {"open_questions": 2}}, indent=2), encoding="utf-8"
    )

    # Unit 002: refine done but design missing.
    unit2 = program_dir / "units" / "002-grammar"
    unit2.mkdir(parents=True)
    (unit2 / "brief.md").write_text("# brief", encoding="utf-8")
    (unit2 / "brief.json").write_text(
        json.dumps({"refinement": {"open_questions": 0}}, indent=2), encoding="utf-8"
    )

    # Unit 003: design complete, should recommend sequence.
    unit3 = program_dir / "units" / "003-task"
    unit3.mkdir(parents=True)
    (unit3 / "brief.md").write_text("# brief", encoding="utf-8")
    (unit3 / "brief.json").write_text(
        json.dumps({"refinement": {"open_questions": 0}}, indent=2), encoding="utf-8"
    )
    for rel_path in (
        "design.md",
        "design.json",
        "content-model.md",
        "content-model.json",
        "exercise-design.md",
        "exercise-design.json",
        "assessment-map.md",
        "delivery-guide.md",
        "design-decisions.json",
        "assessment-blueprint.json",
        "template-selection.json",
        "outputs/manifest.json",
    ):
        target = unit3 / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix == ".json":
            target.write_text("{}", encoding="utf-8")
        else:
            target.write_text("# placeholder", encoding="utf-8")

    (context_dir / "current-program").write_text(program_id, encoding="utf-8")
    (context_dir / "current-unit").write_text("002-grammar", encoding="utf-8")

    script = bash_scripts_dir / "manage-program-context.sh"
    cmd = ["bash", str(script), "--json", "workflow-status", "--program", program_id]
    result = subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout.strip())

    assert payload["program_id"] == program_id
    assert payload["summary"]["total_units"] == 3
    assert payload["summary"]["refine_pending"] >= 1
    assert payload["summary"]["design_pending"] >= 1
    assert payload["summary"]["sequence_pending"] >= 1
    assert payload["follow_up_tasks"], "follow_up_tasks should not be empty"
    assert any("/lcs.programs activate" in task["command"] for task in payload["follow_up_tasks"])
    assert any("/lcs.refine" in task["command"] or "/lcs.design" in task["command"] for task in payload["follow_up_tasks"])


@pytest.mark.skipif(os.name == "nt", reason="Bash workflow test")
def test_manage_program_context_resolve_unit_next_intent_activates_next_unit(tmp_path: Path):
    repo = tmp_path / "repo"
    bash_scripts_dir = repo / ".lcs" / "scripts" / "bash"
    generic_scripts_dir = repo / ".lcs" / "scripts"
    context_dir = repo / ".lcs" / "context"
    programs_dir = repo / "programs"

    bash_scripts_dir.mkdir(parents=True)
    generic_scripts_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True)
    programs_dir.mkdir(parents=True)

    shutil.copy(ROOT / "factory/scripts/bash/common.sh", bash_scripts_dir / "common.sh")
    shutil.copy(ROOT / "factory/scripts/bash/manage-program-context.sh", bash_scripts_dir / "manage-program-context.sh")
    shutil.copy(ROOT / "factory/scripts/python/manage_program_context.py", generic_scripts_dir / "manage_program_context.py")

    program_id = "ielts-writing-5-0-to-7-5-in-30-days-20260215-2122"
    program_dir = programs_dir / program_id
    (program_dir / "units" / "001-unit-a").mkdir(parents=True)
    (program_dir / "units" / "002-unit-b").mkdir(parents=True)
    (program_dir / "units" / "003-unit-c").mkdir(parents=True)
    (program_dir / "program.json").write_text(
        json.dumps({"program_id": program_id, "title": "Writing", "status": "draft"}), encoding="utf-8"
    )

    # Unit B already has design artifacts; Unit C should be selected as next design target.
    unit_b = program_dir / "units" / "002-unit-b"
    (unit_b / "brief.md").write_text("# brief", encoding="utf-8")
    (unit_b / "brief.json").write_text(json.dumps({"refinement": {"open_questions": 0}}, indent=2), encoding="utf-8")
    for rel_path in (
        "design.md",
        "design.json",
        "content-model.md",
        "content-model.json",
        "exercise-design.md",
        "exercise-design.json",
        "assessment-map.md",
        "delivery-guide.md",
        "design-decisions.json",
        "assessment-blueprint.json",
        "template-selection.json",
        "outputs/manifest.json",
    ):
        target = unit_b / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}" if target.suffix == ".json" else "# placeholder", encoding="utf-8")

    unit_c = program_dir / "units" / "003-unit-c"
    (unit_c / "brief.md").write_text("# brief", encoding="utf-8")
    (unit_c / "brief.json").write_text(json.dumps({"refinement": {"open_questions": 0}}, indent=2), encoding="utf-8")

    (context_dir / "current-program").write_text(program_id, encoding="utf-8")
    (context_dir / "current-unit").write_text("002-unit-b", encoding="utf-8")

    script = bash_scripts_dir / "manage-program-context.sh"
    cmd = [
        "bash",
        str(script),
        "--json",
        "resolve-unit",
        "--program",
        program_id,
        "--for-stage",
        "design",
        "--intent",
        "Generate design artifacts for next unit",
        "--activate-resolved",
    ]
    result = subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout.strip())

    assert payload["selected_unit"] == "003-unit-c"
    assert payload["activated"] is True
    assert (context_dir / "current-unit").read_text(encoding="utf-8").strip() == "003-unit-c"


@pytest.mark.skipif(os.name == "nt", reason="Bash workflow test")
def test_manage_program_context_resolve_program_falls_back_to_single_existing_program(tmp_path: Path):
    repo = tmp_path / "repo"
    bash_scripts_dir = repo / ".lcs" / "scripts" / "bash"
    generic_scripts_dir = repo / ".lcs" / "scripts"
    context_dir = repo / ".lcs" / "context"
    programs_dir = repo / "programs"

    bash_scripts_dir.mkdir(parents=True)
    generic_scripts_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True)
    programs_dir.mkdir(parents=True)

    shutil.copy(ROOT / "factory/scripts/bash/common.sh", bash_scripts_dir / "common.sh")
    shutil.copy(ROOT / "factory/scripts/bash/manage-program-context.sh", bash_scripts_dir / "manage-program-context.sh")
    shutil.copy(ROOT / "factory/scripts/python/manage_program_context.py", generic_scripts_dir / "manage_program_context.py")

    existing_program = "ielts-speaking-5-0-to-6-5-in-30-days-20260215-2233"
    (programs_dir / existing_program / "units" / "001-speaking").mkdir(parents=True)
    (programs_dir / existing_program / "program.json").write_text(
        json.dumps({"program_id": existing_program, "title": "Speaking", "status": "draft"}), encoding="utf-8"
    )

    # Stale context points to a missing program, but only one valid program exists.
    (context_dir / "current-program").write_text("missing-program-20260215-0000", encoding="utf-8")
    (context_dir / "current-unit").write_text("001-speaking", encoding="utf-8")

    script = bash_scripts_dir / "manage-program-context.sh"
    cmd = [
        "bash",
        str(script),
        "--json",
        "resolve-unit",
        "--for-stage",
        "design",
        "--intent",
        "Generate design artifacts for current unit",
    ]
    result = subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout.strip())

    assert payload["program_id"] == existing_program
    assert payload["selected_unit"] == "001-speaking"


@pytest.mark.skipif(os.name == "nt", reason="Bash workflow test")
def test_manage_program_context_resolve_program_falls_back_to_latest_existing_program(tmp_path: Path):
    repo = tmp_path / "repo"
    bash_scripts_dir = repo / ".lcs" / "scripts" / "bash"
    generic_scripts_dir = repo / ".lcs" / "scripts"
    context_dir = repo / ".lcs" / "context"
    programs_dir = repo / "programs"

    bash_scripts_dir.mkdir(parents=True)
    generic_scripts_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True)
    programs_dir.mkdir(parents=True)

    shutil.copy(ROOT / "factory/scripts/bash/common.sh", bash_scripts_dir / "common.sh")
    shutil.copy(ROOT / "factory/scripts/bash/manage-program-context.sh", bash_scripts_dir / "manage-program-context.sh")
    shutil.copy(ROOT / "factory/scripts/python/manage_program_context.py", generic_scripts_dir / "manage_program_context.py")

    older = "ielts-writing-5-0-to-7-5-in-30-days-20260215-2122"
    latest = "ielts-writing-5-0-to-7-5-in-30-days-20260215-2233"
    (programs_dir / older / "units" / "001-writing").mkdir(parents=True)
    (programs_dir / latest / "units" / "001-writing").mkdir(parents=True)

    (context_dir / "current-program").write_text("missing-program-20260215-0000", encoding="utf-8")
    (context_dir / "current-unit").write_text("001-writing", encoding="utf-8")

    script = bash_scripts_dir / "manage-program-context.sh"
    cmd = [
        "bash",
        str(script),
        "--json",
        "resolve-unit",
        "--for-stage",
        "design",
        "--intent",
        "Generate design artifacts for current unit",
    ]
    result = subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True)
    payload = json.loads(result.stdout.strip())

    assert payload["program_id"] == latest
    assert payload["selected_unit"] == "001-writing"
