#!/usr/bin/env bash

# Update agent context files with information from design.md

set -euo pipefail

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_unit_paths)"
AGENT_TYPE="${1:-}"

CLAUDE_FILE="$REPO_ROOT/CLAUDE.md"
GEMINI_FILE="$REPO_ROOT/GEMINI.md"
COPILOT_FILE="$REPO_ROOT/.github/agents/copilot-instructions.md"
CURSOR_FILE="$REPO_ROOT/.cursor/rules/lcs-rules.mdc"
QWEN_FILE="$REPO_ROOT/QWEN.md"
OPENCODE_FILE="$REPO_ROOT/AGENTS.md"
CODEX_FILE="$REPO_ROOT/AGENTS.md"
WINDSURF_FILE="$REPO_ROOT/.windsurf/rules/lcs-rules.md"
KILOCODE_FILE="$REPO_ROOT/.kilocode/rules/lcs-rules.md"
AUGGIE_FILE="$REPO_ROOT/.augment/rules/lcs-rules.md"
ROO_FILE="$REPO_ROOT/.roo/rules/lcs-rules.md"
CODEBUDDY_FILE="$REPO_ROOT/CODEBUDDY.md"
QODER_FILE="$REPO_ROOT/QODER.md"
AMP_FILE="$REPO_ROOT/AGENTS.md"
SHAI_FILE="$REPO_ROOT/SHAI.md"
Q_FILE="$REPO_ROOT/AGENTS.md"
BOB_FILE="$REPO_ROOT/AGENTS.md"

TEMPLATE_FILE="$REPO_ROOT/.lcs/templates/agent-file-template.md"

extract_field_from_file() {
    local file="$1"
    local field_name="$2"
    local escaped

    [[ -f "$file" ]] || return 0

    escaped="$(printf '%s' "$field_name" | sed -e 's/[][(){}.^$*+?|\\/]/\\&/g')"
    grep -Eim1 "^[[:space:]]*-?[[:space:]]*(\\*\\*${escaped}\\*\\*|${escaped})[[:space:]]*:[[:space:]]*" "$file" 2>/dev/null \
        | sed -E "s/^[[:space:]]*-?[[:space:]]*(\\*\\*${escaped}\\*\\*|${escaped})[[:space:]]*:[[:space:]]*//I" \
        | sed 's/^[ \t]*//;s/[ \t]*$//'
}

extract_learning_field() {
    local field_name="$1"
    local value

    value="$(extract_field_from_file "$DESIGN_FILE" "$field_name")"
    if [[ -z "$value" ]]; then
        value="$(extract_field_from_file "$BRIEF_FILE" "$field_name")"
    fi

    echo "$value"
}

AUDIENCE="$(extract_learning_field "Audience Profile")"
DURATION="$(extract_learning_field "Duration Budget")"
MODALITY="$(extract_learning_field "Modality Mix")"
DELIVERY_MODE="$(extract_learning_field "Delivery Mode")"
LEVEL="$(extract_learning_field "Entry Level")"

STRUCTURE_PATH="programs/${PROGRAM_ID:-<program-id>}/units/${CURRENT_UNIT:-<unit-id>}"
TECH_LINE="- Audience: ${AUDIENCE:-unknown} | Level: ${LEVEL:-unknown} | Duration: ${DURATION:-unknown} | Modality: ${MODALITY:-unknown} | Mode: ${DELIVERY_MODE:-unknown} (${STRUCTURE_PATH})"
RECENT_LINE="- ${STRUCTURE_PATH}: Updated unit learning profile (${MODALITY:-unknown})"

create_from_template() {
    local target_file="$1" project_name
    project_name="$(basename "$REPO_ROOT")"
    mkdir -p "$(dirname "$target_file")"
    sed \
        -e "s|\[PROJECT NAME\]|$project_name|g" \
        -e "s|\[DATE\]|$(date +%Y-%m-%d)|g" \
        -e "s|\[EXTRACTED FROM ALL DESIGN.MD FILES\]|$TECH_LINE|g" \
        -e "s|\[ACTUAL STRUCTURE FROM PLANS\]|${STRUCTURE_PATH}/\\n  outputs/|g" \
        -e "s|\[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES\]|/lcs.define, /lcs.design, /lcs.sequence, /lcs.rubric, /lcs.audit, /lcs.author|g" \
        -e "s|\[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE\]|Use concise, learner-centered writing and consistent terminology.|g" \
        -e "s|\[LAST 3 FEATURES AND WHAT THEY ADDED\]|$RECENT_LINE|g" \
        "$TEMPLATE_FILE" > "$target_file"
}

update_agent_file() {
    local file="$1"
    [[ -f "$TEMPLATE_FILE" ]] || { echo "ERROR: Missing template at $TEMPLATE_FILE" >&2; exit 1; }

    if [[ ! -f "$file" ]]; then
        create_from_template "$file"
        echo "✓ Created: $file"
        return
    fi

    if ! grep -Fq "$TECH_LINE" "$file"; then
        awk -v line="$TECH_LINE" '
            /^## Active Learning Profiles$/ {print; print ""; print line; next}
            {print}
        ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
    fi

    if ! grep -Fq "$RECENT_LINE" "$file"; then
        awk -v line="$RECENT_LINE" '
            /^## Recent Unit Changes$/ {print; print ""; print line; next}
            {print}
        ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
    fi

    echo "✓ Updated: $file"
}

case "$AGENT_TYPE" in
    claude) update_agent_file "$CLAUDE_FILE" ;;
    gemini) update_agent_file "$GEMINI_FILE" ;;
    copilot) update_agent_file "$COPILOT_FILE" ;;
    cursor-agent) update_agent_file "$CURSOR_FILE" ;;
    qwen) update_agent_file "$QWEN_FILE" ;;
    opencode) update_agent_file "$OPENCODE_FILE" ;;
    codex) update_agent_file "$CODEX_FILE" ;;
    windsurf) update_agent_file "$WINDSURF_FILE" ;;
    kilocode) update_agent_file "$KILOCODE_FILE" ;;
    auggie) update_agent_file "$AUGGIE_FILE" ;;
    roo) update_agent_file "$ROO_FILE" ;;
    codebuddy) update_agent_file "$CODEBUDDY_FILE" ;;
    qoder) update_agent_file "$QODER_FILE" ;;
    amp) update_agent_file "$AMP_FILE" ;;
    shai) update_agent_file "$SHAI_FILE" ;;
    q) update_agent_file "$Q_FILE" ;;
    bob) update_agent_file "$BOB_FILE" ;;
    "")
        for file in "$CLAUDE_FILE" "$GEMINI_FILE" "$COPILOT_FILE" "$CURSOR_FILE" "$QWEN_FILE" "$OPENCODE_FILE" "$CODEX_FILE" "$WINDSURF_FILE" "$KILOCODE_FILE" "$AUGGIE_FILE" "$ROO_FILE" "$CODEBUDDY_FILE" "$QODER_FILE" "$AMP_FILE" "$SHAI_FILE" "$Q_FILE" "$BOB_FILE"; do
            [[ -f "$file" ]] && update_agent_file "$file"
        done
        ;;
    *)
        echo "ERROR: Unknown agent type '$AGENT_TYPE'" >&2
        exit 1
        ;;
esac
