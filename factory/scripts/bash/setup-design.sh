#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false
FORCE_RESET=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --force-reset) FORCE_RESET=true ;;
        --help|-h)
            echo "Usage: $0 [--json] [--force-reset]"
            exit 0
            ;;
    esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

eval "$(get_unit_paths)"
check_unit_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1
CONTRACT_VERSION="$(get_contract_version)"
SELECTOR_TOOL="$(resolve_python_tool generate_template_selection.py)"

compute_sha256() {
    local target_file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$target_file" | awk '{print $1}'
        return
    fi
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$target_file" | awk '{print $1}'
        return
    fi
    if command -v openssl >/dev/null 2>&1; then
        openssl dgst -sha256 "$target_file" | awk '{print $NF}'
        return
    fi
    local py="python3"
    if ! command -v "$py" >/dev/null 2>&1; then
        py="python"
    fi
    "$py" - "$target_file" <<'PY'
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

mkdir -p "$UNIT_DIR" "$RUBRICS_DIR" "$OUTPUTS_DIR"

TEMPLATE="$REPO_ROOT/.lcs/templates/design-template.md"
if [[ "$FORCE_RESET" == "true" || ! -f "$DESIGN_FILE" ]]; then
    if [[ -f "$TEMPLATE" ]]; then
        cp "$TEMPLATE" "$DESIGN_FILE"
    else
        touch "$DESIGN_FILE"
    fi
fi

[[ -f "$CONTENT_MODEL_FILE" ]] || touch "$CONTENT_MODEL_FILE"
[[ -f "$ASSESSMENT_MAP_FILE" ]] || touch "$ASSESSMENT_MAP_FILE"
[[ -f "$DELIVERY_GUIDE_FILE" ]] || touch "$DELIVERY_GUIDE_FILE"
[[ -f "$SEQUENCE_FILE" ]] || touch "$SEQUENCE_FILE"
[[ -f "$AUDIT_REPORT_FILE" ]] || touch "$AUDIT_REPORT_FILE"

UNIT_ID="$(basename "$UNIT_DIR")"
NOW_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [[ ! -f "$BRIEF_FILE" ]]; then
    touch "$BRIEF_FILE"
fi
BRIEF_CHECKSUM="$(compute_sha256 "$BRIEF_FILE")"

if [[ "$FORCE_RESET" == "true" || ! -f "$BRIEF_JSON_FILE" ]]; then
    cat > "$BRIEF_JSON_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "title": "$UNIT_ID",
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
  }
}
EOF
fi

if [[ "$FORCE_RESET" == "true" || ! -f "$DESIGN_JSON_FILE" ]]; then
    cat > "$DESIGN_JSON_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "generated_at": "$NOW_UTC",
  "instructional_strategy": {
    "primary_method": "retrieval-practice",
    "secondary_methods": ["worked-examples"],
    "rationale": "Corporate L&D default; refine with design evidence."
  },
  "pedagogy_decisions": {
    "profile": "corporate-lnd-v1",
    "confidence_threshold": 0.7,
    "confidence": 0.0,
    "candidate_methods": [
      "direct-instruction",
      "worked-examples",
      "retrieval-practice",
      "problem-based-learning",
      "project-based-learning",
      "case-based-learning",
      "peer-instruction",
      "simulation-lab"
    ],
    "scores": {
      "learner_fit": 0.0,
      "outcome_fit": 0.0,
      "evidence_fit": 0.0,
      "delivery_fit": 0.0,
      "accessibility_fit": 0.0
    },
    "selection_rules": {
      "max_secondary_methods": 2,
      "score_delta_threshold": 0.4
    },
    "research": {
      "required": false,
      "triggers": [],
      "evidence_refs": []
    }
  },
  "metadata": {
    "audience": "unspecified",
    "duration_minutes": 60,
    "modality": "unspecified"
  }
}
EOF
fi

if [[ "$FORCE_RESET" == "true" || ! -f "$CONTENT_MODEL_JSON_FILE" ]]; then
    cat > "$CONTENT_MODEL_JSON_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "course": {
    "id": "course-01",
    "title": "Populate from design.md"
  },
  "modules": [
    {
      "id": "module-01",
      "title": "Populate from design.md",
      "lessons": [
        {
          "id": "lesson-01",
          "title": "Populate from design.md",
          "lo_refs": ["LO1"],
          "estimated_minutes": 30
        }
      ]
    }
  ],
  "dependency_graph": {
    "nodes": ["LO1"],
    "edges": [],
    "cycle_check_passed": true
  },
  "duration_tolerance": {
    "lower_percent": -10,
    "upper_percent": 15
  }
}
EOF
fi

if [[ "$FORCE_RESET" == "true" || ! -f "$DESIGN_DECISIONS_FILE" ]]; then
    cat > "$DESIGN_DECISIONS_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "profile": "corporate-lnd-v1",
  "weights": {
    "outcome_fit": 0.3,
    "evidence_fit": 0.25,
    "learner_fit": 0.2,
    "delivery_fit": 0.15,
    "accessibility_fit": 0.1
  },
  "candidate_methods": [
    "direct-instruction",
    "worked-examples",
    "retrieval-practice",
    "problem-based-learning",
    "project-based-learning",
    "case-based-learning",
    "peer-instruction",
    "simulation-lab"
  ],
  "scores": {
    "direct-instruction": 0.0,
    "worked-examples": 0.0,
    "retrieval-practice": 0.0,
    "problem-based-learning": 0.0,
    "project-based-learning": 0.0,
    "case-based-learning": 0.0,
    "peer-instruction": 0.0,
    "simulation-lab": 0.0
  },
  "selected_primary": "",
  "selected_secondary": [],
  "rationale": "Populate from /lcs.design decision process.",
  "confidence_threshold": 0.7,
  "confidence": 0.0,
  "web_research_triggers": [
    "time-sensitive domain/tooling",
    "confidence below threshold",
    "conflicting artifact signals",
    "explicit validation request"
  ],
  "research_evidence_refs": []
}
EOF
fi

if [[ "$FORCE_RESET" == "true" || ! -f "$ASSESSMENT_BLUEPRINT_FILE" ]]; then
    cat > "$ASSESSMENT_BLUEPRINT_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "subject": "english",
  "template_pack_version": "1.0.0",
  "target_distribution": [
    {
      "template_id": "mcq.v1",
      "exercise_type": "MCQ",
      "ratio_percent": 40
    },
    {
      "template_id": "tfng.v1",
      "exercise_type": "TFNG",
      "ratio_percent": 30
    },
    {
      "template_id": "sentence-rewrite.v1",
      "exercise_type": "SENTENCE_REWRITE",
      "ratio_percent": 30
    }
  ],
  "tolerance_percent": 10,
  "lo_mapping": {
    "LO1": ["mcq.v1", "tfng.v1", "sentence-rewrite.v1"]
  }
}
EOF
fi

if [[ "$FORCE_RESET" == "true" || ! -f "$TEMPLATE_SELECTION_FILE" ]]; then
    cat > "$TEMPLATE_SELECTION_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "subject": "english",
  "catalog_version": "1.0.0",
  "top_k": 3,
  "selected_templates": [
    {
      "template_id": "mcq.v1",
      "exercise_type": "MCQ",
      "score": 0.9,
      "score_breakdown": {
        "lo_fit": 1.0,
        "level_fit": 0.9,
        "duration_fit": 0.8,
        "diversity_fit": 0.9
      },
      "rationale": "Balanced starter item for broad LO coverage."
    },
    {
      "template_id": "tfng.v1",
      "exercise_type": "TFNG",
      "score": 0.86,
      "score_breakdown": {
        "lo_fit": 0.9,
        "level_fit": 0.8,
        "duration_fit": 0.9,
        "diversity_fit": 0.85
      },
      "rationale": "Supports evidence-based reading validation."
    },
    {
      "template_id": "sentence-rewrite.v1",
      "exercise_type": "SENTENCE_REWRITE",
      "score": 0.84,
      "score_breakdown": {
        "lo_fit": 0.85,
        "level_fit": 0.8,
        "duration_fit": 0.8,
        "diversity_fit": 0.9
      },
      "rationale": "Evaluates expressive accuracy and transformation skill."
    }
  ],
  "selection_rationale": "Default English starter selection; refine with unit-specific intent."
}
EOF
fi

if [[ "$FORCE_RESET" == "true" || ! -f "$SEQUENCE_JSON_FILE" ]]; then
    cat > "$SEQUENCE_JSON_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "tasks": []
}
EOF
fi

if [[ "$FORCE_RESET" == "true" || ! -f "$AUDIT_REPORT_JSON_FILE" ]]; then
    cat > "$AUDIT_REPORT_JSON_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "gate_decision": "BLOCK",
  "open_critical": 0,
  "open_high": 0,
  "findings": [],
  "role_readiness": {
    "teacher_ready": false,
    "creator_ready": false,
    "ops_ready": false
  }
}
EOF
fi

# Attempt deterministic template auto-select (English-first). If no template pack
# is available for the current repo, the selector returns SKIP and scaffolds remain.
selector_args=(
    "$SELECTOR_TOOL"
    --repo-root "$REPO_ROOT"
    --unit-dir "$UNIT_DIR"
    --json
)
if command -v uv >/dev/null 2>&1; then
    selector_output="$(uv run python "${selector_args[@]}" 2>/dev/null || true)"
else
    PYTHON_BIN="python3"
    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        PYTHON_BIN="python"
    fi
    selector_output="$("$PYTHON_BIN" "${selector_args[@]}" 2>/dev/null || true)"
fi

if [[ -n "$selector_output" ]]; then
    PYTHON_PARSE_BIN="python3"
    if ! command -v "$PYTHON_PARSE_BIN" >/dev/null 2>&1; then
        PYTHON_PARSE_BIN="python"
    fi
    selector_status="$(
        "$PYTHON_PARSE_BIN" - "$selector_output" <<'PY'
import json
import sys
try:
    payload = json.loads(sys.argv[1])
except Exception:
    print("")
    raise SystemExit(0)
print(str(payload.get("STATUS", "")).upper())
PY
    )"
    if [[ "$selector_status" == "BLOCK" ]]; then
        echo "ERROR: template selector blocked setup-design for $UNIT_DIR" >&2
        exit 1
    fi
fi

ASSESSMENT_BLUEPRINT_CHECKSUM="$(compute_sha256 "$ASSESSMENT_BLUEPRINT_FILE")"
TEMPLATE_SELECTION_CHECKSUM="$(compute_sha256 "$TEMPLATE_SELECTION_FILE")"

if [[ "$FORCE_RESET" == "true" || ! -f "$MANIFEST_FILE" ]]; then
    cat > "$MANIFEST_FILE" <<EOF
{
  "contract_version": "$CONTRACT_VERSION",
  "unit_id": "$UNIT_ID",
  "title": "$UNIT_ID",
  "locale": "en-US",
  "generated_at": "$NOW_UTC",
  "outcomes": [
    {
      "lo_id": "LO1",
      "priority": "P1",
      "evidence_refs": ["brief:LO1"]
    }
  ],
  "artifacts": [
    {
      "id": "brief-md",
      "type": "brief",
      "path": "brief.md",
      "media_type": "text/markdown",
      "checksum": "sha256:$BRIEF_CHECKSUM"
    },
    {
      "id": "assessment-blueprint-json",
      "type": "assessment-blueprint",
      "path": "assessment-blueprint.json",
      "media_type": "application/json",
      "checksum": "sha256:$ASSESSMENT_BLUEPRINT_CHECKSUM"
    },
    {
      "id": "template-selection-json",
      "type": "template-selection",
      "path": "template-selection.json",
      "media_type": "application/json",
      "checksum": "sha256:$TEMPLATE_SELECTION_CHECKSUM"
    }
  ],
  "gate_status": {
    "decision": "BLOCK",
    "open_critical": 0,
    "open_high": 0
  },
  "interop": {
    "xapi": {
      "version": "2.0.0",
      "activity_id_set": ["https://example.org/xapi/activity/LO1"],
      "statement_template_refs": ["https://example.org/xapi/template/LO1"]
    }
  }
}
EOF
fi

if $JSON_MODE; then
    printf '{"BRIEF_FILE":"%s","DESIGN_FILE":"%s","UNIT_DIR":"%s","BRANCH":"%s","HAS_GIT":%s}\n' \
        "$BRIEF_FILE" "$DESIGN_FILE" "$UNIT_DIR" "$CURRENT_BRANCH" "$HAS_GIT"
else
    echo "BRIEF_FILE: $BRIEF_FILE"
    echo "DESIGN_FILE: $DESIGN_FILE"
    echo "UNIT_DIR: $UNIT_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi
