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

## User Input

```text
$ARGUMENTS
```

## Goal

Improve brief precision for high-impact decisions before design.

## Workflow

1. Run `{SCRIPT}` once and parse `UNIT_DIR`, `BRIEF_FILE` (paths-only payload).
2. Load brief and scan for missing/ambiguous areas:
   - outcome measurability
   - audience constraints
   - pedagogy assumptions
   - assessment evidence expectations
   - accessibility/readability requirements
3. Ask targeted clarification questions only where ambiguity materially changes design.
4. After each accepted answer:
   - append under `## Clarifications` with session date
   - update the most relevant section directly
   - remove contradictory wording
5. Save brief after each integrated answer.
6. Report: number of clarifications, sections updated, and readiness for `/lcs.design`.
