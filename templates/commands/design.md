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
  sh: scripts/bash/setup-design.sh --json
  ps: scripts/powershell/setup-design.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---

## Intent

Produce complete learning design artifacts from brief + charter with gate-aware decisions.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST preserve existing `design.md` content unless an explicit reset is requested.
- YOU MUST generate and maintain `content-model.md`, `assessment-map.md`, `delivery-guide.md`.
- YOU MUST encode objective-activity-assessment alignment in design choices.
- YOU MUST NOT bypass charter constraints.

## Execution Steps

1. Run `{SCRIPT}` and parse `BRIEF_FILE`, `DESIGN_FILE`, `UNIT_DIR`, `BRANCH`, `HAS_GIT`.
2. Load `BRIEF_FILE`, `.lcs/memory/charter.md`, and `.lcs/templates/design-template.md`.
3. Create/update required design artifacts under `UNIT_DIR`.
4. Ensure metadata is sufficient for `outputs/` local publishing contract.
5. Run `{AGENT_SCRIPT}` to refresh agent context from learning profile.
6. Report artifacts and unresolved risks.

## Hard Gates

- Gate G-DS-001: each LO has mapped activity and assessment strategy.
- Gate G-DS-002: accessibility/readability controls are explicit.
- Gate G-DS-003: metadata fields are complete for outputs.

## Failure Modes

- Missing brief: stop and require `/lcs.define`.
- Charter conflict: stop and surface blocking policy mismatch.
- Partial artifact generation: stop and list missing files.

## Output Contract

- `design.md`, `content-model.md`, `assessment-map.md`, `delivery-guide.md`.
- Execution summary includes `HAS_GIT` state and gate risk list.

## Examples

- Success: design includes LO-to-assessment matrix and remediation strategy.
- Fail: design omits accessibility baseline and cannot pass gate.
