#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
REQUIRE_SEQUENCE=false
INCLUDE_SEQUENCE=false
PATHS_ONLY=false
SKIP_BRANCH_CHECK=false
REQUIRE_DESIGN_CONTRACTS=false
STAGE_OVERRIDE=""
INTENT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_MODE=true ;;
        --require-sequence) REQUIRE_SEQUENCE=true ;;
        --include-sequence) INCLUDE_SEQUENCE=true ;;
        --paths-only) PATHS_ONLY=true ;;
        --skip-branch-check) SKIP_BRANCH_CHECK=true ;;
        --require-design-contracts) REQUIRE_DESIGN_CONTRACTS=true ;;
        --stage)
            STAGE_OVERRIDE="${2:-}"
            shift
            ;;
        --intent)
            INTENT="${2:-}"
            shift
            ;;
        --help|-h)
            cat <<HELP
Usage: check-workflow-prereqs.sh [OPTIONS]

OPTIONS:
  --json
  --require-sequence
  --include-sequence
  --paths-only
  --skip-branch-check
  --require-design-contracts
  --stage <stage>
  --intent <text>
HELP
            exit 0
            ;;
        *)
            if [[ -z "$INTENT" ]]; then
                INTENT="$1"
            else
                INTENT="$INTENT $1"
            fi
            ;;
    esac
    shift
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
PYTHON_PARSE_BIN="python3"
if ! command -v "$PYTHON_PARSE_BIN" >/dev/null 2>&1; then
    PYTHON_PARSE_BIN="python"
fi

if $PATHS_ONLY && [[ "$SKIP_BRANCH_CHECK" == "true" ]]; then
    eval "$(get_unit_paths --allow-missing-unit)"
else
    eval "$(get_unit_paths)"
fi
if [[ "$SKIP_BRANCH_CHECK" != "true" ]]; then
    check_unit_branch "$CURRENT_UNIT" "$HAS_GIT" || exit 1
fi

stage="$STAGE_OVERRIDE"
if [[ -z "$stage" ]]; then
    if [[ "$REQUIRE_DESIGN_CONTRACTS" == "true" && "$REQUIRE_SEQUENCE" == "true" ]]; then
        stage="author"
    elif [[ "$REQUIRE_DESIGN_CONTRACTS" == "true" ]]; then
        stage="sequence"
    elif [[ "$REQUIRE_SEQUENCE" == "true" ]]; then
        stage="issueize"
    else
        stage="refine"
    fi
fi

run_stage_preflight() {
    local requested_stage="$1"
    local loader_args=("$SCRIPT_DIR/load-stage-context.sh" --json --stage "$requested_stage")
    if [[ -n "$INTENT" ]]; then
        loader_args+=(--intent "$INTENT")
    fi

    local loader_output
    loader_output="$(${loader_args[@]} 2>/dev/null || true)"
    if [[ -z "$loader_output" ]]; then
        echo "ERROR: load-stage-context failed to execute" >&2
        return 1
    fi

    local loader_status
    loader_status="$("$PYTHON_PARSE_BIN" - "$loader_output" <<'PY'
import json
import sys
try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("BLOCK")
    raise SystemExit(0)
print(str(payload.get("STATUS", "BLOCK")).upper())
PY
)"

    if [[ "$loader_status" != "PASS" ]]; then
        local blocker_summary
        blocker_summary="$("$PYTHON_PARSE_BIN" - "$loader_output" <<'PY'
import json
import sys
try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("Invalid load-stage-context output")
    raise SystemExit(0)
blockers = payload.get("BLOCKERS", [])
missing = payload.get("MISSING_INPUTS", [])
parts = []
if missing:
    parts.append("missing=" + ",".join(str(item) for item in missing))
if blockers:
    parts.append("blockers=" + "; ".join(str(item) for item in blockers))
print(" | ".join(parts) if parts else "Unknown preflight blockers")
PY
)"
        echo "ERROR: stage preflight BLOCK ($blocker_summary)" >&2
        return 1
    fi
}

if $PATHS_ONLY; then
    # Maintain legacy paths-only behavior unless caller explicitly requests stage preflight.
    if [[ -n "$STAGE_OVERRIDE" ]]; then
        run_stage_preflight "$stage" || exit 1
    fi

    if $JSON_MODE; then
        printf '{"UNIT_REPO_ROOT":"%s","UNIT_BRANCH":"%s","UNIT_ID":"%s","UNIT_HAS_GIT":%s,"PROGRAM_ID":"%s","PROGRAM_DIR":"%s","PROGRAM_CHARTER_FILE":"%s","PROGRAM_ROADMAP_JSON_FILE":"%s","PROGRAM_ROADMAP_MD_FILE":"%s","UNIT_DIR":"%s","UNIT_BRIEF_FILE":"%s","UNIT_BRIEF_JSON_FILE":"%s","UNIT_DESIGN_FILE":"%s","UNIT_DESIGN_JSON_FILE":"%s","UNIT_EXERCISE_DESIGN_FILE":"%s","UNIT_EXERCISE_DESIGN_JSON_FILE":"%s","UNIT_SEQUENCE_FILE":"%s","UNIT_SEQUENCE_JSON_FILE":"%s","UNIT_AUDIT_REPORT_FILE":"%s","UNIT_AUDIT_REPORT_JSON_FILE":"%s","UNIT_RUBRIC_GATES_FILE":"%s","UNIT_MANIFEST_FILE":"%s","UNIT_CHARTER_FILE":"%s","SUBJECT_CHARTER_FILE":"%s"}\n' \
            "$REPO_ROOT" "$CURRENT_BRANCH" "$CURRENT_UNIT" "$HAS_GIT" "$PROGRAM_ID" "$PROGRAM_DIR" "$PROGRAM_CHARTER_FILE" "$PROGRAM_ROADMAP_JSON_FILE" "$PROGRAM_ROADMAP_MD_FILE" "$UNIT_DIR" "$BRIEF_FILE" "$BRIEF_JSON_FILE" "$DESIGN_FILE" "$DESIGN_JSON_FILE" "$EXERCISE_DESIGN_FILE" "$EXERCISE_DESIGN_JSON_FILE" "$SEQUENCE_FILE" "$SEQUENCE_JSON_FILE" "$AUDIT_REPORT_FILE" "$AUDIT_REPORT_JSON_FILE" "$RUBRIC_GATES_FILE" "$MANIFEST_FILE" "$PROGRAM_CHARTER_FILE" "$SUBJECT_CHARTER_FILE"
    else
        echo "UNIT_REPO_ROOT: $REPO_ROOT"
        echo "UNIT_BRANCH: $CURRENT_BRANCH"
        echo "UNIT_ID: $CURRENT_UNIT"
        echo "UNIT_HAS_GIT: $HAS_GIT"
        echo "PROGRAM_ID: $PROGRAM_ID"
        echo "PROGRAM_DIR: $PROGRAM_DIR"
        echo "PROGRAM_CHARTER_FILE: $PROGRAM_CHARTER_FILE"
        echo "PROGRAM_ROADMAP_JSON_FILE: $PROGRAM_ROADMAP_JSON_FILE"
        echo "PROGRAM_ROADMAP_MD_FILE: $PROGRAM_ROADMAP_MD_FILE"
        echo "UNIT_DIR: $UNIT_DIR"
        echo "UNIT_BRIEF_FILE: $BRIEF_FILE"
        echo "UNIT_BRIEF_JSON_FILE: $BRIEF_JSON_FILE"
        echo "UNIT_DESIGN_FILE: $DESIGN_FILE"
        echo "UNIT_DESIGN_JSON_FILE: $DESIGN_JSON_FILE"
        echo "UNIT_EXERCISE_DESIGN_FILE: $EXERCISE_DESIGN_FILE"
        echo "UNIT_EXERCISE_DESIGN_JSON_FILE: $EXERCISE_DESIGN_JSON_FILE"
        echo "UNIT_SEQUENCE_FILE: $SEQUENCE_FILE"
        echo "UNIT_SEQUENCE_JSON_FILE: $SEQUENCE_JSON_FILE"
        echo "UNIT_AUDIT_REPORT_FILE: $AUDIT_REPORT_FILE"
        echo "UNIT_AUDIT_REPORT_JSON_FILE: $AUDIT_REPORT_JSON_FILE"
        echo "UNIT_RUBRIC_GATES_FILE: $RUBRIC_GATES_FILE"
        echo "UNIT_MANIFEST_FILE: $MANIFEST_FILE"
        echo "UNIT_CHARTER_FILE: $PROGRAM_CHARTER_FILE"
        echo "SUBJECT_CHARTER_FILE: $SUBJECT_CHARTER_FILE"
    fi
    exit 0
fi

run_stage_preflight "$stage" || exit 1

available_docs_json="$("$PYTHON_PARSE_BIN" - "$UNIT_DIR" <<'PY'
import json
import sys
from pathlib import Path

unit_dir = Path(sys.argv[1])
if not unit_dir.is_dir():
    print("[]")
    raise SystemExit(0)

candidates = [
    "brief.json",
    "design.json",
    "content-model.json",
    "design-decisions.json",
    "assessment-blueprint.json",
    "template-selection.json",
    "exercise-design.json",
    "sequence.json",
    "rubric-gates.json",
    "audit-report.json",
    "outputs/manifest.json",
]

present = [name for name in candidates if (unit_dir / name).is_file()]
print(json.dumps(present))
PY
)"

if $JSON_MODE; then
    printf '{"UNIT_DIR":"%s","STAGE":"%s","AVAILABLE_DOCS":%s}\n' "$UNIT_DIR" "$stage" "$available_docs_json"
else
    echo "UNIT_DIR:$UNIT_DIR"
    echo "STAGE:$stage"
    echo "AVAILABLE_DOCS:"
    "$PYTHON_PARSE_BIN" - "$available_docs_json" <<'PY'
import json
import sys
for item in json.loads(sys.argv[1]):
    print(f"  ✓ {item}")
PY
fi
