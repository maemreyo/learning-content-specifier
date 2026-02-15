#!/usr/bin/env bash
# Common functions and variables for learning-content workflow scripts.

get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        local script_dir
        script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../../.." && pwd)
    fi
}

resolve_python_tool() {
    local tool_name="$1"
    local repo_root
    repo_root="$(get_repo_root)"

    local candidates=(
        "$repo_root/factory/scripts/python/$tool_name"
        "$repo_root/.lcs/scripts/$tool_name"
    )

    for candidate in "${candidates[@]}"; do
        if [[ -f "$candidate" ]]; then
            echo "$candidate"
            return 0
        fi
    done

    echo "ERROR: Could not locate python tool '$tool_name'" >&2
    return 1
}

has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

read_context_value() {
    local file_path="$1"
    if [[ -f "$file_path" ]]; then
        sed -n '1s/[[:space:]]*$//p' "$file_path"
    fi
}

write_context_value() {
    local context_file="$1"
    local value="$2"
    mkdir -p "$(dirname "$context_file")"
    printf '%s\n' "$value" > "$context_file"
}

infer_program_from_pwd() {
    local repo_root="$1"
    local cwd
    cwd="$(pwd -P)"
    case "$cwd" in
        "$repo_root"/programs/*)
            local rest
            rest="${cwd#"$repo_root"/programs/}"
            echo "${rest%%/*}"
            ;;
    esac
}

infer_unit_from_pwd() {
    local repo_root="$1"
    local cwd
    cwd="$(pwd -P)"
    case "$cwd" in
        "$repo_root"/programs/*/units/*)
            local rest program_part
            rest="${cwd#"$repo_root"/programs/}"
            program_part="${rest%%/*}"
            rest="${rest#"$program_part"/units/}"
            echo "${rest%%/*}"
            ;;
    esac
}

get_current_program() {
    local repo_root="$1"
    local context_file="$repo_root/.lcs/context/current-program"

    if [[ -n "${LCS_PROGRAM:-}" ]]; then
        echo "$LCS_PROGRAM"
        return
    fi

    local from_context
    from_context="$(read_context_value "$context_file" || true)"
    if [[ -n "$from_context" ]]; then
        echo "$from_context"
        return
    fi

    infer_program_from_pwd "$repo_root"
}

get_current_unit() {
    local repo_root="$1"
    local context_file="$repo_root/.lcs/context/current-unit"

    if [[ -n "${LCS_UNIT:-}" ]]; then
        echo "$LCS_UNIT"
        return
    fi

    local from_context
    from_context="$(read_context_value "$context_file" || true)"
    if [[ -n "$from_context" ]]; then
        echo "$from_context"
        return
    fi

    infer_unit_from_pwd "$repo_root"
}

infer_single_unit_from_program() {
    local program_dir="$1"
    local units_dir="$program_dir/units"
    local matches=()

    [[ -d "$units_dir" ]] || return 0

    for dir in "$units_dir"/*; do
        [[ -d "$dir" ]] || continue
        local name
        name="$(basename "$dir")"
        if [[ "$name" =~ ^[0-9]{3}- ]]; then
            matches+=("$name")
        fi
    done

    if [[ ${#matches[@]} -eq 1 ]]; then
        echo "${matches[0]}"
    fi
}

check_unit_branch() {
    local unit_id="$1"
    local has_git_repo="$2"
    : "$has_git_repo"

    if [[ -z "$unit_id" ]]; then
        echo "ERROR: No active unit context found." >&2
        echo "Run /lcs.define first or set .lcs/context/current-unit." >&2
        return 1
    fi

    return 0
}

get_unit_paths() {
    local mode="require-unit"
    if [[ "${1:-}" == "--allow-missing-unit" ]]; then
        mode="allow-missing-unit"
    fi

    local repo_root current_unit has_git_repo="false"
    local program_id program_dir unit_dir=""
    local programs_root context_dir

    repo_root="$(get_repo_root)"
    programs_root="$repo_root/programs"
    context_dir="$repo_root/.lcs/context"

    program_id="$(get_current_program "$repo_root" || true)"
    if [[ -n "$program_id" ]]; then
        program_dir="$programs_root/$program_id"
    else
        program_dir=""
    fi

    current_unit="$(get_current_unit "$repo_root" || true)"
    if [[ -z "$current_unit" && -n "$program_dir" ]]; then
        current_unit="$(infer_single_unit_from_program "$program_dir" || true)"
    fi

    if has_git; then
        has_git_repo="true"
    fi

    if [[ "$mode" == "require-unit" ]]; then
        if [[ -z "$program_id" ]]; then
            echo "ERROR: No active program context found." >&2
            echo "Run /lcs.charter first or set .lcs/context/current-program." >&2
            return 1
        fi
        if [[ ! -d "$program_dir" ]]; then
            echo "ERROR: Active program directory not found: $program_dir" >&2
            return 1
        fi
        if [[ -z "$current_unit" ]]; then
            echo "ERROR: No active unit context found for program '$program_id'." >&2
            echo "Run /lcs.define first or set .lcs/context/current-unit." >&2
            return 1
        fi
        unit_dir="$program_dir/units/$current_unit"
    else
        if [[ -n "$program_id" ]]; then
            unit_dir="$program_dir/units/$current_unit"
            if [[ -z "$current_unit" ]]; then
                unit_dir=""
            fi
        fi
    fi

    local program_file="" program_charter_file=""
    local program_roadmap_json_file="" program_roadmap_md_file=""
    local brief_file="" brief_json_file="" design_file="" design_json_file=""
    local sequence_file="" sequence_json_file="" research_file=""
    local content_model_file="" content_model_json_file=""
    local exercise_design_file="" exercise_design_json_file=""
    local assessment_map_file="" delivery_guide_file="" design_decisions_file=""
    local assessment_blueprint_file="" template_selection_file="" trend_topics_file=""
    local audit_report_file="" audit_report_json_file=""
    local rubrics_dir="" outputs_dir="" manifest_file=""

    if [[ -n "$program_dir" ]]; then
        program_file="$program_dir/program.json"
        program_charter_file="$program_dir/charter.md"
        program_roadmap_json_file="$program_dir/roadmap.json"
        program_roadmap_md_file="$program_dir/roadmap.md"
    fi

    if [[ -n "$unit_dir" ]]; then
        brief_file="$unit_dir/brief.md"
        brief_json_file="$unit_dir/brief.json"
        design_file="$unit_dir/design.md"
        design_json_file="$unit_dir/design.json"
        sequence_file="$unit_dir/sequence.md"
        sequence_json_file="$unit_dir/sequence.json"
        research_file="$unit_dir/research.md"
        content_model_file="$unit_dir/content-model.md"
        content_model_json_file="$unit_dir/content-model.json"
        exercise_design_file="$unit_dir/exercise-design.md"
        exercise_design_json_file="$unit_dir/exercise-design.json"
        assessment_map_file="$unit_dir/assessment-map.md"
        delivery_guide_file="$unit_dir/delivery-guide.md"
        design_decisions_file="$unit_dir/design-decisions.json"
        assessment_blueprint_file="$unit_dir/assessment-blueprint.json"
        template_selection_file="$unit_dir/template-selection.json"
        trend_topics_file="$unit_dir/trend-topics.json"
        audit_report_file="$unit_dir/audit-report.md"
        audit_report_json_file="$unit_dir/audit-report.json"
        rubrics_dir="$unit_dir/rubrics"
        outputs_dir="$unit_dir/outputs"
        manifest_file="$unit_dir/outputs/manifest.json"
    fi

    cat <<PATHS
REPO_ROOT='$repo_root'
PROGRAMS_ROOT='$programs_root'
CONTEXT_DIR='$context_dir'
CONTEXT_PROGRAM_FILE='$context_dir/current-program'
CONTEXT_UNIT_FILE='$context_dir/current-unit'
PROGRAM_ID='$program_id'
PROGRAM_DIR='$program_dir'
PROGRAM_FILE='$program_file'
PROGRAM_CHARTER_FILE='$program_charter_file'
PROGRAM_ROADMAP_JSON_FILE='$program_roadmap_json_file'
PROGRAM_ROADMAP_MD_FILE='$program_roadmap_md_file'
CURRENT_BRANCH='$current_unit'
CURRENT_UNIT='$current_unit'
HAS_GIT='$has_git_repo'
UNIT_DIR='$unit_dir'
BRIEF_FILE='$brief_file'
BRIEF_JSON_FILE='$brief_json_file'
DESIGN_FILE='$design_file'
DESIGN_JSON_FILE='$design_json_file'
SEQUENCE_FILE='$sequence_file'
SEQUENCE_JSON_FILE='$sequence_json_file'
RESEARCH_FILE='$research_file'
CONTENT_MODEL_FILE='$content_model_file'
CONTENT_MODEL_JSON_FILE='$content_model_json_file'
EXERCISE_DESIGN_FILE='$exercise_design_file'
EXERCISE_DESIGN_JSON_FILE='$exercise_design_json_file'
ASSESSMENT_MAP_FILE='$assessment_map_file'
DELIVERY_GUIDE_FILE='$delivery_guide_file'
DESIGN_DECISIONS_FILE='$design_decisions_file'
ASSESSMENT_BLUEPRINT_FILE='$assessment_blueprint_file'
TEMPLATE_SELECTION_FILE='$template_selection_file'
TREND_TOPICS_FILE='$trend_topics_file'
AUDIT_REPORT_FILE='$audit_report_file'
AUDIT_REPORT_JSON_FILE='$audit_report_json_file'
RUBRICS_DIR='$rubrics_dir'
OUTPUTS_DIR='$outputs_dir'
MANIFEST_FILE='$manifest_file'
CHARTER_FILE='$repo_root/.lcs/memory/charter.md'
SUBJECT_CHARTER_FILE='$repo_root/.lcs/memory/charter.md'
PATHS
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }

get_contract_version() {
    local repo_root index_file py
    repo_root="$(get_repo_root)"
    index_file="$repo_root/contracts/index.json"
    if [[ ! -f "$index_file" ]]; then
        index_file="$repo_root/.lcs/contracts/index.json"
    fi

    if [[ ! -f "$index_file" ]]; then
        echo "ERROR: Missing contract index. Checked: $repo_root/contracts/index.json and $repo_root/.lcs/contracts/index.json" >&2
        return 1
    fi

    py="python3"
    if ! command -v "$py" >/dev/null 2>&1; then
        py="python"
    fi
    if ! command -v "$py" >/dev/null 2>&1; then
        echo "ERROR: python3/python is required to read contract_version" >&2
        return 1
    fi

    "$py" - "$index_file" <<'PY'
import json
import re
import sys
from pathlib import Path

index_file = Path(sys.argv[1])
payload = json.loads(index_file.read_text(encoding="utf-8"))
version = str(payload.get("contract_version", "")).strip()
if not version:
    raise SystemExit(f"contracts/index.json missing contract_version: {index_file}")
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit(f"Invalid contract_version '{version}' in {index_file} (expected X.Y.Z)")
print(version)
PY
}
