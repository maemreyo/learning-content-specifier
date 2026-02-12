---
description: Create dependency-ordered production sequence for learning content authoring.
handoffs:
  - label: Run Quality Audit
    agent: lcs.audit
    prompt: Audit cross-artifact consistency.
    send: true
  - label: Start Authoring
    agent: lcs.author
    prompt: Author outputs from approved sequence.
    send: true
scripts:
  sh: scripts/bash/check-workflow-prereqs.sh --json
  ps: scripts/powershell/check-workflow-prereqs.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

## Workflow

1. Run `{SCRIPT}` and parse `UNIT_DIR`, `AVAILABLE_DOCS`.
2. Load required docs: `design.md`, `brief.md`.
3. Optionally load: `content-model.md`, `assessment-map.md`, `delivery-guide.md`, `research.md`.
4. Generate `sequence.md` using `.lcs/templates/sequence-template.md`.
5. Sequence requirements:
   - explicit LO mapping for authoring tasks
   - clear file paths under `outputs/`
   - hard-gate tasks before `/lcs.author`
6. Report total task count, LO coverage, and parallel opportunities.
