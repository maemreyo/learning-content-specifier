# Quick Start

## 1. Initialize

```bash
uvx --from git+https://github.com/maemreyo/learning-content-specifier.git lcs init <PROJECT_NAME> --ai claude
```

## 2. Run the command chain

```text
/lcs.charter
/lcs.subject.charter (optional, subject governance only)
/lcs.define Build a learning unit for ...
/lcs.programs list-units (recommended for multi-unit programs)
/lcs.refine
/lcs.design
/lcs.redesign (optional, force-reset design for current unit)
/lcs.sequence
/lcs.rubric
/lcs.audit
/lcs.author
```

For multi-unit programs, activate the intended unit before refine/design:

```text
/lcs.programs activate --program <program-id> --unit <unit-id>
/lcs.programs workflow-status --program <program-id>
```

## 3. Confirm artifacts

Expected under `programs/<program-id>/units/<###-slug>/`:

- `brief.md`
- `brief.json`
- `design.md`
- `design.json`
- `sequence.md`
- `sequence.json`
- `content-model.md`
- `content-model.json`
- `exercise-design.md`
- `exercise-design.json`
- `design-decisions.json`
- `assessment-map.md`
- `delivery-guide.md`
- `rubrics/`
- `audit-report.md`
- `audit-report.json`
- `outputs/`
- `outputs/manifest.json`

Expected under `programs/<program-id>/` (for larger scopes, e.g. 30-day target mapped into study sessions):

- `roadmap.json`
- `roadmap.md`

## Hard Gate Rule

Do not run `/lcs.author` unless:

- rubric items are resolved with evidence,
- audit decision is `PASS` in machine/human reports,
- artifact contract validator passes for required JSON files,
- open `CRITICAL/HIGH` count is zero.
