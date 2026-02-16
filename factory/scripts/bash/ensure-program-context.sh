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
JSON_INTENT_PROGRAM=""
JSON_INTENT_TITLE=""
JSON_INTENT_TEXT=""
JSON_INTENT_DURATION_DAYS=""
JSON_INTENT_TARGET_SESSIONS=""

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
CONTEXT_DIR="$REPO_ROOT/.lcs/context"
PROGRAMS_ROOT="$REPO_ROOT/programs"
TEMPLATE_FILE="$REPO_ROOT/.lcs/templates/charter-template.md"
SUBJECT_CHARTER_FILE="$REPO_ROOT/.lcs/memory/charter.md"
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

preflight_args=("$SCRIPT_DIR/load-stage-context.sh" --json --stage charter)
if [[ -n "$PROGRAM_INTENT" ]]; then
    preflight_args+=(--intent "$PROGRAM_INTENT")
fi
preflight_out="$("${preflight_args[@]}" 2>/dev/null || true)"
if [[ -z "$preflight_out" ]]; then
    echo "ERROR: charter preflight failed to execute" >&2
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
blockers = payload.get("BLOCKERS", [])
print("; ".join(str(item) for item in blockers) if blockers else "unknown-preflight-blocker")
PY
)"
    echo "ERROR: charter preflight BLOCK ($preflight_summary)" >&2
    exit 1
fi

if [[ -n "$PROGRAM_INTENT" ]]; then
    parsed_json_intent="$("$PYTHON_BIN" - "$PROGRAM_INTENT" <<'PY'
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
title = payload.get("title")
intent = payload.get("intent")
duration = payload.get("duration")
sessions = payload.get("sessions")

if isinstance(duration, str):
    duration = "".join(ch for ch in duration if ch.isdigit())
if isinstance(sessions, str):
    sessions = "".join(ch for ch in sessions if ch.isdigit())

duration_text = str(duration) if isinstance(duration, int) or (isinstance(duration, str) and duration) else ""
sessions_text = str(sessions) if isinstance(sessions, int) or (isinstance(sessions, str) and sessions) else ""

print(
    "\t".join(
        [
            str(program).strip() if isinstance(program, str) else "",
            str(title).strip() if isinstance(title, str) else "",
            str(intent).strip() if isinstance(intent, str) else "",
            duration_text,
            sessions_text,
        ]
    )
)
PY
)"
    if [[ -n "$parsed_json_intent" ]]; then
        IFS=$'\t' read -r JSON_INTENT_PROGRAM JSON_INTENT_TITLE JSON_INTENT_TEXT JSON_INTENT_DURATION_DAYS JSON_INTENT_TARGET_SESSIONS <<< "$parsed_json_intent"
        [[ -z "$PROGRAM_OVERRIDE" && -n "$JSON_INTENT_PROGRAM" ]] && PROGRAM_OVERRIDE="$JSON_INTENT_PROGRAM"
        if [[ -n "$JSON_INTENT_TEXT" ]]; then
            PROGRAM_INTENT="$JSON_INTENT_TEXT"
        elif [[ -n "$JSON_INTENT_TITLE" ]]; then
            PROGRAM_INTENT="$JSON_INTENT_TITLE"
        fi
    fi
fi

slugify() {
    echo "$1" \
        | tr '[:upper:]' '[:lower:]' \
        | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g' \
        | cut -c1-40
}

program_base_slug() {
    local value="$1"
    printf '%s\n' "$value" | sed -E 's/-[0-9]{8}-[0-9]{4}(-[0-9]{2})?$//'
}

find_program_matches_for_slug() {
    local intent_slug="$1"
    local dir name base
    [[ -d "$PROGRAMS_ROOT" ]] || return 0

    for dir in "$PROGRAMS_ROOT"/*; do
        [[ -d "$dir" ]] || continue
        name="$(basename "$dir")"
        base="$(program_base_slug "$name")"
        if [[ "$base" == "$intent_slug" ]]; then
            printf '%s\n' "$name"
        fi
    done | sort
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
    local current_program intent_slug current_base
    local matched latest="" match_count=0
    current_program="$(read_context_value "$CONTEXT_DIR/current-program" || true)"

    if [[ -n "$PROGRAM_OVERRIDE" ]]; then
        slugify "$PROGRAM_OVERRIDE"
        return
    fi

    if [[ -n "${LCS_PROGRAM:-}" ]]; then
        slugify "$LCS_PROGRAM"
        return
    fi

    if [[ -z "$PROGRAM_INTENT" ]]; then
        if [[ -n "$current_program" && -d "$PROGRAMS_ROOT/$current_program" ]]; then
            echo "$current_program"
            return
        fi
        generate_program_id "$PROGRAM_INTENT"
        return
    fi

    intent_slug="$(slugify "$PROGRAM_INTENT")"
    if [[ -z "$intent_slug" ]]; then
        if [[ -n "$current_program" && -d "$PROGRAMS_ROOT/$current_program" ]]; then
            echo "$current_program"
            return
        fi
        generate_program_id "$PROGRAM_INTENT"
        return
    fi

    if [[ -n "$current_program" && -d "$PROGRAMS_ROOT/$current_program" ]]; then
        current_base="$(program_base_slug "$current_program")"
        if [[ "$current_base" == "$intent_slug" ]]; then
            echo "$current_program"
            return
        fi
    fi

    while IFS= read -r matched; do
        [[ -n "$matched" ]] || continue
        latest="$matched"
        match_count=$((match_count + 1))
    done < <(find_program_matches_for_slug "$intent_slug")

    if [[ "$match_count" -eq 1 && -n "$latest" ]]; then
        echo "$latest"
        return
    fi

    if [[ "$match_count" -gt 1 && -n "$latest" ]]; then
        echo "[lcs] Info: Multiple program matches for intent '$PROGRAM_INTENT'. Auto-selecting latest: $latest" >&2
        echo "$latest"
        return
    fi

    generate_program_id "$PROGRAM_INTENT"
}

extract_duration_days() {
    local raw="${1:-}"
    local normalized
    normalized="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"

    if [[ "$normalized" =~ ([0-9]{1,3})[[:space:]]*[-]?[[:space:]]*(day|days|ngay|ngày)\b ]]; then
        echo "${BASH_REMATCH[1]}"
        return
    fi

    if [[ "$normalized" =~ ([0-9]{1,3})[[:space:]]*d\b ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

extract_target_sessions() {
    local raw="${1:-}"
    local normalized
    normalized="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"

    if [[ "$normalized" =~ ([0-9]{1,3})[[:space:]]*[-]?[[:space:]]*(session|sessions|buoi|buổi)\b ]]; then
        echo "${BASH_REMATCH[1]}"
        return
    fi
}

read_program_duration_days() {
    local file_path="$1"
    [[ -f "$file_path" ]] || return 0
    "$PYTHON_BIN" - "$file_path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)

value = payload.get("duration_days")
if isinstance(value, int) and value > 0:
    print(value)
    raise SystemExit(0)

estimate = payload.get("duration_days_estimate")
if isinstance(estimate, int) and estimate > 0:
    print(estimate)
PY
}

read_program_target_sessions() {
    local file_path="$1"
    [[ -f "$file_path" ]] || return 0
    "$PYTHON_BIN" - "$file_path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)

value = payload.get("target_sessions")
if isinstance(value, int) and value > 0:
    print(value)
PY
}

read_program_title() {
    local file_path="$1"
    [[ -f "$file_path" ]] || return 0
    "$PYTHON_BIN" - "$file_path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    payload = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)

title = payload.get("title")
if isinstance(title, str) and title.strip():
    print(title.strip())
PY
}

write_program_file() {
    local file_path="$1"
    local program_id="$2"
    local title="$3"
    local target_sessions="$4"
    local session_span="$5"
    local sessions_per_week="$6"
    local expected_units="$7"
    local duration_days_estimate="$8"

    "$PYTHON_BIN" - "$file_path" "$program_id" "$title" "$target_sessions" "$session_span" "$sessions_per_week" "$expected_units" "$duration_days_estimate" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
program_id = sys.argv[2]
title = sys.argv[3]
target_sessions = int(sys.argv[4]) if sys.argv[4].isdigit() else 0
session_span = int(sys.argv[5]) if sys.argv[5].isdigit() else 4
sessions_per_week = int(sys.argv[6]) if sys.argv[6].isdigit() else 3
expected_units = int(sys.argv[7]) if sys.argv[7].isdigit() else 1
duration_days_estimate = int(sys.argv[8]) if sys.argv[8].isdigit() else 0

payload = {
    "program_id": program_id,
    "title": title,
    "status": "draft",
}

if path.exists():
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(existing, dict):
            payload.update(existing)
    except Exception:
        pass

payload["program_id"] = program_id
payload["title"] = title
payload["status"] = "draft"

from datetime import datetime, timezone
now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
payload.setdefault("created_at", now_utc)
payload["updated_at"] = now_utc

if target_sessions > 0:
    payload["progress_unit"] = "study_session"
    payload["target_sessions"] = target_sessions
    payload["session_span"] = session_span
    payload["sessions_per_week_assumption"] = sessions_per_week
    payload["expected_units"] = expected_units
if duration_days_estimate > 0:
    payload["duration_days_estimate"] = duration_days_estimate

path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

write_program_roadmap_files() {
    local roadmap_json="$1"
    local roadmap_md="$2"
    local program_id="$3"
    local target_sessions="$4"
    local session_span="$5"
    local sessions_per_week="$6"
    local expected_units="$7"
    local duration_days_estimate="$8"
    local render_md="$9"

    "$PYTHON_BIN" - "$roadmap_json" "$roadmap_md" "$program_id" "$target_sessions" "$session_span" "$sessions_per_week" "$expected_units" "$duration_days_estimate" "$render_md" <<'PY'
import json
import sys
from pathlib import Path

roadmap_json = Path(sys.argv[1])
roadmap_md = Path(sys.argv[2])
program_id = sys.argv[3]
target_sessions = int(sys.argv[4])
session_span = int(sys.argv[5])
sessions_per_week = int(sys.argv[6])
expected_units = int(sys.argv[7])
duration_days_estimate = int(sys.argv[8]) if sys.argv[8].isdigit() else 0
render_md = str(sys.argv[9]).lower() in {"1", "true", "yes", "on"}

units = []
for index in range(expected_units):
    start = index * session_span + 1
    end = min(target_sessions, (index + 1) * session_span)
    # Keep day estimates optional and clearly marked as derived assumptions.
    day_start = int(((start - 1) / max(sessions_per_week, 1)) * 7) + 1
    day_end = int(((end - 1) / max(sessions_per_week, 1)) * 7) + 7
    units.append(
        {
            "slot": index + 1,
            "session_start": start,
            "session_end": end,
            "estimated_day_start": day_start,
            "estimated_day_end": day_end,
            "suggested_unit_id": f"{index + 1:03d}-sessions-{start:03d}-to-{end:03d}",
        }
    )

payload = {
    "program_id": program_id,
    "progress_unit": "study_session",
    "target_sessions": target_sessions,
    "session_span": session_span,
    "sessions_per_week_assumption": sessions_per_week,
    "expected_units": expected_units,
    "duration_days_estimate": duration_days_estimate,
    "units": units,
}
roadmap_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

if render_md:
    lines = [
        f"# Program Roadmap: {program_id}",
        "",
        f"- Progress unit: study session",
        f"- Target sessions: {target_sessions}",
        f"- Session span per unit: {session_span}",
        f"- Sessions/week assumption: {sessions_per_week}",
        f"- Duration estimate (days): {duration_days_estimate}",
        f"- Expected units: {expected_units}",
        "",
        "| Slot | Session Range | Estimated Day Range | Suggested Unit ID |",
        "|------|---------------|---------------------|-------------------|",
    ]
    for unit in units:
        lines.append(
            f"| {unit['slot']} | {unit['session_start']}-{unit['session_end']} | {unit['estimated_day_start']}-{unit['estimated_day_end']} | `{unit['suggested_unit_id']}` |"
        )

    roadmap_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
}

PROGRAM_ID="$(choose_program_id)"
[[ -z "$PROGRAM_ID" ]] && { echo "ERROR: Could not determine program id" >&2; exit 1; }

PROGRAM_DIR="$PROGRAMS_ROOT/$PROGRAM_ID"
PROGRAM_FILE="$PROGRAM_DIR/program.json"
PROGRAM_CHARTER_FILE="$PROGRAM_DIR/charter.md"
PROGRAM_ROADMAP_JSON_FILE="$PROGRAM_DIR/roadmap.json"
PROGRAM_ROADMAP_MD_FILE="$PROGRAM_DIR/roadmap.md"

mkdir -p "$PROGRAM_DIR/units"
mkdir -p "$CONTEXT_DIR"

DURATION_DAYS="${JSON_INTENT_DURATION_DAYS:-}"
if [[ -z "$DURATION_DAYS" ]]; then
    DURATION_DAYS="$(extract_duration_days "$PROGRAM_INTENT" || true)"
fi
if [[ -z "$DURATION_DAYS" ]]; then
    DURATION_DAYS="$(read_program_duration_days "$PROGRAM_FILE" || true)"
fi
TARGET_SESSIONS="${JSON_INTENT_TARGET_SESSIONS:-}"
if [[ -z "$TARGET_SESSIONS" ]]; then
    TARGET_SESSIONS="$(extract_target_sessions "$PROGRAM_INTENT" || true)"
fi
if [[ -z "$TARGET_SESSIONS" ]]; then
    TARGET_SESSIONS="$(read_program_target_sessions "$PROGRAM_FILE" || true)"
fi

SESSIONS_PER_WEEK=3
SESSION_SPAN=4
EXPECTED_UNITS=1

if [[ -z "$TARGET_SESSIONS" && -n "$DURATION_DAYS" && "$DURATION_DAYS" =~ ^[0-9]+$ && "$DURATION_DAYS" -gt 0 ]]; then
    TARGET_SESSIONS=$(( (DURATION_DAYS * SESSIONS_PER_WEEK + 6) / 7 ))
fi

if [[ -n "$TARGET_SESSIONS" && "$TARGET_SESSIONS" =~ ^[0-9]+$ && "$TARGET_SESSIONS" -gt 0 ]]; then
    EXPECTED_UNITS=$(( (TARGET_SESSIONS + SESSION_SPAN - 1) / SESSION_SPAN ))
elif [[ -n "$DURATION_DAYS" && "$DURATION_DAYS" =~ ^[0-9]+$ && "$DURATION_DAYS" -gt 0 ]]; then
    EXPECTED_UNITS=$(( (DURATION_DAYS + 6) / 7 ))
fi

if [[ ! -f "$PROGRAM_FILE" ]]; then
    TITLE="$PROGRAM_INTENT"
    [[ -z "$TITLE" ]] && TITLE="$PROGRAM_ID"
    write_program_file "$PROGRAM_FILE" "$PROGRAM_ID" "$TITLE" "${TARGET_SESSIONS:-0}" "$SESSION_SPAN" "$SESSIONS_PER_WEEK" "$EXPECTED_UNITS" "${DURATION_DAYS:-0}"
elif { [[ -n "$TARGET_SESSIONS" && "$TARGET_SESSIONS" =~ ^[0-9]+$ && "$TARGET_SESSIONS" -gt 0 ]]; } || { [[ -n "$DURATION_DAYS" && "$DURATION_DAYS" =~ ^[0-9]+$ && "$DURATION_DAYS" -gt 0 ]]; }; then
    TITLE="$(read_program_title "$PROGRAM_FILE" || true)"
    [[ -z "$TITLE" ]] && TITLE="$PROGRAM_INTENT"
    [[ -z "$TITLE" ]] && TITLE="$PROGRAM_ID"
    write_program_file "$PROGRAM_FILE" "$PROGRAM_ID" "$TITLE" "${TARGET_SESSIONS:-0}" "$SESSION_SPAN" "$SESSIONS_PER_WEEK" "$EXPECTED_UNITS" "${DURATION_DAYS:-0}"
fi

if should_render_md_sidecar "$RENDER_MD_SIDECAR" && [[ ! -f "$PROGRAM_CHARTER_FILE" ]]; then
    if [[ -f "$TEMPLATE_FILE" ]]; then
        cp "$TEMPLATE_FILE" "$PROGRAM_CHARTER_FILE"
    else
        touch "$PROGRAM_CHARTER_FILE"
    fi
fi

if [[ -n "$TARGET_SESSIONS" && "$TARGET_SESSIONS" =~ ^[0-9]+$ && "$TARGET_SESSIONS" -ge 8 ]]; then
    write_program_roadmap_files "$PROGRAM_ROADMAP_JSON_FILE" "$PROGRAM_ROADMAP_MD_FILE" "$PROGRAM_ID" "$TARGET_SESSIONS" "$SESSION_SPAN" "$SESSIONS_PER_WEEK" "$EXPECTED_UNITS" "${DURATION_DAYS:-0}" "$RENDER_MD_SIDECAR"
fi

write_context_value "$CONTEXT_DIR/current-program" "$PROGRAM_ID"
rm -f "$CONTEXT_DIR/current-unit"

export LCS_PROGRAM="$PROGRAM_ID"

if $JSON_MODE; then
    printf '{"PROGRAM_ID":"%s","PROGRAM_DIR":"%s","PROGRAM_FILE":"%s","PROGRAM_CHARTER_FILE":"%s","PROGRAM_ROADMAP_JSON_FILE":"%s","PROGRAM_ROADMAP_MD_FILE":"%s","TARGET_SESSIONS":%d,"DURATION_DAYS":%d,"EXPECTED_UNITS":%d,"SUBJECT_CHARTER_FILE":"%s"}\n' \
        "$PROGRAM_ID" "$PROGRAM_DIR" "$PROGRAM_FILE" "$PROGRAM_CHARTER_FILE" "$PROGRAM_ROADMAP_JSON_FILE" "$PROGRAM_ROADMAP_MD_FILE" "${TARGET_SESSIONS:-0}" "${DURATION_DAYS:-0}" "$EXPECTED_UNITS" "$SUBJECT_CHARTER_FILE"
else
    echo "PROGRAM_ID: $PROGRAM_ID"
    echo "PROGRAM_DIR: $PROGRAM_DIR"
    echo "PROGRAM_FILE: $PROGRAM_FILE"
    echo "PROGRAM_CHARTER_FILE: $PROGRAM_CHARTER_FILE"
    echo "PROGRAM_ROADMAP_JSON_FILE: $PROGRAM_ROADMAP_JSON_FILE"
    echo "PROGRAM_ROADMAP_MD_FILE: $PROGRAM_ROADMAP_MD_FILE"
    echo "TARGET_SESSIONS: ${TARGET_SESSIONS:-0}"
    echo "DURATION_DAYS: ${DURATION_DAYS:-0}"
    echo "EXPECTED_UNITS: $EXPECTED_UNITS"
    echo "SUBJECT_CHARTER_FILE: $SUBJECT_CHARTER_FILE"
fi
