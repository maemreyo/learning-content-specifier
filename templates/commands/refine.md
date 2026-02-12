---
description: Reduce ambiguity in the active learning unit brief and write clarifications back to the brief.
handoffs:
  - label: Build Learning Design
    agent: lcs.design
    prompt: Build design artifacts from the refined brief.
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json --paths-only
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json -PathsOnly
---

## Intent

Convert high-impact ambiguity into explicit brief clarifications before design.

## Inputs

```text
$ARGUMENTS
```

## Mandatory Rules (YOU MUST / MUST NOT)

- YOU MUST ask only questions that materially affect design or gate outcomes.
- YOU MUST persist accepted clarifications back into `brief.md` immediately.
- YOU MUST append clarification history with date.
- YOU MUST NOT ask redundant or low-impact questions.

## Execution Steps

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `UNIT_BRIEF_FILE`.
2. Inspect ambiguity hotspots: outcome measurability, audience constraints, pedagogy assumptions, assessment evidence, accessibility requirements.
3. Ask targeted clarifications and integrate accepted answers under `## Clarifications`.
4. Reconcile contradictory wording in the main brief sections.
5. Save and report readiness for `/lcs.design`.

## Hard Gates

- Gate G-RF-001: no unresolved critical ambiguity affecting LO or assessment coverage.
- Gate G-RF-002: contradictions removed between original brief and clarifications.

## Failure Modes

- Brief missing: stop and request `/lcs.define` first.
- Clarification conflicts unresolved: stop and require explicit user decision.

## Output Contract

- Updated `specs/<unit>/brief.md`.
- Report includes: clarification count, sections touched, unresolved blockers.

## Examples

- Success: ambiguity on evidence resolved and mapped to LO acceptance.
- Fail: unresolved conflict between audience level and difficulty target.
