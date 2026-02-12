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

get_current_branch() {
    if [[ -n "${LCS_UNIT:-}" ]]; then
        echo "$LCS_UNIT"
        return
    fi

    if [[ -n "${LCS_FEATURE:-}" ]]; then
        echo "$LCS_FEATURE"
        return
    fi

    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
        return
    fi

    local repo_root specs_dir latest_unit="" highest=0
    repo_root="$(get_repo_root)"
    specs_dir="$repo_root/specs"

    if [[ -d "$specs_dir" ]]; then
        for dir in "$specs_dir"/*; do
            [[ -d "$dir" ]] || continue
            local name number
            name="$(basename "$dir")"
            if [[ "$name" =~ ^([0-9]{3})- ]]; then
                number=$((10#${BASH_REMATCH[1]}))
                if [[ "$number" -gt "$highest" ]]; then
                    highest="$number"
                    latest_unit="$name"
                fi
            fi
        done
    fi

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
        return
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
        echo "$specs_dir/$branch_name"
    fi
}

get_unit_paths() {
    local repo_root current_branch has_git_repo="false" unit_dir
    repo_root="$(get_repo_root)"
    current_branch="$(get_current_branch)"

    if has_git; then
        has_git_repo="true"
    fi

    unit_dir="$(find_unit_dir_by_prefix "$repo_root" "$current_branch")"

    cat <<PATHS
REPO_ROOT='$repo_root'
CURRENT_BRANCH='$current_branch'
HAS_GIT='$has_git_repo'
UNIT_DIR='$unit_dir'
BRIEF_FILE='$unit_dir/brief.md'
DESIGN_FILE='$unit_dir/design.md'
SEQUENCE_FILE='$unit_dir/sequence.md'
RESEARCH_FILE='$unit_dir/research.md'
CONTENT_MODEL_FILE='$unit_dir/content-model.md'
ASSESSMENT_MAP_FILE='$unit_dir/assessment-map.md'
DELIVERY_GUIDE_FILE='$unit_dir/delivery-guide.md'
RUBRICS_DIR='$unit_dir/rubrics'
OUTPUTS_DIR='$unit_dir/outputs'
CHARTER_FILE='$repo_root/.lcs/memory/charter.md'
PATHS
}

check_file() { [[ -f "$1" ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
check_dir() { [[ -d "$1" && -n $(ls -A "$1" 2>/dev/null) ]] && echo "  ✓ $2" || echo "  ✗ $2"; }
