#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
SHORT_NAME=""
UNIT_NUMBER=""
PROGRAM_OVERRIDE=""
CHECKOUT_BRANCH=false
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
        --program)
            PROGRAM_OVERRIDE="${2:-}"
            shift 2
            ;;
        --checkout-branch)
            CHECKOUT_BRANCH=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--program <id>] [--short-name <name>] [--number N] [--checkout-branch] <unit_description>"
            exit 0
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

UNIT_DESCRIPTION="${ARGS[*]:-}"
[[ -z "$UNIT_DESCRIPTION" ]] && {
    echo "Usage: $0 [--json] [--program <id>] [--short-name <name>] [--number N] [--checkout-branch] <unit_description>" >&2
    exit 1
}

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
CONTEXT_DIR="$REPO_ROOT/.lcs/context"
PROGRAMS_ROOT="$REPO_ROOT/programs"
PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi
RENDER_MD_SIDECAR="${LCS_RENDER_MD_SIDECAR:-0}"

should_render_md_sidecar() {
    case "${1:-0}" in
        1|true|TRUE|yes|YES|on|ON)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

mkdir -p "$CONTEXT_DIR" "$PROGRAMS_ROOT"

if [[ "$UNIT_DESCRIPTION" == \{* ]]; then
    parsed_json_args="$("$PYTHON_BIN" - "$UNIT_DESCRIPTION" <<'PY'
import json
import sys

raw = sys.argv[1].strip()
if not raw.startswith("{"):
    raise SystemExit(0)
try:
    payload = json.loads(raw)
except Exception:
    raise SystemExit(0)
if not isinstance(payload, dict):
    raise SystemExit(0)

program = payload.get("program")
short_name = payload.get("short_name") or payload.get("slug")
number = payload.get("number")
desc = payload.get("description") or payload.get("title") or payload.get("intent")

number_text = ""
if isinstance(number, int):
    number_text = str(number)
elif isinstance(number, str):
    digits = "".join(ch for ch in number if ch.isdigit())
    number_text = digits

print(
    "\t".join(
        [
            str(program).strip() if isinstance(program, str) else "",
            str(short_name).strip() if isinstance(short_name, str) else "",
            number_text,
            str(desc).strip() if isinstance(desc, str) else "",
        ]
    )
)
PY
)"
    if [[ -n "$parsed_json_args" ]]; then
        IFS=$'\t' read -r JSON_PROGRAM JSON_SHORT_NAME JSON_NUMBER JSON_DESCRIPTION <<< "$parsed_json_args"
        [[ -z "$PROGRAM_OVERRIDE" && -n "${JSON_PROGRAM:-}" ]] && PROGRAM_OVERRIDE="$JSON_PROGRAM"
        [[ -z "$SHORT_NAME" && -n "${JSON_SHORT_NAME:-}" ]] && SHORT_NAME="$JSON_SHORT_NAME"
        [[ -z "$UNIT_NUMBER" && -n "${JSON_NUMBER:-}" ]] && UNIT_NUMBER="$JSON_NUMBER"
        [[ -n "${JSON_DESCRIPTION:-}" ]] && UNIT_DESCRIPTION="$JSON_DESCRIPTION"
    fi
fi

slugify() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

clean_name() {
    slugify "$1" | cut -c1-60
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

resolve_program_id() {
    local candidate=""
    if [[ -n "$PROGRAM_OVERRIDE" ]]; then
        candidate="$(slugify "$PROGRAM_OVERRIDE")"
    elif [[ -n "${LCS_PROGRAM:-}" ]]; then
        candidate="$(slugify "$LCS_PROGRAM")"
    else
        candidate="$(read_context_value "$CONTEXT_DIR/current-program" || true)"
        if [[ -z "$candidate" ]]; then
            candidate="$(infer_program_from_pwd "$REPO_ROOT" || true)"
        fi
    fi
    echo "$candidate"
}

get_highest_from_units() {
    local units_dir="$1" highest=0
    [[ -d "$units_dir" ]] || { echo 0; return; }
    for dir in "$units_dir"/*; do
        [[ -d "$dir" ]] || continue
        local base num
        base="$(basename "$dir")"
        if [[ "$base" =~ ^([0-9]{3})- ]]; then
            num=$((10#${BASH_REMATCH[1]}))
            [[ "$num" -gt "$highest" ]] && highest="$num"
        fi
    done
    echo "$highest"
}

read_roadmap_slot() {
    local roadmap_file="$1"
    local slot_index="$2"
    local py_bin="python3"
    if ! command -v "$py_bin" >/dev/null 2>&1; then
        py_bin="python"
    fi
    "$py_bin" - "$roadmap_file" "$slot_index" <<'PY'
import json
import sys
from pathlib import Path

roadmap = Path(sys.argv[1])
slot = int(sys.argv[2])
if not roadmap.exists():
    raise SystemExit(0)

try:
    payload = json.loads(roadmap.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)

units = payload.get("units", [])
if not isinstance(units, list):
    raise SystemExit(0)

for item in units:
    if not isinstance(item, dict):
        continue
    if int(item.get("slot", -1)) == slot:
        session_start = int(item.get("session_start", item.get("day_start", 0)))
        session_end = int(item.get("session_end", item.get("day_end", 0)))
        day_start = int(item.get("estimated_day_start", item.get("day_start", 0)))
        day_end = int(item.get("estimated_day_end", item.get("day_end", 0)))
        expected = int(payload.get("expected_units", 0))
        print(f"{session_start}\t{session_end}\t{expected}\t{day_start}\t{day_end}")
        raise SystemExit(0)
PY
}

PROGRAM_ID="$(resolve_program_id)"
if [[ -z "$PROGRAM_ID" ]]; then
    echo "ERROR: No active program context found." >&2
    echo "Run /lcs.charter first or pass --program <id>." >&2
    exit 1
fi

preflight_args=("$SCRIPT_DIR/load-stage-context.sh" --json --stage define --program "$PROGRAM_ID")
if [[ -n "$UNIT_DESCRIPTION" ]]; then
    preflight_args+=(--intent "$UNIT_DESCRIPTION")
fi
preflight_out="$("${preflight_args[@]}" 2>/dev/null || true)"
if [[ -z "$preflight_out" ]]; then
    echo "ERROR: define preflight failed to execute" >&2
    exit 1
fi
preflight_status="$("$PYTHON_BIN" - "$preflight_out" <<'PY'
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
if [[ "$preflight_status" != "PASS" ]]; then
    preflight_summary="$("$PYTHON_BIN" - "$preflight_out" <<'PY'
import json
import sys
try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("invalid-preflight-output")
    raise SystemExit(0)
parts = []
missing = payload.get("MISSING_INPUTS", [])
blockers = payload.get("BLOCKERS", [])
if missing:
    parts.append("missing=" + ",".join(str(item) for item in missing))
if blockers:
    parts.append("blockers=" + "; ".join(str(item) for item in blockers))
print(" | ".join(parts) if parts else "unknown-preflight-blocker")
PY
)"
    echo "ERROR: define preflight BLOCK ($preflight_summary)" >&2
    exit 1
fi

PROGRAM_DIR="$PROGRAMS_ROOT/$PROGRAM_ID"
if [[ ! -d "$PROGRAM_DIR" ]]; then
    echo "ERROR: Program directory does not exist: $PROGRAM_DIR" >&2
    echo "Run /lcs.charter first to scaffold the program." >&2
    exit 1
fi

UNITS_DIR="$PROGRAM_DIR/units"
mkdir -p "$UNITS_DIR"

UNIT_SUFFIX="$(clean_name "${SHORT_NAME:-$(generate_name "$UNIT_DESCRIPTION")}")"
[[ -z "$UNIT_SUFFIX" ]] && UNIT_SUFFIX="unit"

if [[ -z "$UNIT_NUMBER" ]]; then
    local_highest="$(get_highest_from_units "$UNITS_DIR")"
    UNIT_NUMBER="$((local_highest + 1))"
fi

UNIT_NUM="$(printf '%03d' "$((10#$UNIT_NUMBER))")"
UNIT_NAME="${UNIT_NUM}-${UNIT_SUFFIX}"
UNIT_DIR="$UNITS_DIR/$UNIT_NAME"
ROADMAP_FILE="$PROGRAM_DIR/roadmap.json"
ROADMAP_SESSION_START=""
ROADMAP_SESSION_END=""
ROADMAP_DAY_ESTIMATE_START=""
ROADMAP_DAY_ESTIMATE_END=""
PROGRAM_EXPECTED_UNITS=""
if [[ -f "$ROADMAP_FILE" ]]; then
    roadmap_slot_output="$(read_roadmap_slot "$ROADMAP_FILE" "$((10#$UNIT_NUM))" || true)"
    if [[ -n "$roadmap_slot_output" ]]; then
        IFS=$'\t' read -r ROADMAP_SESSION_START ROADMAP_SESSION_END PROGRAM_EXPECTED_UNITS ROADMAP_DAY_ESTIMATE_START ROADMAP_DAY_ESTIMATE_END <<< "$roadmap_slot_output"
    fi
fi

if has_git && [[ "$CHECKOUT_BRANCH" == "true" ]]; then
    BRANCH_NAME="${PROGRAM_ID}-${UNIT_NAME}"
    git checkout -b "$BRANCH_NAME" >/dev/null
elif has_git; then
    >&2 echo "[lcs] Info: Branch auto-checkout disabled. Staying on current branch."
fi

mkdir -p "$UNIT_DIR"
CONTRACT_VERSION="$(get_contract_version)"

TEMPLATE="$REPO_ROOT/.lcs/templates/brief-template.md"
BRIEF_FILE="$UNIT_DIR/brief.md"
BRIEF_JSON_FILE="$UNIT_DIR/brief.json"
if should_render_md_sidecar "$RENDER_MD_SIDECAR"; then
    if [[ -f "$TEMPLATE" ]]; then
        cp "$TEMPLATE" "$BRIEF_FILE"
    else
        touch "$BRIEF_FILE"
    fi
fi

if [[ ! -f "$BRIEF_JSON_FILE" ]]; then
    program_scope_block=""
    if [[ -n "$ROADMAP_SESSION_START" && -n "$ROADMAP_SESSION_END" ]]; then
        program_scope_block=$(cat <<EOF_SCOPE
,
  "program_scope": {
    "session_start": $ROADMAP_SESSION_START,
    "session_end": $ROADMAP_SESSION_END,
    "estimated_day_start": ${ROADMAP_DAY_ESTIMATE_START:-0},
    "estimated_day_end": ${ROADMAP_DAY_ESTIMATE_END:-0},
    "slot_index": $((10#$UNIT_NUM)),
    "expected_units": ${PROGRAM_EXPECTED_UNITS:-1}
  }
EOF_SCOPE
)
    fi
    cat > "$BRIEF_JSON_FILE" <<EOF_JSON
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_NAME",
  "program_id": "$PROGRAM_ID",
  "title": "$UNIT_NAME",
  "audience": {
    "primary": "general learners",
    "entry_level": "beginner",
    "delivery_context": "self-paced"
  },
  "duration_minutes": 60,
  "learning_outcomes": [
    {
      "lo_id": "LO1",
      "priority": "P1",
      "statement": "Learner will be able to demonstrate LO1 with measurable evidence.",
      "evidence": "Assessment evidence mapped to LO1 is available in artifacts.",
      "acceptance_criteria": [
        "Given the learning context, When the learner attempts LO1 practice, Then observable evidence meets the completion criteria."
      ]
    }
  ],
  "scope": {
    "in_scope": [],
    "out_of_scope": []
  }${program_scope_block}
}
EOF_JSON
fi

write_context_value "$CONTEXT_DIR/current-program" "$PROGRAM_ID"
write_context_value "$CONTEXT_DIR/current-unit" "$UNIT_NAME"

export LCS_PROGRAM="$PROGRAM_ID"
export LCS_UNIT="$UNIT_NAME"

if $JSON_MODE; then
    printf '{"PROGRAM_ID":"%s","PROGRAM_DIR":"%s","UNIT_NAME":"%s","UNIT_DIR":"%s","BRIEF_JSON_FILE":"%s","BRIEF_FILE":"%s","UNIT_NUM":"%s","SESSION_START":%d,"SESSION_END":%d,"ESTIMATED_DAY_START":%d,"ESTIMATED_DAY_END":%d,"EXPECTED_UNITS":%d}\n' \
        "$PROGRAM_ID" "$PROGRAM_DIR" "$UNIT_NAME" "$UNIT_DIR" "$BRIEF_JSON_FILE" "$BRIEF_FILE" "$UNIT_NUM" "${ROADMAP_SESSION_START:-0}" "${ROADMAP_SESSION_END:-0}" "${ROADMAP_DAY_ESTIMATE_START:-0}" "${ROADMAP_DAY_ESTIMATE_END:-0}" "${PROGRAM_EXPECTED_UNITS:-0}"
else
    echo "PROGRAM_ID: $PROGRAM_ID"
    echo "PROGRAM_DIR: $PROGRAM_DIR"
    echo "UNIT_NAME: $UNIT_NAME"
    echo "UNIT_DIR: $UNIT_DIR"
    echo "BRIEF_JSON_FILE: $BRIEF_JSON_FILE"
    echo "BRIEF_FILE: $BRIEF_FILE"
    echo "UNIT_NUM: $UNIT_NUM"
    echo "SESSION_START: ${ROADMAP_SESSION_START:-0}"
    echo "SESSION_END: ${ROADMAP_SESSION_END:-0}"
    echo "ESTIMATED_DAY_START: ${ROADMAP_DAY_ESTIMATE_START:-0}"
    echo "ESTIMATED_DAY_END: ${ROADMAP_DAY_ESTIMATE_END:-0}"
    echo "EXPECTED_UNITS: ${PROGRAM_EXPECTED_UNITS:-0}"
fi
