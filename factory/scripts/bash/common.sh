#!/usr/bin/env bash
# Common functions and variables for learning-content workflow scripts

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

get_current_branch() {
    if [[ -n "${LCS_UNIT:-}" ]]; then
        echo "$LCS_UNIT"
        return
    fi

    local repo_root specs_dir latest_unit=""
    repo_root="$(get_repo_root)"
    specs_dir="$repo_root/specs"

    get_latest_unit_from_specs() {
        local candidate=""
        local max_num=0
        if [[ -d "$specs_dir" ]]; then
            for dir in "$specs_dir"/*; do
                [[ -d "$dir" ]] || continue
                local name number
                name="$(basename "$dir")"
                if [[ "$name" =~ ^([0-9]{3})- ]]; then
                    number=$((10#${BASH_REMATCH[1]}))
                    if [[ "$number" -gt "$max_num" ]]; then
                        max_num="$number"
                        candidate="$name"
                    fi
                fi
            done
        fi
        [[ -n "$candidate" ]] && echo "$candidate"
    }

    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        local branch
        branch="$(git rev-parse --abbrev-ref HEAD)"
        if [[ "$branch" =~ ^[0-9]{3}- ]]; then
            echo "$branch"
            return
        fi
        latest_unit="$(get_latest_unit_from_specs || true)"
        if [[ -n "$latest_unit" ]]; then
            echo "$latest_unit"
            return
        fi
        echo "$branch"
        return
    fi

    latest_unit="$(get_latest_unit_from_specs || true)"
    [[ -n "$latest_unit" ]] && echo "$latest_unit" || echo "main"
}

has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

check_unit_branch() {
    local branch="$1" has_git_repo="$2"

    if [[ "$has_git_repo" != "true" ]]; then
        echo "[lcs] Warning: Git repository not detected; skipped branch validation" >&2
        return 0
    fi

    if [[ ! "$branch" =~ ^[0-9]{3}- ]]; then
        echo "ERROR: Not on a unit branch. Current branch: $branch" >&2
        echo "Unit branches should be named like: 001-unit-name" >&2
        return 1
    fi

    return 0
}

find_unit_dir_by_prefix() {
    local repo_root="$1" branch_name="$2" specs_dir prefix matches=()
    specs_dir="$repo_root/specs"

    if [[ ! "$branch_name" =~ ^([0-9]{3})- ]]; then
        echo "$specs_dir/$branch_name"
        return 0
    fi

    prefix="${BASH_REMATCH[1]}"

    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/"$prefix"-*; do
            [[ -d "$dir" ]] || continue
            matches+=("$(basename "$dir")")
        done
    fi

    if [[ ${#matches[@]} -eq 0 ]]; then
        echo "$specs_dir/$branch_name"
    elif [[ ${#matches[@]} -eq 1 ]]; then
        echo "$specs_dir/${matches[0]}"
    else
        echo "ERROR: Multiple unit directories found with prefix '$prefix': ${matches[*]}" >&2
        return 1
    fi
}

get_unit_paths() {
    local repo_root current_branch has_git_repo="false" unit_dir
    repo_root="$(get_repo_root)"
    current_branch="$(get_current_branch)"

    if has_git; then
        has_git_repo="true"
    fi

    if ! unit_dir="$(find_unit_dir_by_prefix "$repo_root" "$current_branch")"; then
        return 1
    fi

    cat <<PATHS
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
UNIT_DIR='$unit_dir'
BRIEF_FILE='$unit_dir/brief.md'
BRIEF_JSON_FILE='$unit_dir/brief.json'
DESIGN_FILE='$unit_dir/design.md'
DESIGN_JSON_FILE='$unit_dir/design.json'
SEQUENCE_FILE='$unit_dir/sequence.md'
SEQUENCE_JSON_FILE='$unit_dir/sequence.json'
RESEARCH_FILE='$unit_dir/research.md'
CONTENT_MODEL_FILE='$unit_dir/content-model.md'
CONTENT_MODEL_JSON_FILE='$unit_dir/content-model.json'
ASSESSMENT_MAP_FILE='$unit_dir/assessment-map.md'
DELIVERY_GUIDE_FILE='$unit_dir/delivery-guide.md'
DESIGN_DECISIONS_FILE='$unit_dir/design-decisions.json'
AUDIT_REPORT_FILE='$unit_dir/audit-report.md'
AUDIT_REPORT_JSON_FILE='$unit_dir/audit-report.json'
RUBRICS_DIR='$unit_dir/rubrics'
OUTPUTS_DIR='$unit_dir/outputs'
MANIFEST_FILE='$unit_dir/outputs/manifest.json'
CHARTER_FILE='$repo_root/.lcs/memory/charter.md'
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
