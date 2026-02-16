---
description: Reduce ambiguity in the active learning unit brief and write clarifications back to the brief.
argument-hint: "[clarification focus or unresolved assumptions]"
handoffs:
  - label: Build Learning Design
    agent: lcs.design
    prompt: Build design artifacts from the refined brief.
scripts:
  sh: factory/scripts/bash/check-workflow-prereqs.sh --json --paths-only --stage refine
  ps: factory/scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly -Stage refine
gate_scripts:
  sh: factory/scripts/bash/manage-program-context.sh --json workflow-status
  ps: factory/scripts/powershell/manage-program-context.ps1 --json workflow-status
---

## Intent

Convert high-impact ambiguity into explicit brief clarifications before design.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST ask only questions that materially affect design or gate outcomes.
- YOU MUST persist accepted clarifications into canonical `brief.json`.
- YOU MUST keep `brief.md` optional sidecar only and never canonical.
- YOU MUST append clarification history with date.
- YOU MUST maintain `brief.json.refinement` with:
  - `decisions` (accepted clarifications),
  - `open_questions` (integer),
  - `last_refined_at` (ISO timestamp).
- YOU MUST run `{GATE_SCRIPT}` after refinement and use it to summarize remaining units needing refinement/design.
- YOU MUST include a `Follow-up Tasks` section with exact next prompts.
- YOU MUST suggest `/lcs.programs activate --program <program_id> --unit <unit_id>` before refining another unit.
- YOU MUST NOT ask redundant or low-impact questions.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `UNIT_BRIEF_FILE`.
2. Inspect ambiguity hotspots: outcome measurability, audience constraints, pedagogy assumptions, assessment evidence, accessibility requirements.
3. Ask targeted clarifications and integrate accepted answers under `## Clarifications`.
4. Reconcile contradictory wording in the main brief sections.
5. Update `brief.json` fields impacted by clarifications and set `refinement.open_questions`.
6. Run `{GATE_SCRIPT}` to capture pending workflow status for all units.
7. Save and report readiness for `/lcs.design` with prioritized follow-up tasks.

## Hard Gates

- Gate G-RF-001: `refinement.open_questions = 0` for design readiness.
- Gate G-RF-002: contradictions removed between original brief and clarifications.

## Failure Modes

- Brief missing: stop and request `/lcs.define` first.
- Clarification conflicts unresolved: stop and require explicit user decision.

## Output Contract

- Updated canonical `programs/<program_id>/units/<unit_id>/brief.json`.
- Optional sidecar update: `programs/<program_id>/units/<unit_id>/brief.md`.
- Report includes: clarification count, sections touched, unresolved blockers.
- Report MUST include `Follow-up Tasks`:
  - next command for current unit,
  - units still needing refinement,
  - units ready for design with exact prompts (`/lcs.programs activate ...`, `/lcs.refine ...`, `/lcs.design ...`).

## Examples

- Success: ambiguity on evidence resolved and mapped to LO acceptance.
- Fail: unresolved conflict between audience level and difficulty target.
