#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
SHORT_NAME=""
UNIT_NUMBER=""
ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --short-name)
            SHORT_NAME="${2:-}"
            shift 2
            ;;
        --number)
            UNIT_NUMBER="${2:-}"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--short-name <name>] [--number N] <unit_description>"
            exit 0
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

UNIT_DESCRIPTION="${ARGS[*]:-}"
[[ -z "$UNIT_DESCRIPTION" ]] && { echo "Usage: $0 [--json] [--short-name <name>] [--number N] <unit_description>" >&2; exit 1; }

clean_name() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g; s/-\+/-/g; s/^-//; s/-$//'
}

generate_name() {
    local desc="$1"
    local stop='^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$'
    local cleaned words=() out=()
    cleaned="$(echo "$desc" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/ /g')"
    for w in $cleaned; do
        [[ -z "$w" ]] && continue
        if ! echo "$w" | grep -qiE "$stop" && [[ ${#w} -ge 3 ]]; then
            words+=("$w")
        fi
    done
    if [[ ${#words[@]} -eq 0 ]]; then
        clean_name "$desc" | cut -d'-' -f1-3
        return
    fi
    out=("${words[@]:0:3}")
    local IFS='-'
    echo "${out[*]}"
}

find_repo_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        if [[ -d "$dir/.git" || -d "$dir/.lcs" ]]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

get_highest_from_specs() {
    local specs_dir="$1" highest=0
    [[ -d "$specs_dir" ]] || { echo 0; return; }
    for dir in "$specs_dir"/*; do
        [[ -d "$dir" ]] || continue
        local base num
        base="$(basename "$dir")"
        num="$(echo "$base" | grep -o '^[0-9]\+' || echo 0)"
        num=$((10#$num))
        [[ "$num" -gt "$highest" ]] && highest="$num"
    done
    echo "$highest"
}

get_highest_from_branches() {
    local highest=0
    local branches
    branches="$(git branch -a 2>/dev/null || true)"
    [[ -z "$branches" ]] && { echo 0; return; }
    while IFS= read -r branch; do
        local clean num
        clean="$(echo "$branch" | sed 's/^[* ]*//; s|^remotes/[^/]*/||')"
        if echo "$clean" | grep -q '^[0-9]\{3\}-'; then
            num="$(echo "$clean" | grep -o '^[0-9]\{3\}' || echo 0)"
            num=$((10#$num))
            [[ "$num" -gt "$highest" ]] && highest="$num"
        fi
    done <<< "$branches"
    echo "$highest"
}

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT="$(git rev-parse --show-toplevel)"
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    HAS_GIT=false
fi

cd "$REPO_ROOT"
SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

UNIT_SUFFIX="$(clean_name "${SHORT_NAME:-$(generate_name "$UNIT_DESCRIPTION")}")"

if [[ -z "$UNIT_NUMBER" ]]; then
    if [[ "$HAS_GIT" == true ]]; then
        git fetch --all --prune 2>/dev/null || true
        b="$(get_highest_from_branches)"
        s="$(get_highest_from_specs "$SPECS_DIR")"
        (( s > b )) && UNIT_NUMBER="$((s + 1))" || UNIT_NUMBER="$((b + 1))"
    else
        s="$(get_highest_from_specs "$SPECS_DIR")"
        UNIT_NUMBER="$((s + 1))"
    fi
fi

UNIT_NUM="$(printf "%03d" "$((10#$UNIT_NUMBER))")"
UNIT_NAME="${UNIT_NUM}-${UNIT_SUFFIX}"

if [[ "$HAS_GIT" == true ]]; then
    git checkout -b "$UNIT_NAME" >/dev/null
else
    >&2 echo "[lcs] Warning: Git repository not detected; skipped branch creation for $UNIT_NAME"
fi

UNIT_DIR="$SPECS_DIR/$UNIT_NAME"
mkdir -p "$UNIT_DIR"

TEMPLATE="$REPO_ROOT/.lcs/templates/brief-template.md"
BRIEF_FILE="$UNIT_DIR/brief.md"
if [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$BRIEF_FILE"
else
    touch "$BRIEF_FILE"
fi

export LCS_UNIT="$UNIT_NAME"
export LCS_FEATURE="$UNIT_NAME"

if $JSON_MODE; then
    printf '{"UNIT_NAME":"%s","BRIEF_FILE":"%s","UNIT_NUM":"%s"}\n' "$UNIT_NAME" "$BRIEF_FILE" "$UNIT_NUM"
else
    echo "UNIT_NAME: $UNIT_NAME"
    echo "BRIEF_FILE: $BRIEF_FILE"
    echo "UNIT_NUM: $UNIT_NUM"
fi
