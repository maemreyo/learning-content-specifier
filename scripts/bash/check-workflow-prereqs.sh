#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
REQUIRE_SEQUENCE=false
INCLUDE_SEQUENCE=false
PATHS_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --require-sequence) REQUIRE_SEQUENCE=true ;;
        --include-sequence) INCLUDE_SEQUENCE=true ;;
        --paths-only) PATHS_ONLY=true ;;
        --help|-h)
            cat <<HELP
Usage: check-workflow-prereqs.sh [OPTIONS]

OPTIONS:
  --json
  --require-sequence
  --include-sequence
  --paths-only
HELP
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'" >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_unit_paths)"
check_unit_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

if $PATHS_ONLY; then
    if $JSON_MODE; then
        printf '{"REPO_ROOT":"%s","BRANCH":"%s","UNIT_DIR":"%s","BRIEF_FILE":"%s","DESIGN_FILE":"%s","SEQUENCE_FILE":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$UNIT_DIR" "$BRIEF_FILE" "$DESIGN_FILE" "$SEQUENCE_FILE"
    else
        echo "REPO_ROOT: $REPO_ROOT"
        echo "BRANCH: $CURRENT_BRANCH"
        echo "UNIT_DIR: $UNIT_DIR"
        echo "BRIEF_FILE: $BRIEF_FILE"
        echo "DESIGN_FILE: $DESIGN_FILE"
        echo "SEQUENCE_FILE: $SEQUENCE_FILE"
    fi
    exit 0
fi

[[ -d "$UNIT_DIR" ]] || { echo "ERROR: Unit directory not found: $UNIT_DIR" >&2; exit 1; }
[[ -f "$DESIGN_FILE" ]] || { echo "ERROR: design.md not found in $UNIT_DIR" >&2; echo "Run /lcs.design first." >&2; exit 1; }

if $REQUIRE_SEQUENCE && [[ ! -f "$SEQUENCE_FILE" ]]; then
    echo "ERROR: sequence.md not found in $UNIT_DIR" >&2
    echo "Run /lcs.sequence first." >&2
    exit 1
fi

docs=()
[[ -f "$RESEARCH_FILE" ]] && docs+=("research.md")
[[ -f "$CONTENT_MODEL_FILE" ]] && docs+=("content-model.md")
[[ -f "$ASSESSMENT_MAP_FILE" ]] && docs+=("assessment-map.md")
[[ -f "$DELIVERY_GUIDE_FILE" ]] && docs+=("delivery-guide.md")
if $INCLUDE_SEQUENCE && [[ -f "$SEQUENCE_FILE" ]]; then docs+=("sequence.md"); fi

if $JSON_MODE; then
    if [[ ${#docs[@]} -eq 0 ]]; then
        json_docs="[]"
    else
        json_docs=$(printf '"%s",' "${docs[@]}")
        json_docs="[${json_docs%,}]"
    fi
    printf '{"UNIT_DIR":"%s","AVAILABLE_DOCS":%s}\n' "$UNIT_DIR" "$json_docs"
else
    echo "UNIT_DIR:$UNIT_DIR"
    echo "AVAILABLE_DOCS:"
    check_file "$RESEARCH_FILE" "research.md"
    check_file "$CONTENT_MODEL_FILE" "content-model.md"
    check_file "$ASSESSMENT_MAP_FILE" "assessment-map.md"
    check_file "$DELIVERY_GUIDE_FILE" "delivery-guide.md"
    if $INCLUDE_SEQUENCE; then
        check_file "$SEQUENCE_FILE" "sequence.md"
    fi
fi
