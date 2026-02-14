---
description: Generate learning design artifacts from the unit brief and charter.
handoffs:
  - label: Build Production Sequence
    agent: lcs.sequence
    prompt: Create a production sequence from design artifacts.
    send: true
  - label: Generate Rubric
    agent: lcs.rubric
    prompt: Generate hard-gate rubric for this unit.
scripts:
  sh: factory/scripts/bash/setup-design.sh --json
  ps: factory/scripts/powershell/setup-design.ps1 -Json
agent_scripts:
  sh: factory/scripts/bash/update-agent-context.sh __AGENT__
  ps: factory/scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## Intent

Produce complete learning design artifacts from brief + charter with deterministic pedagogy decisions and machine-readable contracts.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST preserve existing `design.md` content unless an explicit reset is requested.
- YOU MUST generate and maintain `content-model.md`, `assessment-map.md`, `delivery-guide.md`.
- YOU MUST generate or update `design.json`, `content-model.json`, `design-decisions.json`, `assessment-blueprint.json`, `template-selection.json`, and `outputs/manifest.json`.
- YOU MUST apply Corporate L&D default pedagogy weights:
  - `outcome_fit=0.30`
  - `evidence_fit=0.25`
  - `learner_fit=0.20`
  - `delivery_fit=0.15`
  - `accessibility_fit=0.10`
- YOU MUST apply selection rule: max 2 secondary methods with `score_delta <= 0.40`.
- YOU MUST mark research required when confidence `< 0.70`.
- YOU MUST load subject template catalog (English-first) and produce weighted top-K template candidates.
- YOU MUST include score breakdown (`lo_fit`, `level_fit`, `duration_fit`, `diversity_fit`) in `template-selection.json`.
- YOU MUST NOT bypass charter constraints.

## Execution Steps

1. Run `{SCRIPT}` and parse `BRIEF_FILE`, `DESIGN_FILE`, `UNIT_DIR`, `BRANCH`, `HAS_GIT`.
2. Load `BRIEF_FILE`, `.lcs/memory/charter.md`, and `.lcs/templates/design-template.md`.
3. Produce/update design artifacts under `UNIT_DIR`.
4. Update decision contracts (`design.json`, `design-decisions.json`) with scored pedagogy rationale.
5. If confidence `< 0.70` OR domain is time-sensitive OR artifacts conflict, add evidence references to `research.md` and `design-decisions.json`.
6. Update `content-model.json` with module/lesson LO references and dependency graph cycle check.
7. Generate/update `assessment-blueprint.json` with template ratio targets and LO mapping.
8. Generate/update `template-selection.json` with top-K candidates and final selected template set.
9. Ensure `outputs/manifest.json` remains valid, xAPI interop block exists, and new template artifacts are registered.
10. Run `{AGENT_SCRIPT}` to refresh agent context from learning profile.
11. Report artifacts and unresolved risks.

## Hard Gates

- Gate G-DS-001: each LO has mapped activity and assessment strategy.
- Gate G-DS-002: pedagogy decision log includes method scores, selected primary, selected secondary, confidence.
- Gate G-DS-003: accessibility/readability controls are explicit.
- Gate G-DS-004: duration estimate is within tolerance (`-10%` to `+15%`) or explicitly blocked.
- Gate G-DS-005: `design.json`, `content-model.json`, `design-decisions.json`, and `outputs/manifest.json` are present.
- Gate G-DS-006: `assessment-blueprint.json` and `template-selection.json` are present and machine-parseable.

## Failure Modes

- Missing brief: stop and require `/lcs.define`.
- Charter conflict: stop and surface blocking policy mismatch.
- Cyclic LO dependency graph: stop and request explicit decomposition fix.
- Partial artifact generation: stop and list missing files.

## Output Contract

- Markdown: `design.md`, `content-model.md`, `assessment-map.md`, `delivery-guide.md`.
- JSON: `design.json`, `content-model.json`, `design-decisions.json`, `outputs/manifest.json`.
- JSON: `design.json`, `content-model.json`, `design-decisions.json`, `assessment-blueprint.json`, `template-selection.json`, `outputs/manifest.json`.
- Execution summary includes `HAS_GIT` state, confidence score, and research trigger decision.

## Examples

- Success: design includes LO-to-assessment matrix, scored pedagogy rationale, and valid machine-readable contracts.
- Fail: design omits decision scores or produces cyclic LO dependency graph.
