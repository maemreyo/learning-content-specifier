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

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi

audit_file="$AUDIT_REPORT_FILE"
audit_json_file="$AUDIT_REPORT_JSON_FILE"
rubric_unchecked=0
rubric_blockers=0
audit_decision="MISSING"
audit_open_critical=0
audit_open_high=0
contract_status="BLOCK"
contract_summary="validation-not-run"
blockers=()

contract_output="$("$SCRIPT_DIR/validate-artifact-contracts.sh" --json --unit-dir "$UNIT_DIR" 2>/dev/null || true)"
if [[ -z "$contract_output" ]]; then
    blockers+=("Artifact contract validation failed to execute")
else
    parsed_contract="$($PYTHON_BIN - "$contract_output" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("BLOCK\tinvalid-contract-validator-output")
    raise SystemExit(0)

status = str(payload.get("STATUS", "BLOCK")).upper()
missing = len(payload.get("MISSING_FILES", [])) + len(payload.get("MISSING_SCHEMAS", []))
errors = len(payload.get("ERRORS", []))
print(f"{status}\tmissing={missing},errors={errors}")
PY
)"
    IFS=$'\t' read -r contract_status contract_summary <<< "$parsed_contract"

    if [[ "$contract_status" != "PASS" ]]; then
        blockers+=("Artifact contract validation is BLOCK ($contract_summary)")
    fi
fi

if [[ ! -d "$RUBRICS_DIR" ]]; then
    blockers+=("Missing rubrics directory: $RUBRICS_DIR")
else
    shopt -s nullglob
    rubric_files=("$RUBRICS_DIR"/*.md)
    shopt -u nullglob

    if [[ ${#rubric_files[@]} -eq 0 ]]; then
        blockers+=("No rubric files found in $RUBRICS_DIR")
    else
        for rubric_file in "${rubric_files[@]}"; do
            [[ -f "$rubric_file" ]] || continue

            count_unchecked=$(grep -Eic '^[[:space:]]*-[[:space:]]*\[[[:space:]]\]' "$rubric_file" || true)
            count_blockers=$(grep -Eic 'status:[[:space:]]*(FAIL|BLOCK|UNSET|TODO)' "$rubric_file" || true)
            rubric_unchecked=$((rubric_unchecked + count_unchecked))
            rubric_blockers=$((rubric_blockers + count_blockers))
        done
    fi
fi

if [[ $rubric_unchecked -gt 0 ]]; then
    blockers+=("Rubric has $rubric_unchecked unchecked item(s)")
fi

if [[ $rubric_blockers -gt 0 ]]; then
    blockers+=("Rubric has $rubric_blockers non-pass status item(s)")
fi

if [[ -f "$audit_json_file" ]]; then
    parsed_audit="$($PYTHON_BIN - "$audit_json_file" <<'PY'
import json
import sys

path = sys.argv[1]

try:
    data = json.loads(open(path, encoding="utf-8").read())
except Exception as exc:
    print(f"ERR\tinvalid-audit-json:{exc}")
    raise SystemExit(0)

try:
    decision = str(data.get("gate_decision", "")).upper()
    critical = int(data.get("open_critical", -1))
    high = int(data.get("open_high", -1))
except Exception as exc:
    print(f"ERR\tinvalid-audit-fields:{exc}")
    raise SystemExit(0)

if decision not in {"PASS", "BLOCK"}:
    print("ERR\tmissing-or-invalid-gate_decision")
    raise SystemExit(0)
if critical < 0:
    print("ERR\tmissing-or-invalid-open_critical")
    raise SystemExit(0)
if high < 0:
    print("ERR\tmissing-or-invalid-open_high")
    raise SystemExit(0)

print(f"OK\t{decision}\t{critical}\t{high}")
PY
)"

    IFS=$'\t' read -r audit_state audit_value1 audit_value2 audit_value3 <<< "$parsed_audit"
    if [[ "$audit_state" == "OK" ]]; then
        audit_decision="$audit_value1"
        audit_open_critical="$audit_value2"
        audit_open_high="$audit_value3"
    else
        blockers+=("Audit JSON invalid: $audit_value1")
    fi
elif [[ -f "$audit_file" ]]; then
    decision_line=$(grep -Eim1 '^Gate Decision:[[:space:]]*(PASS|BLOCK)$' "$audit_file" || true)
    if [[ -n "$decision_line" ]]; then
        audit_decision="${decision_line#*:}"
        audit_decision="$(echo "$audit_decision" | tr -d '[:space:]' | tr '[:lower:]' '[:upper:]')"
    else
        blockers+=("Audit report missing 'Gate Decision: PASS|BLOCK'")
    fi

    critical_line=$(grep -Eim1 '^Open Critical:[[:space:]]*[0-9]+' "$audit_file" || true)
    if [[ -n "$critical_line" ]]; then
        audit_open_critical="$(echo "$critical_line" | grep -Eo '[0-9]+' | head -1)"
    else
        blockers+=("Audit report missing 'Open Critical: <number>'")
    fi

    high_line=$(grep -Eim1 '^Open High:[[:space:]]*[0-9]+' "$audit_file" || true)
    if [[ -n "$high_line" ]]; then
        audit_open_high="$(echo "$high_line" | grep -Eo '[0-9]+' | head -1)"
    else
        blockers+=("Audit report missing 'Open High: <number>'")
    fi
else
    blockers+=("Missing audit report: $audit_file")
fi

if [[ "$audit_decision" != "PASS" ]]; then
    blockers+=("Audit decision is $audit_decision")
fi

if [[ ${audit_open_critical:-0} -gt 0 ]]; then
    blockers+=("Audit has $audit_open_critical open CRITICAL finding(s)")
fi

if [[ ${audit_open_high:-0} -gt 0 ]]; then
    blockers+=("Audit has $audit_open_high open HIGH finding(s)")
fi

status="PASS"
if [[ ${#blockers[@]} -gt 0 ]]; then
    status="BLOCK"
fi

blocker_text=""
if [[ ${#blockers[@]} -gt 0 ]]; then
    IFS='; '
    blocker_text="${blockers[*]}"
    unset IFS
fi

if $JSON_MODE; then
    printf '{"STATUS":"%s","UNIT_DIR":"%s","CONTRACT_STATUS":"%s","CONTRACT_SUMMARY":"%s","RUBRIC_UNCHECKED":%d,"RUBRIC_BLOCKERS":%d,"AUDIT_DECISION":"%s","AUDIT_OPEN_CRITICAL":%d,"AUDIT_OPEN_HIGH":%d,"BLOCKERS":"%s"}\n' \
        "$status" "$UNIT_DIR" "$contract_status" "$contract_summary" "$rubric_unchecked" "$rubric_blockers" "$audit_decision" "$audit_open_critical" "$audit_open_high" "$blocker_text"
else
    echo "STATUS: $status"
    echo "UNIT_DIR: $UNIT_DIR"
    echo "CONTRACT_STATUS: $contract_status"
    echo "CONTRACT_SUMMARY: $contract_summary"
    echo "RUBRIC_UNCHECKED: $rubric_unchecked"
    echo "RUBRIC_BLOCKERS: $rubric_blockers"
    echo "AUDIT_DECISION: $audit_decision"
    echo "AUDIT_OPEN_CRITICAL: $audit_open_critical"
    echo "AUDIT_OPEN_HIGH: $audit_open_high"
    if [[ ${#blockers[@]} -gt 0 ]]; then
        echo "BLOCKERS:"
        for blocker in "${blockers[@]}"; do
            echo "  - $blocker"
        done
    fi
fi

if [[ "$status" == "BLOCK" ]]; then
    exit 1
fi
