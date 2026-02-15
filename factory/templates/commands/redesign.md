---
description: Rebuild learning design artifacts for the active unit with a forced reset.
handoffs:
  - label: Build Production Sequence
    agent: lcs.sequence
    prompt: Create a production sequence from rebuilt design artifacts.
    send: true
scripts:
  sh: factory/scripts/bash/setup-design.sh --json --force-reset
  ps: factory/scripts/powershell/setup-design.ps1 -Json -ForceReset
agent_scripts:
  sh: factory/scripts/bash/update-agent-context.sh __AGENT__
  ps: factory/scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
gate_scripts:
  sh: factory/scripts/bash/manage-program-context.sh --json workflow-status
  ps: factory/scripts/powershell/manage-program-context.ps1 --json workflow-status
---

## Intent

Recreate design artifacts for the active unit from `brief.*` and charter constraints when the current design needs a clean reset.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST run `{SCRIPT}` exactly once.
- YOU MUST preserve `brief.md` and `brief.json` as source-of-truth.
- YOU MUST regenerate all required design contracts for the active unit.
- YOU MUST run `{AGENT_SCRIPT}` after regenerating artifacts.
- YOU MUST run `{GATE_SCRIPT}` and use it to produce follow-up tasks.
- YOU MUST NOT run this command if `brief.json.refinement.open_questions > 0`.

## Execution Steps

1. Run `{SCRIPT}` and parse `PROGRAM_ID`, `UNIT_ID`, `UNIT_DIR`, `HAS_GIT`.
2. Rebuild design artifacts from templates and source contracts.
3. Re-validate contract consistency and mention any unresolved blockers.
4. Run `{AGENT_SCRIPT}` to refresh agent context.
5. Run `{GATE_SCRIPT}` and extract pending units + next-stage commands.
6. Output summary with a `Follow-up Tasks` section.

## Output Contract

- Rebuilt artifacts in `programs/<program_id>/units/<unit_id>/` (`design.*`, `content-model.*`, `exercise-design.*`, `assessment-blueprint.json`, `template-selection.json`, `outputs/manifest.json`).
- A `Follow-up Tasks` section with actionable prompts from workflow status.

## Examples

- Success: artifacts rebuilt, current unit ready for `/lcs.sequence`, and pending units listed with commands.
- Fail: command blocked because refinement still has open questions.
