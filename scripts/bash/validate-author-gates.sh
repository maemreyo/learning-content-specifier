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

audit_file="$UNIT_DIR/audit-report.md"
rubric_unchecked=0
rubric_blockers=0
audit_decision="MISSING"
audit_open_critical=0
audit_open_high=0
blockers=()

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
            if [[ ! -f "$rubric_file" ]]; then
                continue
            fi

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

if [[ ! -f "$audit_file" ]]; then
    blockers+=("Missing audit report: $audit_file")
else
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
    printf '{"STATUS":"%s","UNIT_DIR":"%s","RUBRIC_UNCHECKED":%d,"RUBRIC_BLOCKERS":%d,"AUDIT_DECISION":"%s","AUDIT_OPEN_CRITICAL":%d,"AUDIT_OPEN_HIGH":%d,"BLOCKERS":"%s"}\n' \
        "$status" "$UNIT_DIR" "$rubric_unchecked" "$rubric_blockers" "$audit_decision" "$audit_open_critical" "$audit_open_high" "$blocker_text"
else
    echo "STATUS: $status"
    echo "UNIT_DIR: $UNIT_DIR"
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
