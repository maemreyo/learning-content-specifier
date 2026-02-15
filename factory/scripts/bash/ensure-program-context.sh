#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
PROGRAM_OVERRIDE=""
ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --program)
            PROGRAM_OVERRIDE="${2:-}"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--program <program_id>] <program_intent>"
            exit 0
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

PROGRAM_INTENT="${ARGS[*]:-}"

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
CONTEXT_DIR="$REPO_ROOT/.lcs/context"
PROGRAMS_ROOT="$REPO_ROOT/programs"
TEMPLATE_FILE="$REPO_ROOT/.lcs/templates/charter-template.md"
SUBJECT_CHARTER_FILE="$REPO_ROOT/.lcs/memory/charter.md"

slugify() {
    echo "$1" \
        | tr '[:upper:]' '[:lower:]' \
        | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g' \
        | cut -c1-40
}

generate_program_id() {
    local intent="$1"
    local slug base candidate counter
    slug="$(slugify "$intent")"
    [[ -z "$slug" ]] && slug="program"

    base="${slug}-$(date +%Y%m%d-%H%M)"
    candidate="$base"
    counter=2

    while [[ -e "$PROGRAMS_ROOT/$candidate" ]]; do
        candidate="$(printf '%s-%02d' "$base" "$counter")"
        counter=$((counter + 1))
    done

    echo "$candidate"
}

choose_program_id() {
    local current_program
    current_program="$(read_context_value "$CONTEXT_DIR/current-program" || true)"

    if [[ -n "$PROGRAM_OVERRIDE" ]]; then
        slugify "$PROGRAM_OVERRIDE"
        return
    fi

    if [[ -n "${LCS_PROGRAM:-}" ]]; then
        slugify "$LCS_PROGRAM"
        return
    fi

    if [[ -n "$current_program" && -d "$PROGRAMS_ROOT/$current_program" ]]; then
        echo "$current_program"
        return
    fi

    generate_program_id "$PROGRAM_INTENT"
}

PROGRAM_ID="$(choose_program_id)"
[[ -z "$PROGRAM_ID" ]] && { echo "ERROR: Could not determine program id" >&2; exit 1; }

PROGRAM_DIR="$PROGRAMS_ROOT/$PROGRAM_ID"
PROGRAM_FILE="$PROGRAM_DIR/program.json"
PROGRAM_CHARTER_FILE="$PROGRAM_DIR/charter.md"

mkdir -p "$PROGRAM_DIR/units"
mkdir -p "$CONTEXT_DIR"

if [[ ! -f "$PROGRAM_FILE" ]]; then
    NOW_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    TITLE="$PROGRAM_INTENT"
    [[ -z "$TITLE" ]] && TITLE="$PROGRAM_ID"
    cat > "$PROGRAM_FILE" <<JSON
{
  "program_id": "$PROGRAM_ID",
  "title": "$TITLE",
  "status": "draft",
  "created_at": "$NOW_UTC",
  "updated_at": "$NOW_UTC"
}
JSON
fi

if [[ ! -f "$PROGRAM_CHARTER_FILE" ]]; then
    if [[ -f "$TEMPLATE_FILE" ]]; then
        cp "$TEMPLATE_FILE" "$PROGRAM_CHARTER_FILE"
    else
        touch "$PROGRAM_CHARTER_FILE"
    fi
fi

write_context_value "$CONTEXT_DIR/current-program" "$PROGRAM_ID"
rm -f "$CONTEXT_DIR/current-unit"

export LCS_PROGRAM="$PROGRAM_ID"

if $JSON_MODE; then
    printf '{"PROGRAM_ID":"%s","PROGRAM_DIR":"%s","PROGRAM_FILE":"%s","PROGRAM_CHARTER_FILE":"%s","SUBJECT_CHARTER_FILE":"%s"}\n' \
        "$PROGRAM_ID" "$PROGRAM_DIR" "$PROGRAM_FILE" "$PROGRAM_CHARTER_FILE" "$SUBJECT_CHARTER_FILE"
else
    echo "PROGRAM_ID: $PROGRAM_ID"
    echo "PROGRAM_DIR: $PROGRAM_DIR"
    echo "PROGRAM_FILE: $PROGRAM_FILE"
    echo "PROGRAM_CHARTER_FILE: $PROGRAM_CHARTER_FILE"
    echo "SUBJECT_CHARTER_FILE: $SUBJECT_CHARTER_FILE"
fi
