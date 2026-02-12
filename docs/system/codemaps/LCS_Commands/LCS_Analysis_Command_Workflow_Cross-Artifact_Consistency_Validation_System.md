---
description: LCS Audit Command Workflow: Cross-Artifact Consistency Validation for Learning Content
---

Codemap title: LCS Audit Command Workflow (Learning Content)
Codemap ID: 'LCS_Audit_Command_Workflow__Learning_Content__20260212'

## System Overview

The workflow is clean-break migrated to learning-content production with hard quality gates.

Command flow:

1. `/lcs.charter`
2. `/lcs.define`
3. `/lcs.refine`
4. `/lcs.design`
5. `/lcs.sequence`
6. `/lcs.rubric`
7. `/lcs.audit`
8. `/lcs.author`
9. `/lcs.issueize`

Primary artifacts under `specs/<###-unit-name>/`:

- `brief.md`
- `design.md`
- `sequence.md`
- `content-model.md`
- `assessment-map.md`
- `delivery-guide.md`
- `rubrics/`
- `outputs/`

Governance artifact:

- `.lcs/memory/charter.md`

## Trace 1: `/lcs.audit` Execution Flow

```text
/lcs.audit
  -> check-workflow-prereqs.sh --json --require-sequence --include-sequence
  -> load brief.md + design.md + sequence.md
  -> evaluate cross-artifact consistency
     - LO coverage consistency
     - objective-activity-assessment continuity
     - metadata/output contract consistency
     - hard gate readiness
  -> produce structured audit report
```

## Trace 2: Unit Definition Flow

```text
/lcs.define
  -> create-new-unit.sh --json
  -> creates numbered unit branch/directory
  -> writes brief.md from brief-template.md
```

## Trace 3: Design Flow

```text
/lcs.design
  -> setup-design.sh --json
  -> writes design.md from design-template.md
  -> generates content-model.md, assessment-map.md, delivery-guide.md
  -> updates agent context from learning profile metadata
```

## Trace 4: Sequence and Authoring Flow

```text
/lcs.sequence
  -> check-workflow-prereqs.sh --json
  -> writes sequence.md from sequence-template.md

/lcs.author
  -> check-workflow-prereqs.sh --json --require-sequence --include-sequence
  -> verifies rubrics/ hard gates are complete
  -> blocks on unresolved critical findings
  -> writes production assets to outputs/
```

## Hard Gates

- Objective-Activity-Assessment alignment gate
- Pedagogy consistency gate
- Accessibility/readability gate
- Metadata completeness gate
- Cross-artifact consistency gate

## Key File References

- `templates/commands/audit.md`
- `templates/commands/author.md`
- `templates/commands/design.md`
- `templates/commands/sequence.md`
- `scripts/bash/check-workflow-prereqs.sh`
- `scripts/bash/create-new-unit.sh`
- `scripts/bash/setup-design.sh`
- `scripts/bash/update-agent-context.sh`
- `docs/system/codemaps/LCS_Commands/diagram.md`
