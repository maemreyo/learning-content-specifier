#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
REQUIRE_SEQUENCE=false
INCLUDE_SEQUENCE=false
PATHS_ONLY=false
SKIP_BRANCH_CHECK=false

for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --require-sequence) REQUIRE_SEQUENCE=true ;;
        --include-sequence) INCLUDE_SEQUENCE=true ;;
        --paths-only) PATHS_ONLY=true ;;
        --skip-branch-check) SKIP_BRANCH_CHECK=true ;;
        --help|-h)
            cat <<HELP
Usage: check-workflow-prereqs.sh [OPTIONS]

OPTIONS:
  --json
  --require-sequence
  --include-sequence
  --paths-only
  --skip-branch-check
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

if $PATHS_ONLY && [[ "$SKIP_BRANCH_CHECK" == "true" ]]; then
    eval "$(get_unit_paths --allow-missing-unit)"
else
    eval "$(get_unit_paths)"
fi
if [[ "$SKIP_BRANCH_CHECK" != "true" ]]; then
    check_unit_branch "$CURRENT_UNIT" "$HAS_GIT" || exit 1
fi

if $PATHS_ONLY; then
    if $JSON_MODE; then
        printf '{"UNIT_REPO_ROOT":"%s","UNIT_BRANCH":"%s","UNIT_ID":"%s","UNIT_HAS_GIT":%s,"PROGRAM_ID":"%s","PROGRAM_DIR":"%s","PROGRAM_CHARTER_FILE":"%s","UNIT_DIR":"%s","UNIT_BRIEF_FILE":"%s","UNIT_BRIEF_JSON_FILE":"%s","UNIT_DESIGN_FILE":"%s","UNIT_DESIGN_JSON_FILE":"%s","UNIT_SEQUENCE_FILE":"%s","UNIT_SEQUENCE_JSON_FILE":"%s","UNIT_AUDIT_REPORT_FILE":"%s","UNIT_AUDIT_REPORT_JSON_FILE":"%s","UNIT_MANIFEST_FILE":"%s","UNIT_CHARTER_FILE":"%s","SUBJECT_CHARTER_FILE":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$CURRENT_UNIT" "$HAS_GIT" "$PROGRAM_ID" "$PROGRAM_DIR" "$PROGRAM_CHARTER_FILE" "$UNIT_DIR" "$BRIEF_FILE" "$BRIEF_JSON_FILE" "$DESIGN_FILE" "$DESIGN_JSON_FILE" "$SEQUENCE_FILE" "$SEQUENCE_JSON_FILE" "$AUDIT_REPORT_FILE" "$AUDIT_REPORT_JSON_FILE" "$MANIFEST_FILE" "$PROGRAM_CHARTER_FILE" "$SUBJECT_CHARTER_FILE"
    else
        echo "UNIT_REPO_ROOT: $REPO_ROOT"
        echo "UNIT_BRANCH: $CURRENT_BRANCH"
        echo "UNIT_ID: $CURRENT_UNIT"
        echo "UNIT_HAS_GIT: $HAS_GIT"
        echo "PROGRAM_ID: $PROGRAM_ID"
        echo "PROGRAM_DIR: $PROGRAM_DIR"
        echo "PROGRAM_CHARTER_FILE: $PROGRAM_CHARTER_FILE"
        echo "UNIT_DIR: $UNIT_DIR"
        echo "UNIT_BRIEF_FILE: $BRIEF_FILE"
        echo "UNIT_BRIEF_JSON_FILE: $BRIEF_JSON_FILE"
        echo "UNIT_DESIGN_FILE: $DESIGN_FILE"
        echo "UNIT_DESIGN_JSON_FILE: $DESIGN_JSON_FILE"
        echo "UNIT_SEQUENCE_FILE: $SEQUENCE_FILE"
        echo "UNIT_SEQUENCE_JSON_FILE: $SEQUENCE_JSON_FILE"
        echo "UNIT_AUDIT_REPORT_FILE: $AUDIT_REPORT_FILE"
        echo "UNIT_AUDIT_REPORT_JSON_FILE: $AUDIT_REPORT_JSON_FILE"
        echo "UNIT_MANIFEST_FILE: $MANIFEST_FILE"
        echo "UNIT_CHARTER_FILE: $PROGRAM_CHARTER_FILE"
        echo "SUBJECT_CHARTER_FILE: $SUBJECT_CHARTER_FILE"
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
