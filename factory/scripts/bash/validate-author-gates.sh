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
RUBRIC_VALIDATOR_TOOL="$(resolve_python_tool validate_rubric_gates.py)"

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi

audit_json_file="$AUDIT_REPORT_JSON_FILE"
rubric_unchecked=0
rubric_blockers=0
audit_decision="MISSING"
audit_open_critical=0
audit_open_high=0
contract_status="BLOCK"
contract_summary="validation-not-run"
contract_response_version=""
contract_pipeline=""
contract_blocking_steps=""
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
    print("BLOCK\tinvalid-contract-validator-output\t\t\t")
    raise SystemExit(0)

status = str(payload.get("STATUS", "BLOCK")).upper()
missing = len(payload.get("MISSING_FILES", [])) + len(payload.get("MISSING_SCHEMAS", []))
errors = len(payload.get("ERRORS", []))
phase_summary = payload.get("PHASE_SUMMARY", {})
open_critical = int(phase_summary.get("open_critical", 0)) if isinstance(phase_summary, dict) else 0
open_high = int(phase_summary.get("open_high", 0)) if isinstance(phase_summary, dict) else 0
blocking = open_critical + open_high
response_version = str(payload.get("RESPONSE_VERSION", ""))
pipeline = payload.get("PIPELINE", {})
pipeline_name = str(pipeline.get("name", "")) if isinstance(pipeline, dict) else ""
agent_report = payload.get("AGENT_REPORT", {})
blocking_steps = agent_report.get("blocking_steps", []) if isinstance(agent_report, dict) else []
blocking_steps_text = ",".join(str(item) for item in blocking_steps if isinstance(item, str))
print(f"{status}\tmissing={missing},errors={errors},blockers={blocking}\t{response_version}\t{pipeline_name}\t{blocking_steps_text}")
PY
)"
    IFS=$'\t' read -r contract_status contract_summary contract_response_version contract_pipeline contract_blocking_steps <<< "$parsed_contract"

    if [[ "$contract_status" != "PASS" ]]; then
        block_detail="$contract_summary"
        if [[ -n "$contract_blocking_steps" ]]; then
            block_detail="$block_detail,steps=$contract_blocking_steps"
        fi
        blockers+=("Artifact contract validation is BLOCK ($block_detail)")
    fi
fi

rubric_parse_errors=0
rubric_parse_output="$($PYTHON_BIN "$RUBRIC_VALIDATOR_TOOL" --rubric-gates-file "$RUBRIC_GATES_FILE" --rubrics-dir "$RUBRICS_DIR" --json 2>/dev/null || true)"
if [[ -z "$rubric_parse_output" ]]; then
    blockers+=("Rubric parser failed to execute")
else
    parsed_rubric="$($PYTHON_BIN - "$rubric_parse_output" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("BLOCK\t0\t0\t1\tinvalid-rubric-parser-output")
    raise SystemExit(0)

status = str(payload.get("STATUS", "BLOCK")).upper()
unchecked = int(payload.get("UNCHECKED_COUNT", 0))
non_pass = int(payload.get("NON_PASS_COUNT", 0))
parse_error_count = int(payload.get("PARSE_ERROR_COUNT", 0))
blockers = payload.get("BLOCKERS", [])
parse_errors = payload.get("PARSE_ERRORS", [])
details = "; ".join([*blockers, *parse_errors]) if (blockers or parse_errors) else ""

print(f"{status}\t{unchecked}\t{non_pass}\t{parse_error_count}\t{details}")
PY
)"
    IFS=$'\t' read -r rubric_parse_status rubric_unchecked rubric_blockers rubric_parse_errors rubric_parse_details <<< "$parsed_rubric"

    if [[ "$rubric_parse_status" != "PASS" ]]; then
        blockers+=("Rubric format validation is BLOCK (${rubric_parse_details:-unknown-parse-error})")
    fi
fi

if [[ $rubric_blockers -gt 0 ]]; then
    blockers+=("Rubric has $rubric_blockers non-pass status item(s)")
fi

if [[ $rubric_unchecked -gt 0 ]]; then
    blockers+=("Rubric has $rubric_unchecked unchecked item(s)")
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
else
    blockers+=("Missing audit report JSON: $audit_json_file")
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
    printf '{"STATUS":"%s","UNIT_DIR":"%s","CONTRACT_STATUS":"%s","CONTRACT_SUMMARY":"%s","CONTRACT_RESPONSE_VERSION":"%s","CONTRACT_PIPELINE":"%s","CONTRACT_BLOCKING_STEPS":"%s","RUBRIC_UNCHECKED":%d,"RUBRIC_BLOCKERS":%d,"RUBRIC_PARSE_ERRORS":%d,"AUDIT_DECISION":"%s","AUDIT_OPEN_CRITICAL":%d,"AUDIT_OPEN_HIGH":%d,"BLOCKERS":"%s"}\n' \
        "$status" "$UNIT_DIR" "$contract_status" "$contract_summary" "$contract_response_version" "$contract_pipeline" "$contract_blocking_steps" "$rubric_unchecked" "$rubric_blockers" "$rubric_parse_errors" "$audit_decision" "$audit_open_critical" "$audit_open_high" "$blocker_text"
else
    echo "STATUS: $status"
    echo "UNIT_DIR: $UNIT_DIR"
    echo "CONTRACT_STATUS: $contract_status"
    echo "CONTRACT_SUMMARY: $contract_summary"
    echo "CONTRACT_RESPONSE_VERSION: $contract_response_version"
    echo "CONTRACT_PIPELINE: $contract_pipeline"
    echo "CONTRACT_BLOCKING_STEPS: $contract_blocking_steps"
    echo "RUBRIC_UNCHECKED: $rubric_unchecked"
    echo "RUBRIC_BLOCKERS: $rubric_blockers"
    echo "RUBRIC_PARSE_ERRORS: $rubric_parse_errors"
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
