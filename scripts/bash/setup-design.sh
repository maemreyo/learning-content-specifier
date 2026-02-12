#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            exit 0
            ;;
    esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_unit_paths)"
check_unit_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

mkdir -p "$UNIT_DIR" "$RUBRICS_DIR" "$OUTPUTS_DIR"

TEMPLATE="$REPO_ROOT/.lcs/templates/design-template.md"
if [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$DESIGN_FILE"
else
    touch "$DESIGN_FILE"
fi

[[ -f "$CONTENT_MODEL_FILE" ]] || touch "$CONTENT_MODEL_FILE"
[[ -f "$ASSESSMENT_MAP_FILE" ]] || touch "$ASSESSMENT_MAP_FILE"
[[ -f "$DELIVERY_GUIDE_FILE" ]] || touch "$DELIVERY_GUIDE_FILE"

if $JSON_MODE; then
    printf '{"BRIEF_FILE":"%s","DESIGN_FILE":"%s","UNIT_DIR":"%s","BRANCH":"%s","HAS_GIT":"%s"}\n' \
        "$BRIEF_FILE" "$DESIGN_FILE" "$UNIT_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
else
    echo "BRIEF_FILE: $BRIEF_FILE"
    echo "DESIGN_FILE: $DESIGN_FILE"
    echo "UNIT_DIR: $UNIT_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi
